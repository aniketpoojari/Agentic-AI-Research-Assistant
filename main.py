"""Simplified FastAPI application for the Dynamic Research Assistant."""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any
import uuid
import uvicorn
from datetime import datetime

from agent.agent_workflow import ResearchAssistantWorkflow
from utils.config_loader import ConfigLoader
from logger.logging import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Global workflow instance
workflow_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global workflow_instance
    
    # Startup
    try:
        logger.info("Starting Dynamic Research Assistant API")
        config = ConfigLoader()
        model_provider = config.get_env("DEFAULT_MODEL_PROVIDER", "groq")
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
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="Dynamic Research Assistant API",
    description="Simplified AI research assistant with automatic tool selection",
    version="1.0.0",
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
    """Dependency to get workflow instance"""
    if workflow_instance is None:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    return workflow_instance


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Dynamic Research Assistant API",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "workflow_initialized": workflow_instance is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/research")
async def research_endpoint(
    request_data: Dict[str, Any],
    workflow: ResearchAssistantWorkflow = Depends(get_workflow)
):
    """Main research endpoint"""
    try:
        # Extract query data
        query = request_data.get("query", "").strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        conversation_id = request_data.get("conversation_id") or str(uuid.uuid4())
        max_results = request_data.get("max_results", 10)
        
        logger.info(f"Processing research query: {query[:100]}...")
        
        # Run research through the workflow
        result = workflow.run_research(query, conversation_id)
        
        # Get execution trace
        execution_trace = workflow.get_execution_trace()
        
        # Extract response from workflow result
        if result and result.get("messages"):
            last_message = result["messages"][-1]
            response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            response_content = "No response generated"
        
        # Create response
        research_result = {
            "query": query,
            "conversation_id": conversation_id,
            "response": response_content,
            "execution_trace": execution_trace,
            "max_results": max_results,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Research completed for query: {query[:100]}...")
        
        return research_result
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Research failed: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


if __name__ == "__main__":
    try:
        config = ConfigLoader()
        host = config.get("api.host", "0.0.0.0")
        port = config.get("api.port", 8000)
        
        logger.info(f"Starting server on {host}:{port}")
        
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
        
    except Exception as e:
        error_msg = f"Failed to start server: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
