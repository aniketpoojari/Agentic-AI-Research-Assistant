"""FastAPI application for the Dynamic Research Assistant with Enhanced Orchestrator."""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
import uuid
import uvicorn
import logging
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
        logger.info("Starting Dynamic Research Assistant API with Enhanced Orchestrator")
        config = ConfigLoader()
        model_provider = config.get_env("DEFAULT_MODEL_PROVIDER", "groq")
        workflow_instance = ResearchAssistantWorkflow(model_provider=model_provider)
        workflow_instance.build_graph()
        logger.info("Enhanced research workflow initialized successfully")
    except Exception as e:
        error_msg = f"Failed to initialize workflow: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        raise Exception(error_msg)
    
    yield
    
    # Shutdown
    try:
        logger.info("Shutting down Dynamic Research Assistant API")
        if workflow_instance:
            # Clear execution traces on shutdown
            workflow_instance.clear_execution_trace()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Initialize FastAPI app
try:
    config = ConfigLoader()
    app = FastAPI(
        title=config.get("api.title", "Dynamic Research Assistant API - Enhanced"),
        description=config.get("api.description", "Advanced AI research assistant with dynamic orchestrator and conditional tool routing"),
        version=config.get("api.version", "2.0.0"),
        lifespan=lifespan
    )
except Exception as e:
    logger.error(f"Failed to initialize FastAPI app: {e}")
    raise

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
    try:
        if workflow_instance is None:
            raise HTTPException(status_code=500, detail="Workflow not initialized")
        return workflow_instance
    except Exception as e:
        error_msg = f"Error getting workflow: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/")
async def root():
    """Root endpoint"""
    try:
        return {
            "message": "Dynamic Research Assistant API - Enhanced Orchestrator",
            "version": "2.0.0",
            "status": "active",
            "features": [
                "Dynamic tool selection",
                "Conditional routing",
                "Execution tracing",
                "Graph visualization",
                "Adaptive workflows"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = f"Error in root endpoint: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "workflow_initialized": workflow_instance is not None,
            "orchestrator_type": "enhanced_dynamic",
            "max_iterations": workflow_instance.max_tool_iterations if workflow_instance else None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = f"Error in health check: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/research")
async def research_endpoint(
    request_data: Dict[str, Any],
    workflow: ResearchAssistantWorkflow = Depends(get_workflow)
):
    """Enhanced research endpoint with dynamic orchestrator"""
    try:
        # Extract query data
        query = request_data.get("query", "").strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        session_id = request_data.get("session_id") or str(uuid.uuid4())
        query_type = request_data.get("query_type", "comprehensive")
        max_results = request_data.get("max_results", 10)
        context = request_data.get("context", {})
        
        logger.info(f"Processing research query with enhanced orchestrator: {query[:100]}... (Session: {session_id})")
        
        # Clear previous execution trace for this request
        workflow.clear_execution_trace()
        
        # Run research through the enhanced workflow
        result = workflow.run_research(query, session_id)
        
        # Get execution trace
        execution_trace = workflow.get_execution_trace()
        
        # Extract response from workflow result
        if result and result.get("messages"):
            last_message = result["messages"][-1]
            response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            response_content = "No response generated"
        
        # Create enhanced structured response
        research_result = {
            "query": query,
            "session_id": session_id,
            "query_type": query_type,
            "summary": response_content,
            "search_results": [],
            "citations": [],
            "fact_check_results": [],
            "extracted_data": [],
            "agent_responses": [],
            "execution_trace": execution_trace,
            "tool_usage_stats": execution_trace.get("tool_usage_stats", {}),
            "total_execution_steps": execution_trace.get("total_steps", 0),
            "total_execution_time": None,
            "created_at": datetime.now().isoformat(),
            "workflow_path": ["enhanced_orchestrator", "dynamic_tool_executor", "research_agent"],
            "context": context,
            "orchestrator_decisions": []
        }
        
        # Extract orchestrator decisions and tool usage from trace
        try:
            for step in execution_trace.get("trace", []):
                if step.get("step") == "tool_strategy_determined":
                    research_result["orchestrator_decisions"].append({
                        "timestamp": step.get("timestamp"),
                        "strategy": step.get("details", {}).get("strategy"),
                        "step": "strategy_selection"
                    })
                elif step.get("step") == "tools_called":
                    research_result["orchestrator_decisions"].append({
                        "timestamp": step.get("timestamp"),
                        "tools": step.get("details", {}).get("tools"),
                        "step": "tool_execution"
                    })
        except Exception as e:
            logger.warning(f"Could not extract orchestrator decisions: {e}")
        
        # Try to extract additional information from tool calls if available
        try:
            if result.get("messages"):
                for message in result["messages"]:
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        for tool_call in message.tool_calls:
                            tool_name = tool_call.get("name", "unknown")
                            research_result["agent_responses"].append({
                                "agent_type": tool_name,
                                "success": True,
                                "execution_time": None,
                                "orchestrator_selected": True
                            })
        except Exception as e:
            logger.warning(f"Could not extract tool call information: {e}")
        
        logger.info(f"Enhanced research completed for query: {query[:100]}... (Session: {session_id})")
        logger.info(f"Execution steps: {research_result['total_execution_steps']}, Tools used: {list(research_result['tool_usage_stats'].keys())}")
        
        return research_result
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Research failed: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/trace/{session_id}")
async def get_execution_trace(
    session_id: str,
    workflow: ResearchAssistantWorkflow = Depends(get_workflow)
):
    """Get execution trace for debugging"""
    try:
        trace_data = workflow.get_execution_trace()
        return {
            "session_id": session_id,
            "execution_trace": trace_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = f"Failed to get trace: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/trace/clear")
async def clear_execution_trace(workflow: ResearchAssistantWorkflow = Depends(get_workflow)):
    """Clear execution trace"""
    try:
        workflow.clear_execution_trace()
        return {
            "message": "Execution trace cleared",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = f"Failed to clear trace: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/graph/structure")
async def get_graph_structure(workflow: ResearchAssistantWorkflow = Depends(get_workflow)):
    """Get the workflow graph structure"""
    try:
        structure = workflow.get_graph_structure()
        return {
            "graph_structure": structure,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = f"Failed to get graph structure: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/graph/visualize")
async def visualize_graph(workflow: ResearchAssistantWorkflow = Depends(get_workflow)):
    """Generate graph visualization"""
    try:
        output_path = workflow.visualize_graph()
        if output_path:
            return {
                "message": "Graph visualization generated",
                "path": output_path,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate visualization")
    except Exception as e:
        error_msg = f"Visualization failed: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/session/{session_id}/history")
async def get_session_history(
    session_id: str,
    limit: Optional[int] = 10,
    workflow: ResearchAssistantWorkflow = Depends(get_workflow)
):
    """Get conversation history for a session"""
    try:
        if not session_id or not session_id.strip():
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        # Find the memory tool
        memory_tool = None
        for tool in workflow.tools:
            if hasattr(tool, 'name') and tool.name == "get_conversation_history":
                memory_tool = tool
                break
        
        if not memory_tool:
            logger.warning("Memory tool not available")
            return {
                "session_id": session_id,
                "history": [],
                "message_count": 0
            }
        
        # Get conversation history
        result = memory_tool.invoke({
            "session_id": session_id,
            "limit": limit or 10
        })
        
        if result.get("success"):
            return {
                "session_id": session_id,
                "history": result.get("history", []),
                "message_count": result.get("message_count", 0)
            }
        else:
            logger.warning(f"Failed to get history: {result.get('error', 'Unknown error')}")
            return {
                "session_id": session_id,
                "history": [],
                "message_count": 0
            }
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to get session history: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    workflow: ResearchAssistantWorkflow = Depends(get_workflow)
):
    """Clear session data"""
    try:
        if not session_id or not session_id.strip():
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        # Access memory manager through workflow
        try:
            memory_manager = workflow.memory_tools.memory_manager
            memory_manager.clear_session(session_id)
            
            return {
                "message": f"Session {session_id} cleared successfully",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        except AttributeError:
            logger.warning("Memory manager not accessible")
            return {
                "message": f"Session {session_id} clear requested (memory manager not available)",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to clear session: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/stats")
async def get_stats(workflow: ResearchAssistantWorkflow = Depends(get_workflow)):
    """Get system statistics"""
    try:
        # Find the memory stats tool
        stats_tool = None
        for tool in workflow.tools:
            if hasattr(tool, 'name') and tool.name == "get_memory_stats":
                stats_tool = tool
                break
        
        system_stats = {}
        if stats_tool:
            try:
                result = stats_tool.invoke({})
                if result.get("success"):
                    system_stats = result.get("stats", {})
            except Exception as e:
                logger.warning(f"Could not get memory stats: {e}")
        
        # Get enhanced workflow info
        workflow_info = {
            "total_tools": len(workflow.tools),
            "model_provider": workflow.model_loader.model_provider,
            "model_info": workflow.model_loader.get_model_info(),
            "orchestrator_type": "enhanced_dynamic",
            "max_tool_iterations": workflow.max_tool_iterations,
            "execution_trace_enabled": True
        }
        
        # Get current execution trace stats
        trace_data = workflow.get_execution_trace()
        
        return {
            "system_stats": system_stats,
            "workflow_info": workflow_info,
            "current_trace_stats": {
                "total_steps": trace_data.get("total_steps", 0),
                "tool_usage_stats": trace_data.get("tool_usage_stats", {})
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        error_msg = f"Failed to get stats: {str(e)}"
        logger.error(error_msg)
        return {
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/tools")
async def get_available_tools(workflow: ResearchAssistantWorkflow = Depends(get_workflow)):
    """Get list of available tools with enhanced information"""
    try:
        tools_info = []
        for tool in workflow.tools:
            try:
                tool_info = {
                    "name": getattr(tool, 'name', 'unknown'),
                    "description": getattr(tool, 'description', 'No description available'),
                    "type": type(tool).__name__,
                    "usage_count": workflow.tool_usage_stats.get(getattr(tool, 'name', 'unknown'), 0)
                }
                tools_info.append(tool_info)
            except Exception as e:
                logger.warning(f"Could not get info for tool: {e}")
        
        return {
            "tools": tools_info,
            "total_tools": len(tools_info),
            "orchestrator_features": [
                "Dynamic tool selection",
                "Conditional routing",
                "Tool usage tracking",
                "Execution tracing"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        error_msg = f"Failed to get tools info: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    try:
        config = ConfigLoader()
        host = config.get("api.host", "0.0.0.0")
        port = config.get("api.port", 8000)
        debug = config.get("api.debug", True)
        
        logger.info(f"Starting enhanced server on {host}:{port}")
        
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=debug,
            reload_excludes=["logs/*", "*.log"],
            log_level="info"
        )
        
    except Exception as e:
        error_msg = f"Failed to start server: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        raise Exception(error_msg)
