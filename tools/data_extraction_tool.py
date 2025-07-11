"""Data extraction tool for the Dynamic Research Assistant."""

from langchain.tools import tool
from utils.data_extractor import DataExtractor
from logger.logging import get_logger

logger = get_logger(__name__)

class DataExtractionTool:
    def __init__(self, model_provider="groq"):
        try:
            self.data_extractor = DataExtractor(model_provider)
            self.data_extraction_tool_list = self._setup_tools()
            logger.info("DataExtractionTool Class Initialized")

        except Exception as e:
            error_msg = f"Error in DataExtractionTool Class Initialization -> {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _setup_tools(self):
        """Setup all tools for data extraction"""
        
        @tool
        def extract_key_metrics(text: str):
            """Extract key metrics and statistics from text"""
            
            try:
                metrics = self.data_extractor.extract_key_metrics(text)
                return {
                    "success": True,
                    "metrics": metrics
                }
            
            except Exception as e:
                error_msg = f"Error in extract_key_metrics tool -> {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        @tool
        def extract_entities(text: str):
            """Extract named entities from text"""
            
            try:
                entities = self.data_extractor.extract_entities(text)
                return {
                    "success": True,
                    "entities": entities

                }
            
            except Exception as e:
                error_msg = f"Error in extract_entities tool -> {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        @tool
        def extract_contact_info(text: str):
            """Extract contact information from text"""
            
            try:
                contact_info = self.data_extractor.extract_contact_info(text)
                return {
                    "success": True,
                    "contact_info": contact_info
                }
            
            except Exception as e:
                error_msg = f"Error in extract_contact_info tool -> {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        @tool
        def extract_table_data(text: str):
            """Extract tabular data from text"""

            try:
                table_data = self.data_extractor.extract_table_data(text)
                return {
                    "success": True,
                    "table_data": table_data
                }
            
            except Exception as e:
                error_msg = f"Error in extract_table_data tool -> {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        return [extract_key_metrics, extract_entities, extract_contact_info, extract_table_data]
