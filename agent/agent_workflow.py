"""Enhanced Agentic workflow for the Dynamic Research Assistant with dynamic orchestrator."""

from utils.model_loader import ModelLoader
from prompt_library.prompt import SYSTEM_PROMPT, ORCHESTRATOR_PROMPT

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
import logging

logger = logging.getLogger(__name__)

class ResearchAssistantWorkflow:
    def __init__(self, model_provider="groq"):
        try:
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
            self.orchestrator_prompt = ORCHESTRATOR_PROMPT
            
            # Enhanced tracking
            self.execution_trace = []
            self.tool_usage_stats = {}
            self.max_tool_iterations = 5  # Prevent infinite loops
            
        except Exception as e:
            error_msg = f"Error in ResearchAssistantWorkflow.__init__: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def _log_execution_step(self, step_name, details=None):
        """Log execution steps for tracing."""
        timestamp = datetime.now().isoformat()
        step_info = {
            "timestamp": timestamp,
            "step": step_name,
            "details": details or {}
        }
        self.execution_trace.append(step_info)
        logger.info(f"Execution step: {step_name}")
    
    def enhanced_orchestrator_agent(self, state):
        """Enhanced orchestrator agent with dynamic tool selection and conditional routing"""
        try:
            self._log_execution_step("orchestrator_start", {"input_messages": len(state["messages"])})
            
            messages = state["messages"]
            
            # Get iteration count to prevent infinite loops
            iteration_count = state.get("iteration_count", 0)
            if iteration_count >= self.max_tool_iterations:
                self._log_execution_step("max_iterations_reached", {"count": iteration_count})
                return {
                    "messages": [SystemMessage(content="Maximum tool iterations reached. Generating final response.")],
                    "iteration_count": iteration_count,
                    "should_continue": False
                }
            
            # Add orchestrator system prompt
            orchestrator_message = SystemMessage(content=self.orchestrator_prompt)
            input_messages = [orchestrator_message] + messages
            
            # Analyze the query and determine tool strategy
            tool_strategy = self._analyze_query_for_tools(messages[-1].content if messages else "")
            self._log_execution_step("tool_strategy_determined", {"strategy": tool_strategy})
            
            response = self.llm_with_tools.invoke(input_messages)
            
            # Track tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_names = [call.get("name", "unknown") for call in response.tool_calls]
                self._log_execution_step("tools_called", {"tools": tool_names})
                
                # Update usage stats
                for tool_name in tool_names:
                    self.tool_usage_stats[tool_name] = self.tool_usage_stats.get(tool_name, 0) + 1
            
            self._log_execution_step("orchestrator_complete")
            return {
                "messages": [response],
                "iteration_count": iteration_count + 1,
                "tool_strategy": tool_strategy
            }
            
        except Exception as e:
            error_msg = f"Error in enhanced_orchestrator_agent: {str(e)}"
            self._log_execution_step("orchestrator_error", {"error": error_msg})
            print(error_msg)
            raise Exception(error_msg)
    
    def _analyze_query_for_tools(self, query):
        """Analyze query to determine optimal tool strategy"""
        try:
            query_lower = query.lower()
            
            # Define tool selection patterns
            strategies = {
                "search_heavy": ["latest", "current", "recent", "news", "what is", "who is", "when did"],
                "fact_check": ["verify", "true", "false", "fact", "claim", "accurate", "correct"],
                "summarize": ["summarize", "summary", "overview", "brief", "explain", "describe"],
                "extract_data": ["extract", "data", "numbers", "statistics", "metrics", "table"],
                "comprehensive": ["research", "analysis", "comprehensive", "detailed", "thorough"]
            }
            
            # Score each strategy
            strategy_scores = {}
            for strategy, keywords in strategies.items():
                score = sum(1 for keyword in keywords if keyword in query_lower)
                if score > 0:
                    strategy_scores[strategy] = score
            
            # Return the highest scoring strategy or default to comprehensive
            if strategy_scores:
                return max(strategy_scores.items(), key=lambda x: x[1])[0]
            else:
                return "comprehensive"
                
        except Exception as e:
            logger.warning(f"Error analyzing query for tools: {e}")
            return "comprehensive"
    
    def dynamic_tool_executor(self, state):
        """Execute tools and evaluate results for conditional routing"""
        try:
            self._log_execution_step("tool_executor_start")
            
            messages = state["messages"]
            last_message = messages[-1]
            
            # Execute tools using ToolNode
            tool_node = ToolNode(tools=self.tools)
            tool_result = tool_node.invoke(state)
            
            # Evaluate tool results
            evaluation = self._evaluate_tool_results(tool_result, state)
            self._log_execution_step("tool_results_evaluated", {"evaluation": evaluation})
            
            # Update state with evaluation
            updated_state = {
                **tool_result,
                "tool_evaluation": evaluation,
                "iteration_count": state.get("iteration_count", 0)
            }
            
            return updated_state
            
        except Exception as e:
            error_msg = f"Error in dynamic_tool_executor: {str(e)}"
            self._log_execution_step("tool_executor_error", {"error": error_msg})
            print(error_msg)
            raise Exception(error_msg)
    
    def _evaluate_tool_results(self, tool_result, state):
        """Evaluate tool results to determine next action"""
        try:
            messages = tool_result.get("messages", [])
            if not messages:
                return {"action": "end", "reason": "no_tool_results"}
            
            last_message = messages[-1]
            content = getattr(last_message, 'content', str(last_message))
            
            # Simple evaluation logic
            evaluation = {
                "has_results": bool(content and content.strip()),
                "content_length": len(content) if content else 0,
                "seems_complete": self._assess_completeness(content, state),
                "needs_more_tools": self._assess_need_for_more_tools(content, state),
                "action": "continue"  # Default action
            }
            
            # Determine action based on evaluation
            if not evaluation["has_results"]:
                evaluation["action"] = "retry"
                evaluation["reason"] = "no_results"
            elif evaluation["seems_complete"] and not evaluation["needs_more_tools"]:
                evaluation["action"] = "end"
                evaluation["reason"] = "complete"
            elif evaluation["needs_more_tools"] and state.get("iteration_count", 0) < self.max_tool_iterations:
                evaluation["action"] = "continue"
                evaluation["reason"] = "needs_more_tools"
            else:
                evaluation["action"] = "end"
                evaluation["reason"] = "max_iterations_or_sufficient"
            
            return evaluation
            
        except Exception as e:
            logger.warning(f"Error evaluating tool results: {e}")
            return {"action": "end", "reason": "evaluation_error"}
    
    def _assess_completeness(self, content, state):
        """Assess if the content seems complete"""
        try:
            if not content:
                return False
            
            # Simple heuristics for completeness
            completeness_indicators = [
                len(content) > 200,  # Substantial content
                "." in content,      # Complete sentences
                not content.lower().endswith(("searching", "loading", "processing"))
            ]
            
            return sum(completeness_indicators) >= 2
            
        except Exception as e:
            logger.warning(f"Error assessing completeness: {e}")
            return True  # Default to complete to avoid loops
    
    def _assess_need_for_more_tools(self, content, state):
        """Assess if more tools are needed"""
        try:
            if not content:
                return True
            
            content_lower = content.lower()
            
            # Indicators that more tools might be needed
            more_tools_indicators = [
                "need more information" in content_lower,
                "insufficient data" in content_lower,
                "let me search" in content_lower,
                "additional research" in content_lower,
                len(content) < 100  # Very short responses might need more
            ]
            
            return any(more_tools_indicators)
            
        except Exception as e:
            logger.warning(f"Error assessing need for more tools: {e}")
            return False  # Default to not needing more tools
    
    def research_agent(self, state):
        """Enhanced research agent with better context handling"""
        try:
            self._log_execution_step("research_agent_start")
            
            messages = state["messages"]
            
            # Add system prompt with context about tool usage
            tool_context = ""
            if state.get("tool_evaluation"):
                eval_data = state["tool_evaluation"]
                tool_context = f"\nTool execution completed. Results evaluation: {eval_data.get('reason', 'unknown')}"
            
            enhanced_system_prompt = self.system_prompt + tool_context
            system_message = SystemMessage(content=enhanced_system_prompt)
            input_messages = [system_message] + messages
            
            response = self.llm_with_tools.invoke(input_messages)
            
            self._log_execution_step("research_agent_complete", {
                "response_length": len(response.content) if hasattr(response, 'content') else 0
            })
            
            return {"messages": [response]}
            
        except Exception as e:
            error_msg = f"Error in research_agent: {str(e)}"
            self._log_execution_step("research_agent_error", {"error": error_msg})
            print(error_msg)
            raise Exception(error_msg)
    
    def should_continue(self, state):
        """Enhanced continuation logic with conditional routing"""
        try:
            messages = state["messages"]
            last_message = messages[-1]
            iteration_count = state.get("iteration_count", 0)
            
            # Check iteration limit
            if iteration_count >= self.max_tool_iterations:
                self._log_execution_step("should_continue_max_iterations")
                return "end"
            
            # Check if the last message has tool calls
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                self._log_execution_step("should_continue_has_tool_calls")
                return "tools"
            
            # Check tool evaluation if available
            if state.get("tool_evaluation"):
                evaluation = state["tool_evaluation"]
                action = evaluation.get("action", "end")
                
                if action == "continue":
                    self._log_execution_step("should_continue_evaluation_continue")
                    return "orchestrator"  # Loop back to orchestrator for more tools
                elif action == "retry":
                    self._log_execution_step("should_continue_evaluation_retry")
                    return "orchestrator"  # Retry with different approach
            
            # Check if we need more research based on content
            content = last_message.content.lower() if hasattr(last_message, 'content') else ""
            if any(phrase in content for phrase in ["need more information", "searching for", "let me find"]):
                self._log_execution_step("should_continue_needs_more_research")
                return "orchestrator"
            
            self._log_execution_step("should_continue_end")
            return "end"
            
        except Exception as e:
            error_msg = f"Error in should_continue: {str(e)}"
            self._log_execution_step("should_continue_error", {"error": error_msg})
            print(error_msg)
            return "end"
    
    def build_graph(self):
        """Build the enhanced research workflow graph with dynamic routing"""
        try:
            graph_builder = StateGraph(MessagesState)
            
            # Add nodes
            graph_builder.add_node("orchestrator", self.enhanced_orchestrator_agent)
            graph_builder.add_node("research_agent", self.research_agent)
            graph_builder.add_node("tools", self.dynamic_tool_executor)
            
            # Add edges with enhanced routing
            graph_builder.add_edge(START, "orchestrator")
            graph_builder.add_conditional_edges("orchestrator", tools_condition)
            graph_builder.add_edge("tools", "research_agent")
            graph_builder.add_conditional_edges("research_agent", self.should_continue)
            
            self.graph = graph_builder.compile()


            # Generate the graph visualization
            graph_image = self.graph.get_graph().draw_mermaid_png()
            
            with open("agent_graph.png", "wb") as f:
                f.write(graph_image)


            return self.graph
            
        except Exception as e:
            error_msg = f"Error in build_graph: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_execution_trace(self):
        """Get the execution trace for debugging"""
        return {
            "trace": self.execution_trace,
            "tool_usage_stats": self.tool_usage_stats,
            "total_steps": len(self.execution_trace)
        }
    
    def clear_execution_trace(self):
        """Clear the execution trace"""
        self.execution_trace = []
        self.tool_usage_stats = {}
    
    def visualize_graph(self, output_path="agent_graph.png"):
        """Generate a visual representation of the agent workflow graph"""
        try:
            if not self.graph:
                self.build_graph()
            
            # Generate the graph visualization
            graph_image = self.graph.get_graph().draw_mermaid_png()
            
            with open(output_path, "wb") as f:
                f.write(graph_image)
            
            print(f"Graph visualization saved to {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error generating graph visualization: {e}")
            return None
    
    def get_graph_structure(self):
        """Get the graph structure as a dictionary"""
        try:
            if not self.graph:
                self.build_graph()
            
            return {
                "nodes": ["orchestrator", "research_agent", "tools"],
                "edges": [
                    {"from": "START", "to": "orchestrator"},
                    {"from": "orchestrator", "to": "tools", "condition": "tools_condition"},
                    {"from": "tools", "to": "research_agent"},
                    {"from": "research_agent", "to": "END", "condition": "should_continue"},
                    {"from": "research_agent", "to": "orchestrator", "condition": "should_continue (loop)"}
                ],
                "tools": [tool.name for tool in self.tools if hasattr(tool, 'name')]
            }
            
        except Exception as e:
            print(f"Error getting graph structure: {e}")
            return {}
    
    def run_research(self, query, session_id=None):
        """Run a research query through the enhanced workflow"""
        try:
            if not self.graph:
                self.build_graph()
            
            # Clear previous execution trace
            self.clear_execution_trace()
            
            # Create initial message
            initial_message = HumanMessage(content=query)
            
            # Add session context if provided
            if session_id:
                try:
                    history_tool = next(tool for tool in self.tools if hasattr(tool, 'name') and tool.name == "get_conversation_history")
                    history_result = history_tool.invoke({"session_id": session_id, "limit": 5})
                    if history_result.get("success") and history_result.get("history"):
                        context_message = SystemMessage(
                            content=f"Previous conversation context: {history_result['history']}"
                        )
                        messages = [context_message, initial_message]
                    else:
                        messages = [initial_message]
                except:
                    messages = [initial_message]
            else:
                messages = [initial_message]
            
            # Initialize state
            initial_state = {
                "messages": messages,
                "iteration_count": 0
            }
            
            # Run the workflow
            result = self.graph.invoke(initial_state)
            
            # Store the conversation if session_id is provided
            if session_id:
                try:
                    store_tool = next(tool for tool in self.tools if hasattr(tool, 'name') and tool.name == "store_conversation")
                    store_tool.invoke({
                        "session_id": session_id,
                        "message": query,
                        "role": "user"
                    })
                    
                    # Store assistant response
                    if result["messages"]:
                        last_response = result["messages"][-1]
                        store_tool.invoke({
                            "session_id": session_id,
                            "message": last_response.content if hasattr(last_response, 'content') else str(last_response),
                            "role": "assistant"
                        })
                except:
                    pass  # Continue even if storing fails
            
            return result
            
        except Exception as e:
            error_msg = f"Error in run_research: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def __call__(self, query, session_id=None):
        """Make the workflow callable"""
        try:
            return self.run_research(query, session_id)
        except Exception as e:
            error_msg = f"Error in __call__: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
