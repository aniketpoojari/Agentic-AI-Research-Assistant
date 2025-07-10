"""Summarization utility for the Dynamic Research Assistant."""

import logging
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter

from utils.model_loader import ModelLoader
# from exception.exception_handling import ToolException

logger = logging.getLogger(__name__)

class Summarizer:
    """Handles text summarization tasks."""
    
    def __init__(self, model_provider: str = "groq"):
        self.model_loader = ModelLoader(model_provider)
        self.llm = self.model_loader.load_llm()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200,
            length_function=len
        )
    
    def summarize_text(self, text: str, max_length: int = 500) -> str:
        """Summarize a single text."""
        # try:
        if len(text) <= max_length:
            return text
        
        prompt = f"""Please provide a concise summary of the following text in approximately {max_length} words:

                    Text: {text}

                    Summary:"""
        
        response = self.llm.invoke(prompt)
        return response.content.strip()
        
        # except Exception as e:
        #     logger.error(f"Text summarization failed: {e}")
        #     raise ToolException(f"Summarization failed: {e}")
    
    
    def create_executive_summary(self, documents: List[Dict[str, Any]], topic: str) -> str:
        """Create an executive summary from multiple documents."""
        # try:
        # First, summarize individual documents
        summaries = []
        for doc in documents:
            content = doc.get("content", "")
            if content:
                summary = self.summarize_text(content, 300)
                summaries.append({
                    "title": doc.get("title", "Unknown"),
                    "summary": summary,
                    "url": doc.get("url", "")
                })
        
        # Create combined summary
        combined_text = "\n\n".join([f"Source: {s['title']}\n{s['summary']}" for s in summaries])
        
        prompt = f"""Based on the following research summaries about "{topic}", create a comprehensive executive summary that synthesizes the key findings, insights, and conclusions:

                    {combined_text}

                    Executive Summary:"""
        
        response = self.llm.invoke(prompt)
        return response.content.strip()
            
        # except Exception as e:
        #     logger.error(f"Executive summary creation failed: {e}")
        #     raise ToolException(f"Executive summary creation failed: {e}")
    
    def extract_key_points(self, text: str, num_points: int = 5) -> List[str]:
        """Extract key points from text."""
        # try:
        prompt = f"""Extract the {num_points} most important key points from the following text. Format as a numbered list:

                    Text: {text}

                    Key Points:"""
        
        response = self.llm.invoke(prompt)
        content = response.content.strip()
        
        # Parse the response into a list
        lines = content.split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                # Remove numbering/bullets
                clean_line = line.lstrip('0123456789.-* ').strip()
                if clean_line:
                    key_points.append(clean_line)
        
        return key_points[:num_points]
            
        # except Exception as e:
        #     logger.error(f"Key point extraction failed: {e}")
        #     raise ToolException(f"Key point extraction failed: {e}")