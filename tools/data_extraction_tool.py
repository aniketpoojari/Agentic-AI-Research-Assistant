"""Data extraction tool for the Dynamic Research Assistant."""

import os
from typing import List
from langchain.tools import tool
from dotenv import load_dotenv
from utils.data_extractor import DataExtractor

class DataExtractionTool:
    def __init__(self, model_provider: str = "groq"):
        load_dotenv()
        self.data_extractor = DataExtractor(model_provider)
        self.data_extraction_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
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
                return {
                    "success": False,
                    "error": str(e)
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
                return {
                    "success": False,
                    "error": str(e)
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
                return {
                    "success": False,
                    "error": str(e)
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
                return {
                    "success": False,
                    "error": str(e)
                }
        
        return [extract_key_metrics, extract_entities, extract_contact_info, extract_table_data]
