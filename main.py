"""
FastAPI application for the Dynamic Research Assistant.

Features:
- Async request handling with thread pool executor
- Streaming responses for real-time output
- Response caching for improved performance
- Health monitoring and cache statistics
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from typing import Dict, Any, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
import asyncio
import uuid
import uvicorn
import json
from datetime import datetime

from agent.agent_workflow import ResearchAssistantWorkflow
from utils.config_loader import ConfigLoader
from utils.cache import get_all_cache_stats, clear_all_caches, search_cache
from logger.logging import setup_logging, get_logger

# Initialize logging
config = ConfigLoader()
log_level = config.get("logging.level", "INFO")
log_file = config.get("logging.file", None)
format = config.get("logging.format", "%(asctime)s - %(levelname)s - %(message)s")
setup_logging(log_level=log_level, log_file=log_file, format=format)
logger = get_logger(__name__)

# Global instances
workflow_instance = None
thread_pool = ThreadPoolExecutor(max_workers=4)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with resource cleanup."""
    global workflow_instance

    # Startup
    try:
        logger.info("Starting Dynamic Research Assistant API")
        config = ConfigLoader()
        model_provider = config.get_env("MODEL_PROVIDER", "groq")
        workflow_instance = ResearchAssistantWorkflow(model_provider=model_provider)
        workflow_instance.build_graph()
        logger.info("Research workflow initialized successfully")

    except Exception as e:
        error_msg = f"Failed to initialize workflow: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    yield

    # Shutdown
    try:
        logger.info("Shutting down Dynamic Research Assistant API")
        thread_pool.shutdown(wait=False)
        clear_all_caches()
        logger.info("Cleanup completed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="Dynamic Research Assistant API",
    description="AI research assistant with automatic tool selection, caching, and streaming support",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_workflow():
    """Dependency to get workflow instance."""
    if workflow_instance is None:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    return workflow_instance


def run_research_sync(workflow, query: str, conversation_id: str, max_results: int) -> Dict[str, Any]:
    """Synchronous research execution for thread pool."""
    result = workflow.run_research(query, conversation_id, max_results)
    execution_trace = workflow.get_execution_trace()

    if result and result.get("messages"):
        last_message = result["messages"][-1]
        response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
    else:
        response_content = "No response generated"

    return {
        "response": response_content,
        "execution_trace": execution_trace
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Dynamic Research Assistant API",
        "version": "2.0.0",
        "status": "active",
        "endpoints": {
            "research": "/research",
            "stream": "/research/stream",
            "health": "/health",
            "cache_stats": "/cache/stats"
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status."""
    cache_stats = get_all_cache_stats()

    return {
        "status": "healthy",
        "workflow_initialized": workflow_instance is not None,
        "cache": {
            "llm_hit_rate": cache_stats["llm_cache"]["hit_rate"],
            "search_hit_rate": cache_stats["search_cache"]["hit_rate"]
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/cache/stats")
async def cache_statistics():
    """Get detailed cache statistics."""
    return {
        "caches": get_all_cache_stats(),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/cache/clear")
async def clear_cache():
    """Clear all caches."""
    clear_all_caches()
    return {
        "status": "success",
        "message": "All caches cleared",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/research")
async def research_endpoint(
    request_data: Dict[str, Any],
    workflow: ResearchAssistantWorkflow = Depends(get_workflow)
):
    """
    Main research endpoint with async execution.

    Runs the research workflow in a thread pool to avoid blocking.
    """
    try:
        # Extract and validate query data
        query = request_data.get("query", "").strip()
        conversation_id = request_data.get("conversation_id") or str(uuid.uuid4())
        max_results = request_data.get("max_results", 5)

        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        logger.info(f"Processing research query: {query[:100]}...")

        # Check cache for identical recent queries
        cache_key = f"research:{query}:{max_results}"
        cached_response = search_cache.get(cache_key)

        if cached_response:
            logger.info("Returning cached research result")
            return {
                **cached_response,
                "cached": True,
                "timestamp": datetime.now().isoformat()
            }

        # Run research in thread pool for async execution
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            thread_pool,
            run_research_sync,
            workflow,
            query,
            conversation_id,
            max_results
        )

        # Build response
        research_result = {
            "query": query,
            "conversation_id": conversation_id,
            "response": result["response"],
            "execution_trace": result["execution_trace"],
            "max_results": max_results,
            "cached": False,
            "timestamp": datetime.now().isoformat()
        }

        # Cache the result (TTL: 30 minutes)
        search_cache.set(cache_key, research_result, ttl=1800)

        logger.info(f"Research completed for query: {query[:100]}...")

        return research_result

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Research failed -> {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/research/stream")
async def research_stream_endpoint(
    request_data: Dict[str, Any],
    workflow: ResearchAssistantWorkflow = Depends(get_workflow)
):
    """
    Streaming research endpoint for real-time updates.

    Returns Server-Sent Events (SSE) with progress updates.
    """
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            query = request_data.get("query", "").strip()
            conversation_id = request_data.get("conversation_id") or str(uuid.uuid4())
            max_results = request_data.get("max_results", 10)

            if not query:
                yield f"data: {json.dumps({'error': 'Query is required'})}\n\n"
                return

            # Send initial status
            yield f"data: {json.dumps({'status': 'started', 'message': 'Processing query...'})}\n\n"

            # Run research
            loop = asyncio.get_event_loop()

            yield f"data: {json.dumps({'status': 'processing', 'message': 'Selecting tools and gathering information...'})}\n\n"

            result = await loop.run_in_executor(
                thread_pool,
                run_research_sync,
                workflow,
                query,
                conversation_id,
                max_results
            )

            # Send execution trace as progress updates
            for step in result.get("execution_trace", []):
                step_data = {
                    "status": "progress",
                    "step": step.get("step"),
                    "details": step.get("details", {})
                }
                yield f"data: {json.dumps(step_data)}\n\n"
                await asyncio.sleep(0.1)  # Small delay for UI updates

            # Send final response
            final_response = {
                "status": "completed",
                "query": query,
                "conversation_id": conversation_id,
                "response": result["response"],
                "execution_trace": result["execution_trace"],
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(final_response)}\n\n"

        except Exception as e:
            error_response = {
                "status": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_response)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/metrics")
async def metrics():
    """Get performance metrics."""
    cache_stats = get_all_cache_stats()

    return {
        "cache_performance": {
            "llm": {
                "size": cache_stats["llm_cache"]["size"],
                "hit_rate": cache_stats["llm_cache"]["hit_rate"],
                "hits": cache_stats["llm_cache"]["hits"],
                "misses": cache_stats["llm_cache"]["misses"]
            },
            "search": {
                "size": cache_stats["search_cache"]["size"],
                "hit_rate": cache_stats["search_cache"]["hit_rate"],
                "hits": cache_stats["search_cache"]["hits"],
                "misses": cache_stats["search_cache"]["misses"]
            },
            "content": {
                "size": cache_stats["content_cache"]["size"],
                "hit_rate": cache_stats["content_cache"]["hit_rate"],
                "hits": cache_stats["content_cache"]["hits"],
                "misses": cache_stats["content_cache"]["misses"]
            }
        },
        "thread_pool": {
            "max_workers": thread_pool._max_workers
        },
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    try:
        config = ConfigLoader()
        host = config.get_env("API_HOST", "127.0.0.1")
        port = int(config.get_env("API_PORT", 8000))

        logger.info(f"Starting server on {host}:{port}")

        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,
            log_level="info",
            workers=1
        )

    except Exception as e:
        error_msg = f"Failed to start server: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
