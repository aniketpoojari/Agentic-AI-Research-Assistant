"""Citation management utility for the Dynamic Research Assistant."""

from datetime import datetime
from utils.model_loader import ModelLoader
from logger.logging import get_logger

logger = get_logger(__name__)

class CitationManager:
    """Handles citation generation and management."""
    
    def __init__(self, model_provider="groq"):
        try:
            self.model_loader = ModelLoader(model_provider)
            self.llm = self.model_loader.load_llm()
            logger.info(f"CitationManager Utility Class Initialized")

        except Exception as e:
            error_msg = f"Error in CitationManager Utility Class Initialization -> {str(e)}"
            raise Exception(error_msg)

    def create_bibliography(self, sources, style="APA"):
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
            error_msg = f"Error in create_bibliography utility function -> {str(e)}"
            raise Exception(error_msg)

    def generate_citations(self, sources, style="APA"):
        """Generate citations in the specified style."""
        
        try:
            citations = []
            
            for source in sources:
                citation = self.format_citation(source, style)
                if citation:
                    citations.append(citation)
            
            return citations
            
        except Exception as e:
            error_msg = f"Error in generate_citations utility function -> {str(e)}"
            raise Exception(error_msg)

    def format_citation(self, source, style="APA"):
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
            error_msg = f"Error in format_citation utility function -> {str(e)}"
            raise Exception(error_msg)

    def _format_apa_citation(self, source):
        """Format citation in APA style."""
        
        try:
            title = source.get("title", "Unknown Title")
            url = source.get("url", "")
            retrieved_date = datetime.now().strftime("%B %d, %Y")
            
            # Basic web source format
            if url:
                return f"{title}. Retrieved {retrieved_date}, from {url}"
            else:
                return f"{title}. (n.d.)"
            
        except Exception as e:
            error_msg = f"Error in _format_apa_citation utility function -> {str(e)}"
            raise Exception(error_msg)
    
    def _format_mla_citation(self, source):
        """Format citation in MLA style."""
        
        try:
            title = source.get("title", "Unknown Title")
            url = source.get("url", "")
            retrieved_date = datetime.now().strftime("%d %b %Y")
            
            if url:
                return f'"{title}." Web. {retrieved_date}. <{url}>'
            else:
                return f'"{title}." Print.'
            
        except Exception as e:
            error_msg = f"Error in _format_mla_citation utility function -> {str(e)}"
            raise Exception(error_msg)
    
    def _format_chicago_citation(self, source):
        """Format citation in Chicago style."""
        
        try:
            title = source.get("title", "Unknown Title")
            url = source.get("url", "")
            retrieved_date = datetime.now().strftime("%B %d, %Y")
            
            if url:
                return f'"{title}." Accessed {retrieved_date}. {url}.'
            else:
                return f'"{title}."'
            
        except Exception as e:
            error_msg = f"Error in _format_chicago_citation utility function -> {str(e)}"
            raise Exception(error_msg)
    
    def _format_basic_citation(self, source):
        """Format basic citation."""
        
        try:
            title = source.get("title", "Unknown Title")
            url = source.get("url", "")
            
            if url:
                return f"{title} - {url}"
            else:
                return title
            
        except Exception as e:
            error_msg = f"Error in _format_basic_citation utility function -> {str(e)}"
            raise Exception(error_msg)

    def validate_sources(self, sources):
        """Validate and clean source information."""
        
        try:
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
            
        except Exception as e:
            error_msg = f"Error in validate_sources utility function -> {str(e)}"
            raise Exception(error_msg)
