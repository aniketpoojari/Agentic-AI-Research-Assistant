"""Citation management utility for the Dynamic Research Assistant."""

import logging
from typing import List, Dict, Any
from datetime import datetime
from utils.model_loader import ModelLoader
from exception.exception_handling import ToolException, handle_tool_exceptions

logger = logging.getLogger(__name__)

class CitationManager:
    """Handles citation generation and management."""
    
    def __init__(self, model_provider: str = "groq"):
        self.model_loader = ModelLoader(model_provider)
        self.llm = self.model_loader.load_llm()


    @handle_tool_exceptions
    def create_bibliography(self, sources: List[Dict[str, Any]], style: str = "APA") -> str:
        """Create a formatted bibliography."""
        try:
            citations = self.generate_citations(sources, style)
            
            if not citations:
                return "No sources to cite."
            
            bibliography = f"{style.upper()} Bibliography:\n\n"
            
            for i, citation in enumerate(citations, 1):
                bibliography += f"{i}. {citation}\n"
            
            return bibliography
            
        except Exception as e:
            logger.error(f"Bibliography creation failed: {e}")
            raise ToolException(f"Bibliography creation failed: {e}")


    def generate_citations(self, sources: List[Dict[str, Any]], style: str = "APA") -> List[str]:
        """Generate citations in the specified style."""
        try:
            citations = []
            
            for source in sources:
                citation = self.format_citation(source, style)
                if citation:
                    citations.append(citation)
            
            return citations
            
        except Exception as e:
            logger.error(f"Citation generation failed: {e}")
            raise ToolException(f"Citation generation failed: {e}")
    
    def format_citation(self, source: Dict[str, Any], style: str = "APA") -> str:
        """Format a single citation."""
        try:
            if style.upper() == "APA":
                return self._format_apa_citation(source)
            elif style.upper() == "MLA":
                return self._format_mla_citation(source)
            elif style.upper() == "CHICAGO":
                return self._format_chicago_citation(source)
            else:
                return self._format_basic_citation(source)
                
        except Exception as e:
            logger.error(f"Citation formatting failed: {e}")
            return self._format_basic_citation(source)
    
    def _format_apa_citation(self, source: Dict[str, Any]) -> str:
        """Format citation in APA style."""
        title = source.get("title", "Unknown Title")
        url = source.get("url", "")
        retrieved_date = datetime.now().strftime("%B %d, %Y")
        
        # Basic web source format
        if url:
            return f"{title}. Retrieved {retrieved_date}, from {url}"
        else:
            return f"{title}. (n.d.)"
    
    def _format_mla_citation(self, source: Dict[str, Any]) -> str:
        """Format citation in MLA style."""
        title = source.get("title", "Unknown Title")
        url = source.get("url", "")
        retrieved_date = datetime.now().strftime("%d %b %Y")
        
        if url:
            return f'"{title}." Web. {retrieved_date}. <{url}>'
        else:
            return f'"{title}." Print.'
    
    def _format_chicago_citation(self, source: Dict[str, Any]) -> str:
        """Format citation in Chicago style."""
        title = source.get("title", "Unknown Title")
        url = source.get("url", "")
        retrieved_date = datetime.now().strftime("%B %d, %Y")
        
        if url:
            return f'"{title}." Accessed {retrieved_date}. {url}.'
        else:
            return f'"{title}."'
    
    def _format_basic_citation(self, source: Dict[str, Any]) -> str:
        """Format basic citation."""
        title = source.get("title", "Unknown Title")
        url = source.get("url", "")
        
        if url:
            return f"{title} - {url}"
        else:
            return title


    def validate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean source information."""
        validated_sources = []
        
        for source in sources:
            validated_source = {
                "title": source.get("title", "Unknown Title"),
                "url": source.get("url", ""),
                "content": source.get("content", ""),
                "snippet": source.get("snippet", ""),
                "source": source.get("source", "unknown"),
                "retrieved_date": datetime.now().isoformat(),
                "is_valid": bool(source.get("title") and (source.get("url") or source.get("content")))
            }
            
            validated_sources.append(validated_source)
        
        return validated_sources


    
    

    
    