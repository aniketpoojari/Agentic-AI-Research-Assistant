"""Simplified Agentic workflow for the Dynamic Research Assistant."""

from utils.model_loader import ModelLoader
from prompt_library.prompt import SYSTEM_PROMPT, AGENT_PROMPT, CRITIC_PROMPT

from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, BaseMessage
from typing import Annotated, List, Dict, Any, TypedDict
import json

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

ROUTER_PROMPT = """Classify this user query into one category. Reply with ONLY the category name.

Categories:
- none: Greetings, casual chat, simple questions answerable without tools (e.g. "hello", "how are you", "what is 2+2")
- memory: User references past conversation (e.g. "what did I ask before", "expand on that", "my previous question")
- search: Research queries needing web search (e.g. "what is quantum computing", "latest news on AI")
- all: Complex research needing analysis, fact-checking, citations, or data extraction

Query: {query}
Category:"""

class AgentState(MessagesState):
    """Custom state for the research assistant with retry tracking."""
    retry_count: int
    contexts: List[str]
    intent: str

class ResearchAssistantWorkflow:
    def __init__(self, model_provider="groq"):
        try:

            client = Client()

            # Initialize LLM            
            self.model_loader = ModelLoader(model_provider=model_provider)
            self.llm = self.model_loader.load_llm()
            
            # Initialize all tools
            self.web_search_tools = WebSearchTool()
            self.summarization_tools = SummarizationTool(model_provider)
            self.fact_checking_tools = FactCheckingTool(model_provider)
            self.data_extraction_tools = DataExtractionTool(model_provider)
            self.citation_tools = CitationTool(model_provider)
            self.memory_tools = ConversationMemoryTool()

            # Tool groups by intent
            memory_tools = self.memory_tools.conversation_memory_tool_list
            search_tools = self.web_search_tools.web_search_tool_list + memory_tools
            all_tools = (
                self.web_search_tools.web_search_tool_list
                + self.summarization_tools.summarization_tool_list
                + self.fact_checking_tools.fact_checking_tool_list
                + self.data_extraction_tools.data_extraction_tool_list
                + self.citation_tools.citation_tool_list
                + memory_tools
            )

            self.tool_groups = {
                "none": [],
                "memory": memory_tools,
                "search": search_tools,
                "all": all_tools,
            }
            # Flat list of all tools (needed for ToolNode)
            self.tools = all_tools
            
            self.graph = None
            self.system_prompt = SYSTEM_PROMPT
            self.agent_prompt = AGENT_PROMPT
            self.critic_prompt = CRITIC_PROMPT
            
            # Simple execution trace
            self.execution_trace = []
            
            # Reflection stats and logs
            self.reflection_stats = {
                "total_queries": 0,
                "triggered_reflections": 0,
                "total_retries": 0,
                "confidence_scores": []
            }
            self.current_reflection_logs = []

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


    def router_node(self, state):
        """Classify query intent to select the right tool group."""
        try:
            query = state["messages"][0].content if state["messages"] else ""
            self._log_step("router_start", {"query": query[:100]})

            prompt = ROUTER_PROMPT.format(query=query)
            response = self.llm.invoke([SystemMessage(content=prompt)])
            intent = response.content.strip().lower()

            # Normalize to valid intent
            if intent not in self.tool_groups:
                intent = "search"

            self._log_step("router_result", {"intent": intent})
            return {"intent": intent}

        except Exception as e:
            logger.error(f"Router failed: {e}, defaulting to search")
            return {"intent": "search"}

    def agent_node(self, state):
        """Main agent node that uses only the tools selected by the router."""
        try:
            self._log_step("agent_start")

            messages = state["messages"]
            max_results = state.get("max_results", 10)
            retry_count = state.get("retry_count", 0)
            intent = state.get("intent", "search")

            # Bind only the tools needed for this intent
            selected_tools = self.tool_groups.get(intent, self.tools)
            if selected_tools:
                llm = self.llm.bind_tools(tools=selected_tools)
            else:
                llm = self.llm

            self._log_step("tools_bound", {"intent": intent, "tool_count": len(selected_tools)})

            # Format the agent prompt
            agent_prompt_text = self.agent_prompt.format(max_results=max_results)

            if retry_count > 0:
                agent_prompt_text += f"\n\nNOTE: This is retry attempt {retry_count}. Your previous response was flagged for potential hallucinations. Please be more careful and rely strictly on the retrieved context."

            system_message = SystemMessage(content=agent_prompt_text)
            all_messages = [system_message] + messages

            response = llm.invoke(all_messages)

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
    
    def critic_node(self, state):
        """Critic node that evaluates the response for hallucinations."""
        try:
            self._log_step("critic_start")
            
            messages = state["messages"]
            last_response = messages[-1].content
            
            # Extract contexts from ToolMessages in history
            contexts = []
            for msg in messages:
                if isinstance(msg, ToolMessage):
                    contexts.append(str(msg.content))
            
            if not contexts:
                self._log_step("critic_no_context")
                return {"is_hallucinating": False, "confidence_score": 1.0}

            # Format critic prompt
            formatted_critic_prompt = self.critic_prompt.format(
                contexts="\n---\n".join(contexts),
                response=last_response
            )
            
            # Invoke LLM as critic
            critic_response = self.llm.invoke([SystemMessage(content=formatted_critic_prompt)])
            
            # Parse JSON response
            try:
                # Find JSON block if it's wrapped in backticks
                content = critic_response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                reflection_result = json.loads(content)
            except Exception as e:
                logger.error(f"Failed to parse critic JSON: {e}")
                reflection_result = {
                    "confidence_score": 1.0,
                    "supported": True,
                    "reasoning": "Failed to parse critic response, assuming OK."
                }

            confidence_score = reflection_result.get("confidence_score", 1.0)
            is_hallucinating = confidence_score < 0.7
            
            # Update stats
            self.reflection_stats["total_queries"] += 1
            self.reflection_stats["confidence_scores"].append(confidence_score)
            
            retry_count = state.get("retry_count", 0)
            
            log_entry = {
                "original_response": last_response[:200] + "...",
                "confidence_score": confidence_score,
                "is_hallucinating": is_hallucinating,
                "retry_triggered": is_hallucinating and retry_count < 3,
                "reasoning": reflection_result.get("reasoning", "")
            }
            self.current_reflection_logs.append(log_entry)
            
            if is_hallucinating:
                self.reflection_stats["triggered_reflections"] += 1
                self._log_step("hallucination_detected", log_entry)
            else:
                self._log_step("response_verified", {"confidence": confidence_score})

            return {
                "is_hallucinating": is_hallucinating,
                "confidence_score": confidence_score,
                "retry_count": retry_count + 1 if is_hallucinating else retry_count
            }

        except Exception as e:
            logger.error(f"Error in critic_node: {e}")
            return {"is_hallucinating": False, "confidence_score": 1.0}

    def reflection_condition(self, state):
        """Determine if we should retry or end based on critic feedback."""
        is_hallucinating = state.get("is_hallucinating", False)
        retry_count = state.get("retry_count", 0)
        
        if is_hallucinating and retry_count <= 3:
            self._log_step("triggering_retry", {"attempt": retry_count})
            self.reflection_stats["total_retries"] += 1
            return "agent"
        else:
            return END

    def build_graph(self):
        """Build the research workflow graph with router and reflection."""
        try:
            graph_builder = StateGraph(AgentState)

            # Add nodes
            graph_builder.add_node("router", self.router_node)
            graph_builder.add_node("agent", self.agent_node)
            graph_builder.add_node("tools", ToolNode(self.tools))
            graph_builder.add_node("critic", self.critic_node)

            # Router classifies intent first
            graph_builder.add_edge(START, "router")
            graph_builder.add_edge("router", "agent")

            # Agent can go to tools or critic
            graph_builder.add_conditional_edges(
                "agent",
                tools_condition,
                {
                    "tools": "tools",
                    END: "critic"
                }
            )

            graph_builder.add_edge("tools", "agent")

            # Critic can go to agent (retry) or end
            graph_builder.add_conditional_edges(
                "critic",
                self.reflection_condition
            )

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
    
    def run_research(self, query, conversation_id=None, max_results=5):
        """Run a research query through the workflow."""
        try:
            if not self.graph:
                self.build_graph()

            # Clear previous execution trace
            self.clear_execution_trace()
            self.current_reflection_logs = []

            # Set session ID for memory tools
            if conversation_id:
                self.memory_tools.set_session_id(conversation_id)

            self._log_step("workflow_start", {"query": query[:100]})

            # Store user query in memory
            self.memory_tools.add_message("user", query)

            # Create message with current query only
            # The agent can use get_conversation_history tool if it needs past context
            initial_message = HumanMessage(content=query)

            # Initialize state
            initial_state = {
                "messages": [initial_message],
                "conversation_id": conversation_id,
                "max_results": max_results,
                "retry_count": 0,
                "contexts": [],
                "intent": ""
            }

            # Run the workflow
            result = self.graph.invoke(initial_state)

            # Store assistant response in memory
            response_content = "No response generated"
            contexts = []
            
            if result.get("messages"):
                last_response = result["messages"][-1]
                response_content = last_response.content if hasattr(last_response, 'content') else str(last_response)
                self.memory_tools.add_message("assistant", response_content)
                
                # Extract contexts from ToolMessages
                for msg in result["messages"]:
                    if isinstance(msg, ToolMessage):
                        contexts.append(str(msg.content))
            
            self._log_step("workflow_complete")

            result["reflection_logs"] = self.current_reflection_logs
            
            return result
            
        except Exception as e:
            error_msg = f"Error in run_research: {str(e)}"
            self._log_step("workflow_error", {"error": error_msg})
            raise Exception(error_msg)

    
    def get_reflection_stats(self):
        """Get self-reflection statistics."""
        stats = self.reflection_stats.copy()
        
        # Calculate average retries
        if stats["total_queries"] > 0:
            stats["average_retries"] = stats["total_retries"] / stats["total_queries"]
            
            # Group confidence scores into distribution
            scores = stats["confidence_scores"]
            distribution = {
                "0.0-0.2": len([s for s in scores if 0.0 <= s < 0.2]),
                "0.2-0.4": len([s for s in scores if 0.2 <= s < 0.4]),
                "0.4-0.6": len([s for s in scores if 0.4 <= s < 0.6]),
                "0.6-0.8": len([s for s in scores if 0.6 <= s < 0.8]),
                "0.8-1.0": len([s for s in scores if 0.8 <= s <= 1.0])
            }
            stats["confidence_distribution"] = distribution
        else:
            stats["average_retries"] = 0
            stats["confidence_distribution"] = {}
            
        return stats

    def __call__(self, query, conversation_id=None):
        """Make the workflow callable."""
        try:
            return self.run_research(query, conversation_id)
        except Exception as e:
            error_msg = f"Error in __call__: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
