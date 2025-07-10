"""Streamlit application for the Dynamic Research Assistant."""

import streamlit as st
import requests
import json
import uuid
from datetime import datetime

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

def clear_session():
    """Clear current session."""
    try:
        clear_url = f"{API_URL}/session/{st.session_state['session_id']}"
        requests.delete(clear_url, timeout=30)
        
        # Reset session state
        st.session_state["session_id"] = str(uuid.uuid4())
        st.session_state["conversation_history"] = []
        st.session_state["research_results"] = []
        
        st.success("Session cleared successfully!")
        
    except Exception as e:
        st.error(f"Error clearing session: {e}")

def main():
    """Main Streamlit application."""
    try:
        # Page configuration
        st.set_page_config(
            page_title="Dynamic Research Assistant",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize session state
        initialize_session_state()
        
        # Header
        st.title("🤖 Dynamic Research Assistant")
        st.markdown("Ask any research question and get comprehensive, AI-powered answers with automatic tool selection.")
        
        # Sidebar
        with st.sidebar:
            st.header("⚙️ Settings")
            
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
                    st.success("✅ API Connected")
                else:
                    st.error("❌ API Error")
            except:
                st.error("❌ API Disconnected")
            
            # Statistics
            st.subheader("Statistics")
            try:
                stats_response = requests.get(f"{API_URL}/stats", timeout=10)
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    if "system_stats" in stats:
                        st.write(f"**Total Sessions:** {stats['system_stats'].get('total_sessions', 0)}")
                        st.write(f"**Total Conversations:** {stats['system_stats'].get('total_conversations', 0)}")
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
                            "include_fact_check": include_fact_check
                        }
                    }
                    
                    # Show loading
                    with st.spinner("🔍 Processing your query... This may take a moment."):
                        # Make API request
                        data, error = make_api_request(payload)
                        
                        if error:
                            st.error(f"❌ {error}")
                        else:
                            # Store results
                            st.session_state["research_results"].append({
                                "query": query,
                                "results": data,
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            # Display results
                            st.success("✅ Research completed!")
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
            else:
                st.info("No recent results. Submit a query to get started!")
        
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
            "**Dynamic Research Assistant** - Powered by AI agents with automatic tool selection | "
            "Built with Streamlit and FastAPI"
        )
        
    except Exception as e:
        st.error(f"Application error: {e}")
        st.info("Please refresh the page and try again.")

if __name__ == "__main__":
    main()
