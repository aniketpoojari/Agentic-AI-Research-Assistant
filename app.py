"""Simplified Streamlit application for the Dynamic Research Assistant."""

import streamlit as st
import requests
import uuid
from datetime import datetime


RESEARCH_ENDPOINT = "http://127.0.0.1:8000/research"

def initialize_session_state():
    """Initialize session state variables."""
    if "conversation_id" not in st.session_state:
        st.session_state["conversation_id"] = str(uuid.uuid4())
    
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

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

def save_to_chat_history(role, content):
    """Save message to local chat history."""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    st.session_state["chat_history"].append(message)

def display_execution_trace(trace):
    """Display simple execution trace."""
    if not trace:
        return
        
    with st.expander("🔍 Execution Trace"):
        for step in trace:
            step_name = step.get("step", "unknown")
            timestamp = step.get("timestamp", "")
            details = step.get("details", {})
            
            st.write(f"**{step_name}** - {timestamp}")
            if details:
                st.json(details)
            st.write("---")

def main():
    """Main Streamlit application."""
    # Page configuration
    st.set_page_config(
        page_title="Research Assistant",
        page_icon="🤖",
        layout="wide"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("🤖 Research Assistant")
    st.markdown("Ask any question and the AI will automatically decide which tools to use.")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        max_results = st.slider("Max Search Results", 1, 20, 10)
        
        if st.button("Clear Chat History"):
            st.session_state["chat_history"] = []
            st.session_state["conversation_id"] = str(uuid.uuid4())
            st.rerun()
    
    # Chat interface
    st.header("💬 Chat")
    
    # Display chat history
    for message in st.session_state["chat_history"]:
        role = message.get("role", "user")
        content = message.get("content", "")
        
        if role == "user":
            with st.chat_message("user"):
                st.write(content)
        else:
            with st.chat_message("assistant"):
                st.write(content)
    
    # Chat input
    if prompt := st.chat_input("Ask your research question..."):
        # Display user message immediately
        with st.chat_message("user"):
            st.write(prompt)
        
        # Save user message to chat history
        save_to_chat_history("user", prompt)
        
        # Prepare payload
        payload = {
            "query": prompt,
            "conversation_id": st.session_state["conversation_id"],
            "max_results": max_results
        }
        
        # Show loading and get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking and selecting tools..."):
                # Make API request
                data, error = make_api_request(payload)
                
                if error:
                    error_message = f"❌ {error}"
                    st.error(error_message)
                    save_to_chat_history("assistant", error_message)
                else:
                    # Display response
                    response = data.get("response", "No response generated")
                    st.write(response)
                    
                    # Save assistant response to chat history
                    save_to_chat_history("assistant", response)
                    
                    # Display execution trace
                    execution_trace = data.get("execution_trace", [])
                    if execution_trace:
                        display_execution_trace(execution_trace)

if __name__ == "__main__":
    main()
