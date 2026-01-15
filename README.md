---
title: Agentic AI Research Assistant
emoji: 🧠
colorFrom: indigo
colorTo: purple
sdk: streamlit
sdk_version: 1.40.0
app_file: app.py
pinned: false
license: mit
---

# 🧠 Agentic AI Research Assistant

An **advanced agentic AI research assistant** that revolutionizes research workflows through intelligent automation and sophisticated tool orchestration. This cutting-edge system leverages a LangGraph-powered state machine architecture to autonomously select, chain, and execute specialized tools, transforming complex research tasks into streamlined, efficient processes without requiring manual intervention.

Built on a foundation of modular design principles, the Dynamic Research Assistant integrates multiple AI providers, advanced web search capabilities, intelligent document processing, real-time fact verification, and comprehensive data extraction tools. The system features persistent conversation memory, sophisticated citation management, and a dual-interface architecture that supports both programmatic API access and interactive web-based usage.

The platform's agent-driven architecture automatically analyzes incoming queries, determines the optimal tool selection strategy, and executes multi-step research workflows that combine web search, content extraction, summarization, fact-checking, data mining, and citation generation. This autonomous approach eliminates the need for users to manually configure pipelines or understand the underlying complexity, instead providing a seamless research experience that adapts to diverse query types and complexity levels.

## 🚀 Features

- **Autonomous Agent Architecture**: Utilizes a LangGraph-powered state machine to intelligently orchestrate multi-step workflows by adaptively selecting and chaining tools based on query analysis, intermediate results, conversation history, and user preferences—enabling fully automated, context-aware decision making.

- **Multi-Provider LLM Support**: Enables dynamic model selection and seamless switching between providers like Groq (LLaMA 3 8B) and OpenAI (GPT-4), optimizing for speed, availability, and task-specific requirements without requiring system reconfiguration.

- **Tools**:
    - **Web Search Tools**: Enables advanced, multi-source web search with intelligent result aggregation, content extraction, and redundancy support for reliable information retrieval.
    Tools: `search_web`, `get_page_content`
    - **Summarization Tools**: Support intelligent, multi-layered summarization of complex documents, with capabilities for executive synthesis and key point extraction across multiple sources.
    Tools: `summarize_text`, `create_executive_summary`, `extract_key_points`
    - **Fact Checking Tools**: Automate claim detection and verification using real-time data, multi-source evidence, credibility scoring, and contradiction resolution.
    Tools: `verify_claim`, `extract_and_verify_claims`, `extract_claims`
    - **Data Extraction Tools**: Extract structured data—including metrics, entities, contact info, and tables—from unstructured text with precision and formatting support.
    Tools: `extract_key_metrics`, `extract_entities`, `extract_contact_info`, `extract_table_data`
    - **Citation Management Tools**: Generate citations, create bibliographies, and validate sources for academic and professional use.
    Tools: `generate_citations`, `create_bibliography`, `validate_sources`
    - **Memory Management Tools**: Maintain persistent conversation memory, enabling cross-session continuity and historical context retrieval.
    Tools: `get_conversation_history`

- **Dual Interface Design**: Features a FastAPI backend running on port 8000 that provides programmatic access and seamless integration capabilities, a Streamlit frontend on port 7860 delivering an interactive web-based research environment, RESTful API endpoints designed for comprehensive system integration and automation workflows, real-time execution tracking with detailed workflow visualization to monitor process progress, and a responsive web interface optimized for various device types to ensure accessibility across desktop, tablet, and mobile platforms.

- **Robust Automated Testing and Continuous Deployment Pipeline**: Every Git push triggers an integrated testing workflow powered by GitHub Actions, running the comprehensive test suite—including LangSmith-guided quality checks, trajectory analysis for tool orchestration, response quality evaluation, and performance benchmarking. Only after all tests pass is the codebase automatically deployed to Huggingface Spaces, ensuring users always access the latest, fully tested, and reliable version of the platform.


## 🔧 Quickstart

### Local Installation

```bash
# Clone the repository
git clone https://github.com/your-org/dynamic-research-assistant.git
cd dynamic-research-assistant

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export GROQ_API_KEY="your-groq-api-key"
export TAVILY_API_KEY="your-tavily-api-key"  # Optional

# Start the FastAPI backend
uvicorn main:app --reload --reload-ignore "logs/*"

# In a new terminal, start the Streamlit frontend
streamlit run app.py
```

### Docker Deployment

```bash
# Build the Docker image
docker build -t research-assistant .

# Run with environment variables
docker run -p 8000:8000 -p 7860:7860 \
  -e GROQ_API_KEY="your-groq-api-key" \
  -e TAVILY_API_KEY="your-tavily-api-key" \
  research-assistant
```


## 📌 Results

### **System Performance Metrics**
Based on the LangSmith evaluation results, the Dynamic Research Assistant demonstrates exceptional performance across all testing dimensions:

| Metric | Performance | Status |
|--------|-------------|--------|
| **Final Response Quality** | 100% (0.999 score) | ✅ Passed |
| **Trajectory Execution** | 100% success rate | ✅ Passed |
| **Individual Tool Performance** | 100% (3/3 tools) | ✅ Passed |
| **Overall Test Suite** | 100% pass rate | ✅ Passed |

### **Detailed Test Results**

#### **Final Response Evaluation**
The system achieved **near-perfect quality scores** on complex research queries:
- **Query Processing**: Successfully handled renewable energy storage technology research
- **Response Quality**: 99.9% quality score with comprehensive 1,678-character responses
- **Content Depth**: Demonstrated ability to provide detailed, well-structured answers
- **Accuracy**: Maintained high factual accuracy throughout complex technical topics

#### **Agent Workflow Trajectory Analysis**
The LangGraph-powered state machine executed flawlessly with intelligent tool orchestration:
- **Workflow Execution**: Complete 6-step trajectory from start to finish
- **Tool Selection**: Automatically selected `search_web` and `summarize_text` tools
- **Decision Making**: Demonstrated adaptive decision-making with "no_tools_needed" optimization
- **Query Handling**: Successfully processed AI safety research paper analysis requests
- **Completion Rate**: 100% successful workflow completion

#### **Individual Tool Performance Assessment**

**Web Search Tool Performance**:
- **Status**: ✅ Passed
- **Results Retrieved**: 5 comprehensive search results
- **Reliability**: Consistent performance across multiple search queries
- **Coverage**: Successfully accessed diverse information sources

**Summarization Tool Performance**:
- **Status**: ✅ Passed
- **Compression Efficiency**: 41.2% compression ratio (4,326 → 1,781 characters)
- **Content Preservation**: Maintained key information while reducing length
- **Processing Speed**: Efficient handling of multi-document summarization

**Fact-Checking Tool Performance**:
- **Status**: ✅ Passed
- **Verification Confidence**: 90% confidence score
- **Accuracy**: "True" verification status for tested claims
- **Reliability**: Consistent fact-checking across diverse content types