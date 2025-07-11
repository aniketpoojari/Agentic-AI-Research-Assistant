"""Data extraction utility for the Dynamic Research Assistant."""

import re
import json
from utils.model_loader import ModelLoader
from logger.logging import get_logger

logger = get_logger(__name__)

class DataExtractor:
    """Handles structured data extraction from unstructured text."""
    
    def __init__(self, model_provider="groq"):
        try:
            self.model_loader = ModelLoader(model_provider)
            self.llm = self.model_loader.load_llm()
            logger.info(f"DataExtractor Utility Class Initialized")

        except Exception as e:
            error_msg = f"Error in DataExtractor Utility Class Initialization -> {str(e)}"
            raise Exception(error_msg)
    
    def extract_key_metrics(self, text):
        """Extract key metrics and statistics from text."""
        
        try:
            prompt = f"""Extract key metrics, statistics, and quantitative data from the following text. Format as JSON:

                        Text: {text}

                        Please extract:
                        - Numbers with units (e.g., "25%", "$1.5 million", "300 users")
                        - Dates and time periods
                        - Percentages and rates
                        - Financial figures
                        - Performance metrics

                        Format as JSON with categories: numbers, dates, percentages, financial, performance"""
            
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Try to parse as JSON, fallback to structured text
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"raw_metrics": content}
                
        except Exception as e:
            error_msg = f"Error in extract_key_metrics utility function -> {str(e)}"
            raise Exception(error_msg)
    
    def extract_entities(self, text):
        """Extract named entities from text."""
        
        try:
            prompt = f"""Extract named entities from the following text. Categorize them as:
                        - PERSON: People's names
                        - ORGANIZATION: Companies, institutions, organizations
                        - LOCATION: Cities, countries, places
                        - DATE: Dates and time expressions
                        - MONEY: Monetary values
                        - PERCENT: Percentages
                        - PRODUCT: Products, services, technologies

                        Text: {text}

                        Format as JSON with categories as keys and lists of entities as values."""
            
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Try to parse as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Fallback parsing
                return self._parse_entities_fallback(content)
                
        except Exception as e:
            error_msg = f"Error in extract_entities utility function -> {str(e)}"
            raise Exception(error_msg)
    
    def _parse_entities_fallback(self, content):
        """Fallback entity parsing when JSON parsing fails."""
        
        try:
            entities = {
                "PERSON": [],
                "ORGANIZATION": [],
                "LOCATION": [],
                "DATE": [],
                "MONEY": [],
                "PERCENT": [],
                "PRODUCT": []
            }
            
            lines = content.split('\n')
            current_category = None
            
            for line in lines:
                line = line.strip()
                if line.upper().replace(':', '') in entities:
                    current_category = line.upper().replace(':', '')
                elif current_category and line:
                    # Clean up the line
                    clean_line = line.lstrip('- *').strip()
                    if clean_line:
                        entities[current_category].append(clean_line)
            
            return entities
            
        except Exception as e:
            error_msg = f"Error in _parse_entities_fallback utility function -> {str(e)}"
            return {"error": error_msg}
    
    def extract_table_data(self, text):
        """Extract tabular data from text."""
        
        try:
            prompt = f"""Extract any tabular data from the following text. Convert tables to structured format:

                            Text: {text}

                            If there are tables, extract them as JSON arrays of objects where each object represents a row with column headers as keys."""
            
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Try to parse as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return [{"raw_table_data": content}]
                
        except Exception as e:
            error_msg = f"Error in extract_table_data utility function -> {str(e)}"
            raise Exception(error_msg)
    
    def extract_contact_info(self, text):
        """Extract contact information from text."""
        
        try:
            contact_info = {
                "emails": [],
                "phones": [],
                "urls": [],
                "addresses": []
            }
            
            # Email regex
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            contact_info["emails"] = re.findall(email_pattern, text)
            
            # Phone regex (simple pattern)
            phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            contact_info["phones"] = re.findall(phone_pattern, text)
            
            # URL regex
            url_pattern = r'https?://[^\s<>"{}|\\^`[\]]+|www\.[^\s<>"{}|\\^`[\]]+'
            contact_info["urls"] = re.findall(url_pattern, text)
            
            # Use LLM for address extraction
            prompt = f"""Extract physical addresses from the following text:

                            Text: {text}

                            List only complete addresses:"""
            
            response = self.llm.invoke(prompt)
            addresses = [line.strip() for line in response.content.split('\n') if line.strip()]
            contact_info["addresses"] = addresses
            
            return contact_info
            
        except Exception as e:
            error_msg = f"Error in extract_contact_info utility function -> {str(e)}"
            raise Exception(error_msg)
