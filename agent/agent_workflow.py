"""Simplified Agentic workflow for the Dynamic Research Assistant."""

from utils.model_loader import ModelLoader
from prompt_library.prompt import SYSTEM_PROMPT, AGENT_PROMPT

from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.schema import HumanMessage, SystemMessage

# Import all tools
from tools.web_search_tool import WebSearchTool
from tools.summarization_tool import SummarizationTool
from tools.fact_checking_tool import FactCheckingTool
from tools.data_extraction_tool import DataExtractionTool
from tools.citation_tool import CitationTool
from tools.conversation_memory_tool import ConversationMemoryTool

from datetime import datetime
from logger.logging import get_logger
from langsmith import Client

logger = get_logger(__name__)

class ResearchAssistantWorkflow:
    def __init__(self, model_provider="groq"):
        try:

            client = Client()

            # Initialize LLM            
            self.model_loader = ModelLoader(model_provider=model_provider)
            self.llm = self.model_loader.load_llm()
            
            # Initialize all tools
            self.tools = []
            
            # Web search tools
            self.web_search_tools = WebSearchTool()
            self.tools.extend(self.web_search_tools.web_search_tool_list)
            
            # Summarization tools
            self.summarization_tools = SummarizationTool(model_provider)
            self.tools.extend(self.summarization_tools.summarization_tool_list)
            
            # Fact-checking tools
            self.fact_checking_tools = FactCheckingTool(model_provider)
            self.tools.extend(self.fact_checking_tools.fact_checking_tool_list)
            
            # Data extraction tools
            self.data_extraction_tools = DataExtractionTool(model_provider)
            self.tools.extend(self.data_extraction_tools.data_extraction_tool_list)
            
            # Citation tools
            self.citation_tools = CitationTool(model_provider)
            self.tools.extend(self.citation_tools.citation_tool_list)
            
            # Conversation memory tools
            self.memory_tools = ConversationMemoryTool()
            self.tools.extend(self.memory_tools.conversation_memory_tool_list)
            
            # Bind tools to LLM
            self.llm_with_tools = self.llm.bind_tools(tools=self.tools)
            
            self.graph = None
            self.system_prompt = SYSTEM_PROMPT
            self.agent_prompt = AGENT_PROMPT
            
            # Simple execution trace
            self.execution_trace = []

            logger.info("Research Assistant __init__ completed.")
            
        except Exception as e:
            error_msg = f"Error in ResearchAssistantWorkflow.__init__: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)


    def _log_step(self, step_name, details=None):
        """Log execution steps for simple tracing."""
        
        step_info = {
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.execution_trace.append(step_info)
        logger.info(f"[TRACE] {step_name}: {details or ''}")


    def agent_node(self, state):
        """Main agent node that decides which tools to use."""
        try:
            self._log_step("agent_start")
            
            messages = state["messages"]
            conversation_id = state.get("conversation_id")
            max_results = state.get("max_results", 10)
            
             # Create context-aware system message
            system_content = f"""{self.agent_prompt}

                            Available Context:
                            - Conversation ID: {conversation_id} (use for memory operations)
                            - Max Results: {max_results} (use for search operations)

                            Tool Parameter Guidelines:
                            - Memory tools: Always include conversation_id parameter
                            - Search tools: Use max_results parameter to limit results
                            - Both parameters are provided in your current context"""
            
            system_message = SystemMessage(content=system_content)

            # Combine system message with existing messages
            all_messages = [system_message] + messages
            
            # Invoke LLM
            response = self.llm_with_tools.invoke(all_messages)
            
            # Log tool calls if any
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_names = [call.get("name", "unknown") for call in response.tool_calls]
                self._log_step("tools_selected", {"tools": tool_names})
            else:
                self._log_step("no_tools_needed")
            
            return {"messages": [response]}
            
        except Exception as e:
            error_msg = f"Error in agent_node: {str(e)}"
            self._log_step("agent_error", {"error": error_msg})
            raise Exception(error_msg)
    
        
    def should_continue(self, state):
        """Determine if we should continue with tools or end."""
        try:
            messages = state["messages"]
            last_message = messages[-1]
            
            # Check if the last message has tool calls
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                self._log_step("continuing_with_tools")
                return "tools"
            else:
                self._log_step("ending_workflow")
                return END  # Use END constant instead of "end"
                
        except Exception as e:
            error_msg = f"Error in should_continue: {str(e)}"
            self._log_step("continue_error", {"error": error_msg})
            return END
    

    def build_graph(self):
        """Build the simplified research workflow graph."""
        try:
            graph_builder = StateGraph(MessagesState)
            
            # Add nodes
            graph_builder.add_node("agent", self.agent_node)
            graph_builder.add_node("tools", ToolNode(self.tools))
            
            # Add edges
            graph_builder.add_edge(START, "agent")
            
            # Use tools_condition for proper routing
            graph_builder.add_conditional_edges(
                "agent",
                tools_condition,  # Use built-in tools_condition
            )
            
            graph_builder.add_edge("tools", "agent")
            
            self.graph = graph_builder.compile()
            return self.graph
            
        except Exception as e:
            error_msg = f"Error in build_graph: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    
    def get_execution_trace(self):
        """Get the simple execution trace."""
        return self.execution_trace
    
    def clear_execution_trace(self):
        """Clear the execution trace."""
        self.execution_trace = []
    
    def run_research(self, query, conversation_id=None, max_results=10):
        """Run a research query through the workflow."""
        try:
            if not self.graph:
                self.build_graph()
            
            # Clear previous execution trace
            self.clear_execution_trace()
            
            self._log_step("workflow_start", {"query": query[:100]})
            
            # Automatically store the user query
            if conversation_id:
                try:
                    store_tool = next(tool for tool in self.tools if hasattr(tool, 'name') and tool.name == "store_conversation")
                    store_tool.invoke({
                        "session_id": conversation_id,
                        "message": query,
                        "role": "user"
                    })
                except:
                    pass  # Continue even if storing fails
            
            # Create initial message
            initial_message = HumanMessage(content=query)
            
            # Initialize state
            initial_state = {
                "messages": [initial_message],
                "conversation_id": conversation_id,
                "max_results": max_results
            }
            
            # Run the workflow
            result = self.graph.invoke(initial_state)
            
            # Automatically store the assistant response
            if conversation_id and result["messages"]:
                try:
                    store_tool = next(tool for tool in self.tools if hasattr(tool, 'name') and tool.name == "store_conversation")
                    last_response = result["messages"][-1]
                    response_content = last_response.content if hasattr(last_response, 'content') else str(last_response)
                    
                    store_tool.invoke({
                        "session_id": conversation_id,
                        "message": response_content,
                        "role": "assistant"
                    })
                except:
                    pass  # Continue even if storing fails
            
            self._log_step("workflow_complete")
            
            return result
            
        except Exception as e:
            error_msg = f"Error in run_research: {str(e)}"
            self._log_step("workflow_error", {"error": error_msg})
            raise Exception(error_msg)

    
    def __call__(self, query, conversation_id=None):
        """Make the workflow callable."""
        try:
            return self.run_research(query, conversation_id)
        except Exception as e:
            error_msg = f"Error in __call__: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
