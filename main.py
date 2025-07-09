"""FastAPI application for the Dynamic Research Assistant."""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional
import uuid
import uvicorn

from models.pydantic_models import ResearchQuery, ResearchResult
from agent.agent_workflow import ResearchAssistantWorkflow
from utils.config_loader import ConfigLoader
from exception.exception_handling import handle_exceptions, APIException
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
    logger.info("Starting Dynamic Research Assistant API")
    try:
        config = ConfigLoader()
        model_provider = config.get_env("DEFAULT_MODEL_PROVIDER", "groq")
        workflow_instance = ResearchAssistantWorkflow(model_provider=model_provider)
        workflow_instance.build_graph()
        logger.info("Research workflow initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize workflow: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Dynamic Research Assistant API")

# Initialize FastAPI app
config = ConfigLoader()
app = FastAPI(
    title=config.get("api.title", "Dynamic Research Assistant API"),
    description=config.get("api.description", "Advanced AI research assistant with dynamic workflow management"),
    version=config.get("api.version", "1.0.0"),
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
        "status": "active"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "workflow_initialized": workflow_instance is not None
    }

@app.post("/research", response_model=ResearchResult)
@handle_exceptions
async def research_endpoint(
    query: ResearchQuery,
    workflow: ResearchAssistantWorkflow = Depends(get_workflow)
):
    """Main research endpoint"""
    try:
        logger.info(f"Processing research query: {query.query[:100]}...")
        
        # Generate session ID if not provided
        session_id = query.session_id or str(uuid.uuid4())
        
        # Run research
        result = workflow.run_research(query.query, session_id)
        
        # Extract response
        if result and result.get("messages"):
            last_message = result["messages"][-1]
            response_content = last_message.content
        else:
            response_content = "No response generated"
        
        # Create research result
        research_result = ResearchResult(
            query=query.query,
            session_id=session_id,
            query_type=query.query_type,
            summary=response_content,
            workflow_path=["orchestrator", "research_agent", "tools"]
        )
        
        logger.info(f"Research completed for query: {query.query[:100]}...")
        return research_result
        
    except Exception as e:
        logger.error(f"Research failed: {e}")
        raise APIException(f"Research failed: {str(e)}", status_code=500)

@app.get("/session/{session_id}/history")
@handle_exceptions
async def get_session_history(
    session_id: str,
    limit: Optional[int] = 10,
    workflow: ResearchAssistantWorkflow = Depends(get_workflow)
):
    """Get conversation history for a session"""
    try:
        # Find the memory tool
        memory_tool = None
        for tool in workflow.tools:
            if tool.name == "get_conversation_history":
                memory_tool = tool
                break
        
        if not memory_tool:
            raise APIException("Memory tool not available", status_code=500)
        
        result = memory_tool.invoke({
            "session_id": session_id,
            "limit": limit
        })
        
        if result.get("success"):
            return {
                "session_id": session_id,
                "history": result.get("history", []),
                "message_count": result.get("message_count", 0)
            }
        else:
            raise APIException(result.get("error", "Failed to get history"), status_code=500)
            
    except Exception as e:
        logger.error(f"Failed to get session history: {e}")
        raise APIException(f"Failed to get session history: {str(e)}", status_code=500)

@app.delete("/session/{session_id}")
@handle_exceptions
async def clear_session(
    session_id: str,
    workflow: ResearchAssistantWorkflow = Depends(get_workflow)
):
    """Clear session data"""
    try:
        # Access memory manager through workflow
        memory_manager = workflow.memory_tools.memory_manager
        memory_manager.clear_session(session_id)
        
        return {
            "message": f"Session {session_id} cleared successfully",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Failed to clear session: {e}")
        raise APIException(f"Failed to clear session: {str(e)}", status_code=500)

@app.get("/stats")
@handle_exceptions
async def get_stats(workflow: ResearchAssistantWorkflow = Depends(get_workflow)):
    """Get system statistics"""
    try:
        # Find the memory stats tool
        stats_tool = None
        for tool in workflow.tools:
            if tool.name == "get_memory_stats":
                stats_tool = tool
                break
        
        if not stats_tool:
            return {"message": "Stats not available"}
        
        result = stats_tool.invoke({})
        
        if result.get("success"):
            return {
                "system_stats": result.get("stats", {}),
                "workflow_info": {
                    "total_tools": len(workflow.tools),
                    "model_provider": workflow.model_loader.model_provider,
                    "model_info": workflow.model_loader.get_model_info()
                }
            }
        else:
            return {"message": "Failed to get stats"}
            
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    
    
    config = ConfigLoader()
    host = config.get("api.host", "0.0.0.0")
    port = config.get("api.port", 8000)
    debug = config.get("api.debug", True)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
