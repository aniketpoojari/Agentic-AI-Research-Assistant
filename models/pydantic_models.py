"""Pydantic models for data validation and serialization."""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class QueryType(str, Enum):
    """Types of research queries."""
    SEARCH = "search"
    SUMMARIZE = "summarize"
    FACT_CHECK = "fact_check"
    EXTRACT_DATA = "extract_data"
    COMPREHENSIVE = "comprehensive"

class AgentType(str, Enum):
    """Types of agents."""
    WEB_SEARCH = "web_search"
    SUMMARIZATION = "summarization"
    FACT_CHECKING = "fact_checking"
    DATA_EXTRACTION = "data_extraction"
    CITATION = "citation"
    CONVERSATION_MEMORY = "conversation_memory"

class ResearchQuery(BaseModel):
    """Model for research queries."""
    query: str = Field(..., description="The research query")
    query_type: QueryType = Field(QueryType.COMPREHENSIVE, description="Type of research query")
    session_id: Optional[str] = Field(None, description="Session identifier")
    max_results: Optional[int] = Field(10, description="Maximum number of results")
    follow_up: bool = Field(False, description="Whether this is a follow-up query")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    @validator('query')
    def query_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class SearchResult(BaseModel):
    """Model for search results."""
    title: str = Field(..., description="Title of the search result")
    url: str = Field(..., description="URL of the search result")
    snippet: str = Field(..., description="Snippet/summary of the content")
    content: str = Field(..., description="Full content")
    source: str = Field(..., description="Search source")
    relevance_score: Optional[float] = Field(None, description="Relevance score")
    retrieved_at: datetime = Field(default_factory=datetime.now, description="When the result was retrieved")

class Citation(BaseModel):
    """Model for citations."""
    title: str = Field(..., description="Title of the source")
    url: Optional[str] = Field(None, description="URL of the source")
    formatted_citation: str = Field(..., description="Formatted citation")
    citation_style: str = Field("APA", description="Citation style used")
    source_type: str = Field("web", description="Type of source")

class FactCheckResult(BaseModel):
    """Model for fact-checking results."""
    claim: str = Field(..., description="The claim being fact-checked")
    verification: str = Field(..., description="Verification status")
    confidence: float = Field(..., description="Confidence level (0.0-1.0)")
    evidence: List[SearchResult] = Field(default_factory=list, description="Supporting evidence")
    explanation: str = Field(..., description="Explanation of the verification")

class ExtractedData(BaseModel):
    """Model for extracted data."""
    data_type: str = Field(..., description="Type of extracted data")
    data: Dict[str, Any] = Field(..., description="The extracted data")
    source_text: str = Field(..., description="Original source text")
    confidence: Optional[float] = Field(None, description="Extraction confidence")

class AgentResponse(BaseModel):
    """Model for agent responses."""
    agent_type: AgentType = Field(..., description="Type of agent")
    success: bool = Field(..., description="Whether the agent succeeded")
    data: Optional[Dict[str, Any]] = Field(None, description="Agent response data")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ResearchResult(BaseModel):
    """Model for comprehensive research results."""
    query: str = Field(..., description="Original research query")
    session_id: Optional[str] = Field(None, description="Session identifier")
    query_type: QueryType = Field(..., description="Type of research query")
    
    # Results from different agents
    search_results: Optional[List[SearchResult]] = Field(None, description="Web search results")
    summary: Optional[str] = Field(None, description="Summary of findings")
    fact_check_results: Optional[List[FactCheckResult]] = Field(None, description="Fact-check results")
    extracted_data: Optional[List[ExtractedData]] = Field(None, description="Extracted data")
    citations: Optional[List[Citation]] = Field(None, description="Citations")
    
    # Metadata
    agent_responses: List[AgentResponse] = Field(default_factory=list, description="Individual agent responses")
    total_execution_time: Optional[float] = Field(None, description="Total execution time")
    created_at: datetime = Field(default_factory=datetime.now, description="Result creation time")
    workflow_path: Optional[List[str]] = Field(None, description="Workflow execution path")
    
    # Context for follow-up queries
    context: Optional[Dict[str, Any]] = Field(None, description="Research context")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True













class ConversationMessage(BaseModel):
    """Model for conversation messages."""
    role: str = Field(..., description="Role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class SessionInfo(BaseModel):
    """Model for session information."""
    session_id: str = Field(..., description="Session identifier")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    last_activity: datetime = Field(default_factory=datetime.now, description="Last activity time")
    message_count: int = Field(0, description="Number of messages in session")
    active: bool = Field(True, description="Whether session is active")