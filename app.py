import streamlit as st
import requests

API_URL = "http://localhost:8000/research"  # Adjust if running on a different host/port

st.set_page_config(page_title="Dynamic Research Assistant", page_icon="🤖")

st.title("🤖 Dynamic Research Assistant")
st.write("Ask a research question and get a comprehensive, AI-powered answer.")

# Session state for conversation
if "session_id" not in st.session_state:
    st.session_state["session_id"] = None

# User input
query = st.text_area("Enter your research question:", height=100)

# Query type selection
query_type = st.selectbox(
    "Query Type",
    ["comprehensive", "search", "summarize", "fact_check", "extract_data"]
)

# Submit button
if st.button("Submit Query"):
    if not query.strip():
        st.warning("Please enter a research question.")
    else:
        payload = {
            "query": query,
            "query_type": query_type,
            "session_id": st.session_state["session_id"],
        }
        with st.spinner("Processing your query..."):
            try:
                response = requests.post(API_URL, json=payload, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    st.session_state["session_id"] = data.get("session_id")
                    st.success("Research completed!")
                    st.markdown(f"### **Summary**\n{data.get('summary', 'No summary available.')}")
                    if data.get("citations"):
                        st.markdown("#### Citations")
                        for c in data["citations"]:
                            st.write(f"- {c['formatted_citation']}")
                    if data.get("search_results"):
                        st.markdown("#### Search Results")
                        for r in data["search_results"]:
                            st.write(f"- [{r['title']}]({r['url']})")
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Request failed: {e}")

# Conversation history
if st.session_state["session_id"]:
    st.markdown("---")
    st.markdown("#### Conversation History")
    try:
        history_url = f"http://localhost:8000/session/{st.session_state['session_id']}/history"
        resp = requests.get(history_url)
        if resp.status_code == 200:
            history = resp.json().get("history", [])
            for msg in history:
                role = msg.get("role", "user").capitalize()
                content = msg.get("content", "")
                st.write(f"**{role}:** {content}")
        else:
            st.info("No conversation history found.")
    except Exception as e:
        st.info(f"Could not load history: {e}")
