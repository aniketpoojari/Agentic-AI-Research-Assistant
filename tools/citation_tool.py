"""Citation tool for the Dynamic Research Assistant."""

from langchain.tools import tool
from dotenv import load_dotenv
from utils.citation_manager import CitationManager

class CitationTool:
    def __init__(self, model_provider="groq"):
        try:
            load_dotenv()
            self.citation_manager = CitationManager(model_provider)
            self.citation_tool_list = self._setup_tools()
        except Exception as e:
            error_msg = f"Error in CitationTool.__init__: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)

    def _setup_tools(self):
        """Setup all tools for citation management"""
        
        @tool
        def generate_citations(sources: str, style: str = "APA"):
            """Generate citations for given sources in specified style"""
            try:
                import json
                sources_list = json.loads(sources)
                citations = self.citation_manager.generate_citations(sources_list, style)
                return {
                    "success": True,
                    "citations": citations,
                    "style": style,
                    "total_sources": len(sources_list)
                }
            except Exception as e:
                error_msg = f"Error in generate_citations: {str(e)}"
                print(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        @tool
        def create_bibliography(sources: str, style: str = "APA"):
            """Create a formatted bibliography from sources"""
            try:
                import json
                sources_list = json.loads(sources)
                bibliography = self.citation_manager.create_bibliography(sources_list, style)
                return {
                    "success": True,
                    "bibliography": bibliography,
                    "style": style
                }
            except Exception as e:
                error_msg = f"Error in create_bibliography: {str(e)}"
                print(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        @tool
        def validate_sources(sources: str):
            """Validate and clean source information"""
            try:
                import json
                sources_list = json.loads(sources)
                validated = self.citation_manager.validate_sources(sources_list)
                return {
                    "success": True,
                    "validated_sources": validated,
                    "total_sources": len(validated)
                }
            except Exception as e:
                error_msg = f"Error in validate_sources: {str(e)}"
                print(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        return [generate_citations, create_bibliography, validate_sources]
