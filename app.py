"""Enhanced Streamlit application for the Dynamic Research Assistant with Orchestrator Visualization."""

import streamlit as st
import requests
import json
import uuid
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd

# Configuration
API_URL = "http://localhost:8000"
RESEARCH_ENDPOINT = f"{API_URL}/research"

def initialize_session_state():
    """Initialize session state variables."""
    try:
        if "session_id" not in st.session_state:
            st.session_state["session_id"] = str(uuid.uuid4())
        
        if "conversation_history" not in st.session_state:
            st.session_state["conversation_history"] = []
        
        if "research_results" not in st.session_state:
            st.session_state["research_results"] = []
        
        if "execution_traces" not in st.session_state:
            st.session_state["execution_traces"] = []
            
    except Exception as e:
        st.error(f"Error initializing session: {e}")

def make_api_request(payload):
    """Make API request with error handling."""
    try:
        response = requests.post(
            RESEARCH_ENDPOINT, 
            json=payload, 
            timeout=120,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            error_msg = f"API Error {response.status_code}: {response.text}"
            return None, error_msg
            
    except requests.exceptions.Timeout:
        return None, "Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return None, "Could not connect to the API. Please check if the server is running."
    except Exception as e:
        return None, f"Request failed: {str(e)}"

def display_execution_trace(trace_data):
    """Display execution trace with visualizations."""
    try:
        if not trace_data or not trace_data.get("trace"):
            st.info("No execution trace available.")
            return
        
        st.markdown("### 🔍 Execution Trace")
        
        # Create timeline visualization
        trace_steps = trace_data.get("trace", [])
        if trace_steps:
            # Prepare data for timeline
            timeline_data = []
            for i, step in enumerate(trace_steps):
                timeline_data.append({
                    "Step": i + 1,
                    "Action": step.get("step", "unknown"),
                    "Timestamp": step.get("timestamp", ""),
                    "Details": str(step.get("details", {}))
                })
            
            # Create timeline chart
            df = pd.DataFrame(timeline_data)
            
            fig = px.timeline(
                df,
                x_start="Timestamp",
                x_end="Timestamp",
                y="Action",
                title="Workflow Execution Timeline",
                color="Action"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Tool usage statistics
        tool_stats = trace_data.get("tool_usage_stats", {})
        if tool_stats:
            st.markdown("#### 🛠️ Tool Usage Statistics")
            
            # Create bar chart for tool usage
            tools = list(tool_stats.keys())
            usage_counts = list(tool_stats.values())
            
            fig = go.Figure(data=[
                go.Bar(x=tools, y=usage_counts, text=usage_counts, textposition='auto')
            ])
            fig.update_layout(
                title="Tool Usage Count",
                xaxis_title="Tools",
                yaxis_title="Usage Count"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed trace steps
        with st.expander("📋 Detailed Execution Steps"):
            for i, step in enumerate(trace_steps, 1):
                st.write(f"**Step {i}: {step.get('step', 'unknown')}**")
                st.write(f"Timestamp: {step.get('timestamp', 'N/A')}")
                if step.get('details'):
                    st.json(step['details'])
                st.write("---")
        
    except Exception as e:
        st.error(f"Error displaying execution trace: {e}")

def display_orchestrator_decisions(decisions):
    """Display orchestrator decision-making process."""
    try:
        if not decisions:
            return
        
        st.markdown("### 🧠 Orchestrator Decisions")
        
        for i, decision in enumerate(decisions, 1):
            step_type = decision.get("step", "unknown")
            timestamp = decision.get("timestamp", "N/A")
            
            if step_type == "strategy_selection":
                strategy = decision.get("strategy", "unknown")
                st.success(f"**Decision {i}:** Selected strategy: `{strategy}` at {timestamp}")
            elif step_type == "tool_execution":
                tools = decision.get("tools", [])
                st.info(f"**Decision {i}:** Executed tools: `{', '.join(tools)}` at {timestamp}")
        
    except Exception as e:
        st.error(f"Error displaying orchestrator decisions: {e}")

def display_research_results(data):
    """Display research results in a formatted way."""
    try:
        if not data:
            st.warning("No results to display.")
            return
        
        # Main summary
        if data.get("summary"):
            st.markdown("### 📋 Research Summary")
            st.markdown(data["summary"])
        
        # Orchestrator decisions
        if data.get("orchestrator_decisions"):
            display_orchestrator_decisions(data["orchestrator_decisions"])
        
        # Execution trace
        if data.get("execution_trace"):
            display_execution_trace(data["execution_trace"])
        
        # Search results
        if data.get("search_results"):
            st.markdown("### 🔍 Search Results")
            for i, result in enumerate(data["search_results"], 1):
                with st.expander(f"Result {i}: {result.get('title', 'Unknown Title')}"):
                    st.write(f"**URL:** {result.get('url', 'N/A')}")
                    st.write(f"**Source:** {result.get('source', 'N/A')}")
                    if result.get('snippet'):
                        st.write(f"**Snippet:** {result['snippet']}")
        
        # Citations
        if data.get("citations"):
            st.markdown("### 📚 Citations")
            for i, citation in enumerate(data["citations"], 1):
                st.write(f"{i}. {citation.get('formatted_citation', 'N/A')}")
        
        # Fact check results
        if data.get("fact_check_results"):
            st.markdown("### ✅ Fact Check Results")
            for result in data["fact_check_results"]:
                status = result.get("verification", "unknown")
                confidence = result.get("confidence", 0.0)
                claim = result.get("claim", "N/A")
                
                # Color code based on verification status
                if status == "true":
                    st.success(f"✅ **Verified**: {claim} (Confidence: {confidence:.2f})")
                elif status == "false":
                    st.error(f"❌ **False**: {claim} (Confidence: {confidence:.2f})")
                elif status == "partially_true":
                    st.warning(f"⚠️ **Partially True**: {claim} (Confidence: {confidence:.2f})")
                else:
                    st.info(f"❓ **Unverified**: {claim} (Confidence: {confidence:.2f})")
        
        # Extracted data
        if data.get("extracted_data"):
            st.markdown("### 📊 Extracted Data")
            for extraction in data["extracted_data"]:
                data_type = extraction.get("data_type", "Unknown")
                extracted_info = extraction.get("data", {})
                
                st.write(f"**{data_type}:**")
                if isinstance(extracted_info, dict):
                    st.json(extracted_info)
                else:
                    st.write(extracted_info)
        
    except Exception as e:
        st.error(f"Error displaying results: {e}")

def get_conversation_history():
    """Get conversation history from API."""
    try:
        history_url = f"{API_URL}/session/{st.session_state['session_id']}/history"
        response = requests.get(history_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("history", [])
        else:
            return []
            
    except Exception as e:
        st.warning(f"Could not load conversation history: {e}")
        return []

def get_graph_structure():
    """Get workflow graph structure."""
    try:
        graph_url = f"{API_URL}/graph/structure"
        response = requests.get(graph_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("graph_structure", {})
        else:
            return {}
            
    except Exception as e:
        st.warning(f"Could not load graph structure: {e}")
        return {}

def display_workflow_graph():
    """Display workflow graph structure."""
    try:
        graph_data = get_graph_structure()
        
        if not graph_data:
            st.info("Graph structure not available.")
            return
        
        st.markdown("### 🔗 Workflow Graph Structure")
        
        # Display nodes
        nodes = graph_data.get("nodes", [])
        if nodes:
            st.write("**Nodes:**")
            for node in nodes:
                st.write(f"- {node}")
        
        # Display edges
        edges = graph_data.get("edges", [])
        if edges:
            st.write("**Edges:**")
            for edge in edges:
                from_node = edge.get("from", "unknown")
                to_node = edge.get("to", "unknown")
                condition = edge.get("condition", "")
                if condition:
                    st.write(f"- {from_node} → {to_node} (condition: {condition})")
                else:
                    st.write(f"- {from_node} → {to_node}")
        
        # Display tools
        tools = graph_data.get("tools", [])
        if tools:
            st.write("**Available Tools:**")
            for tool in tools:
                st.write(f"- {tool}")
        
    except Exception as e:
        st.error(f"Error displaying workflow graph: {e}")

def clear_session():
    """Clear current session."""
    try:
        clear_url = f"{API_URL}/session/{st.session_state['session_id']}"
        requests.delete(clear_url, timeout=30)
        
        # Reset session state
        st.session_state["session_id"] = str(uuid.uuid4())
        st.session_state["conversation_history"] = []
        st.session_state["research_results"] = []
        st.session_state["execution_traces"] = []
        
        st.success("Session cleared successfully!")
        
    except Exception as e:
        st.error(f"Error clearing session: {e}")

def main():
    """Main Streamlit application."""
    try:
        # Page configuration
        st.set_page_config(
            page_title="Dynamic Research Assistant - Enhanced",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize session state
        initialize_session_state()
        
        # Header
        st.title("🤖 Dynamic Research Assistant - Enhanced Orchestrator")
        st.markdown("Advanced AI research assistant with dynamic tool selection, conditional routing, and execution tracing.")
        
        # Sidebar
        with st.sidebar:
            st.header("⚙️ Enhanced Controls")
            
            # Session info
            st.subheader("Session Info")
            st.write(f"**Session ID:** {st.session_state['session_id'][:8]}...")
            
            # Clear session button
            if st.button("🗑️ Clear Session", type="secondary"):
                clear_session()
                st.rerun()
            
            # API status check
            st.subheader("API Status")
            try:
                health_response = requests.get(f"{API_URL}/health", timeout=5)
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    st.success("✅ API Connected")
                    st.write(f"**Type:** {health_data.get('orchestrator_type', 'unknown')}")
                    st.write(f"**Max Iterations:** {health_data.get('max_iterations', 'N/A')}")
                else:
                    st.error("❌ API Error")
            except:
                st.error("❌ API Disconnected")
            
            # Workflow graph
            st.subheader("Workflow Graph")
            if st.button("🔗 Show Graph Structure"):
                with st.expander("Graph Structure", expanded=True):
                    display_workflow_graph()
            
            # Statistics
            st.subheader("Statistics")
            try:
                stats_response = requests.get(f"{API_URL}/stats", timeout=10)
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    if "system_stats" in stats:
                        st.write(f"**Total Sessions:** {stats['system_stats'].get('total_sessions', 0)}")
                        st.write(f"**Total Conversations:** {stats['system_stats'].get('total_conversations', 0)}")
                    if "current_trace_stats" in stats:
                        st.write(f"**Current Trace Steps:** {stats['current_trace_stats'].get('total_steps', 0)}")
            except:
                st.write("Statistics unavailable")
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("💬 Ask Your Question")
            
            # Query input
            query = st.text_area(
                "Enter your research question:",
                height=100,
                placeholder="e.g., What are the latest developments in artificial intelligence?"
            )
            
            # Advanced options
            with st.expander("🔧 Advanced Options"):
                max_results = st.slider("Maximum search results", 1, 20, 10)
                include_citations = st.checkbox("Include citations", value=True)
                include_fact_check = st.checkbox("Include fact-checking", value=False)
                show_execution_trace = st.checkbox("Show execution trace", value=True)
                show_orchestrator_decisions = st.checkbox("Show orchestrator decisions", value=True)
            
            # Submit button
            if st.button("🚀 Submit Query", type="primary", disabled=not query.strip()):
                if query.strip():
                    # Prepare payload
                    payload = {
                        "query": query.strip(),
                        "query_type": "comprehensive",
                        "session_id": st.session_state["session_id"],
                        "max_results": max_results,
                        "context": {
                            "include_citations": include_citations,
                            "include_fact_check": include_fact_check,
                            "show_execution_trace": show_execution_trace,
                            "show_orchestrator_decisions": show_orchestrator_decisions
                        }
                    }
                    
                    # Show loading
                    with st.spinner("🔍 Processing your query with enhanced orchestrator... This may take a moment."):
                        # Make API request
                        data, error = make_api_request(payload)
                        
                        if error:
                            st.error(f"❌ {error}")
                        else:
                            # Store results
                            result_entry = {
                                "query": query,
                                "results": data,
                                "timestamp": datetime.now().isoformat()
                            }
                            st.session_state["research_results"].append(result_entry)
                            
                            # Store execution trace
                            if data.get("execution_trace"):
                                st.session_state["execution_traces"].append(data["execution_trace"])
                            
                            # Display results
                            st.success("✅ Research completed with enhanced orchestrator!")
                            display_research_results(data)
                else:
                    st.warning("⚠️ Please enter a research question.")
        
        with col2:
            st.header("📜 Recent Results")
            
            # Display recent research results
            if st.session_state["research_results"]:
                for i, result in enumerate(reversed(st.session_state["research_results"][-5:]), 1):
                    with st.expander(f"Query {i}: {result['query'][:50]}..."):
                        st.write(f"**Time:** {result['timestamp']}")
                        if result['results'].get('summary'):
                            st.write(f"**Summary:** {result['results']['summary'][:200]}...")
                        
                        # Show execution stats
                        if result['results'].get('total_execution_steps'):
                            st.write(f"**Execution Steps:** {result['results']['total_execution_steps']}")
                        
                        if result['results'].get('tool_usage_stats'):
                            tools_used = list(result['results']['tool_usage_stats'].keys())
                            st.write(f"**Tools Used:** {', '.join(tools_used)}")
            else:
                st.info("No recent results. Submit a query to get started!")
        
        # Execution Trace Analysis
        if st.session_state["execution_traces"]:
            st.header("📊 Execution Trace Analysis")
            
            # Aggregate tool usage across all traces
            all_tool_usage = {}
            total_steps = 0
            
            for trace in st.session_state["execution_traces"]:
                tool_stats = trace.get("tool_usage_stats", {})
                for tool, count in tool_stats.items():
                    all_tool_usage[tool] = all_tool_usage.get(tool, 0) + count
                total_steps += trace.get("total_steps", 0)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Execution Steps", total_steps)
            
            with col2:
                st.metric("Unique Tools Used", len(all_tool_usage))
            
            with col3:
                st.metric("Total Tool Calls", sum(all_tool_usage.values()))
            
            # Tool usage chart across all sessions
            if all_tool_usage:
                st.markdown("#### 🛠️ Cumulative Tool Usage")
                
                tools = list(all_tool_usage.keys())
                usage_counts = list(all_tool_usage.values())
                
                fig = go.Figure(data=[
                    go.Bar(x=tools, y=usage_counts, text=usage_counts, textposition='auto')
                ])
                fig.update_layout(
                    title="Cumulative Tool Usage Across All Sessions",
                    xaxis_title="Tools",
                    yaxis_title="Total Usage Count"
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Conversation history
        st.header("💭 Conversation History")
        
        # Load conversation history
        history = get_conversation_history()
        
        if history:
            for message in history[-10:]:  # Show last 10 messages
                role = message.get("role", "user")
                content = message.get("content", "")
                timestamp = message.get("timestamp", "")
                
                if role == "user":
                    st.chat_message("user").write(f"**You:** {content}")
                else:
                    st.chat_message("assistant").write(f"**Assistant:** {content[:500]}...")
        else:
            st.info("No conversation history yet. Start by asking a question!")
        
        # Footer
        st.markdown("---")
        st.markdown(
            "**Dynamic Research Assistant - Enhanced Orchestrator** | "
            "Features: Dynamic tool selection, conditional routing, execution tracing | "
            "Built with Streamlit and FastAPI"
        )
        
    except Exception as e:
        st.error(f"Application error: {e}")
        st.info("Please refresh the page and try again.")

if __name__ == "__main__":
    main()
