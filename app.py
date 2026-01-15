"""Streamlit application for the Agentic Research Assistant."""

import streamlit as st
import uuid
from datetime import datetime

from agent.agent_workflow import ResearchAssistantWorkflow
from utils.config_loader import ConfigLoader

# Initialize workflow (cached to avoid reloading on every interaction)
@st.cache_resource
def get_workflow():
    """Initialize and cache the research workflow."""
    config = ConfigLoader()
    model_provider = config.get_env("MODEL_PROVIDER", "groq")
    workflow = ResearchAssistantWorkflow(model_provider=model_provider)
    workflow.build_graph()
    return workflow


def initialize_session_state():
    """Initialize session state variables."""
    if "conversation_id" not in st.session_state:
        st.session_state["conversation_id"] = str(uuid.uuid4())

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []


def run_research(workflow, query: str, conversation_id: str, max_results: int):
    """Run research query through the workflow."""
    try:
        result = workflow.run_research(query, conversation_id, max_results)
        execution_trace = workflow.get_execution_trace()

        if result and result.get("messages"):
            last_message = result["messages"][-1]
            response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            response_content = "No response generated"

        return {
            "response": response_content,
            "execution_trace": execution_trace
        }, None

    except Exception as e:
        return None, f"Error: {str(e)}"


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

    with st.expander("Execution Trace"):
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

    # Initialize workflow
    try:
        workflow = get_workflow()
    except Exception as e:
        st.error(f"Failed to initialize workflow: {str(e)}")
        st.info("Make sure GROQ_API_KEY and TAVILY_API_KEY are set in Secrets.")
        return

    # Header
    st.title("🤖 Agentic Research Assistant")
    st.markdown("Ask any question and the AI will automatically decide which tools to use.")

    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")

        st.subheader("Search Settings")
        max_results = st.slider(
            "Max Search Results",
            min_value=1,
            max_value=10,
            value=3,
            help="Number of search results to fetch."
        )

        st.divider()

        if st.button("Clear Chat History", type="primary"):
            st.session_state["chat_history"] = []
            st.session_state["conversation_id"] = str(uuid.uuid4())
            st.rerun()

        st.divider()
        st.caption(f"Session: {st.session_state['conversation_id'][:8]}...")

    # Chat interface
    st.header("Chat")

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

        # Show loading and get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking and selecting tools..."):
                # Run research
                data, error = run_research(
                    workflow,
                    prompt,
                    st.session_state["conversation_id"],
                    max_results
                )

                if error:
                    st.error(error)
                    save_to_chat_history("assistant", f"Error: {error}")
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
