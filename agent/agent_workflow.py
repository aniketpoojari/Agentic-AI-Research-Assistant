"""Agentic workflow for the Dynamic Research Assistant."""

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

class ResearchAssistantWorkflow:
    def __init__(self, model_provider: str = "groq"):
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
    
    def orchestrator_agent(self, state: MessagesState):
        """Orchestrator agent that manages the research workflow"""
        messages = state["messages"]
        
        # Add orchestrator system prompt
        orchestrator_message = SystemMessage(content=self.orchestrator_prompt)
        input_messages = [orchestrator_message] + messages
        
        response = self.llm_with_tools.invoke(input_messages)
        return {"messages": [response]}
    
    def research_agent(self, state: MessagesState):
        """Main research agent function"""
        messages = state["messages"]
        
        # Add system prompt
        system_message = SystemMessage(content=self.system_prompt)
        input_messages = [system_message] + messages
        
        response = self.llm_with_tools.invoke(input_messages)
        return {"messages": [response]}
    
    def should_continue(self, state: MessagesState):
        """Determine if the workflow should continue"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # Check if the last message has tool calls
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        
        # Check if we need more research
        content = last_message.content.lower()
        if any(phrase in content for phrase in ["need more information", "searching for", "let me find"]):
            return "research_agent"
        
        return "end"
    
    def build_graph(self):
        """Build the research workflow graph"""
        graph_builder = StateGraph(MessagesState)
        
        # Add nodes
        graph_builder.add_node("orchestrator", self.orchestrator_agent)
        graph_builder.add_node("research_agent", self.research_agent)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        
        # Add edges
        graph_builder.add_edge(START, "orchestrator")
        graph_builder.add_conditional_edges("orchestrator", tools_condition)
        graph_builder.add_edge("tools", "research_agent")
        graph_builder.add_conditional_edges("research_agent", self.should_continue)
        graph_builder.add_edge("research_agent", END)
        
        self.graph = graph_builder.compile()
        return self.graph
    
    def run_research(self, query: str, session_id: str = None):
        """Run a research query through the workflow"""
        if not self.graph:
            self.build_graph()
        
        # Create initial message
        initial_message = HumanMessage(content=query)
        
        # Add session context if provided
        if session_id:
            # Try to get conversation history
            try:
                history_tool = next(tool for tool in self.tools if tool.name == "get_conversation_history")
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
        
        # Run the workflow
        result = self.graph.invoke({"messages": messages})
        
        # Store the conversation if session_id is provided
        if session_id:
            try:
                store_tool = next(tool for tool in self.tools if tool.name == "store_conversation")
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
                        "message": last_response.content,
                        "role": "assistant"
                    })
            except:
                pass  # Continue even if storing fails
        
        return result
    
    def __call__(self, query: str, session_id: str = None):
        """Make the workflow callable"""
        return self.run_research(query, session_id)
