"""Summarization utility for the Dynamic Research Assistant."""

import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
from utils.model_loader import ModelLoader
from utils.cache import llm_cache
from logger.logging import get_logger

logger = get_logger(__name__)

class Summarizer:
    """Handles text summarization tasks."""
    
    def __init__(self, model_provider="groq"):
        try:
            self.model_loader = ModelLoader(model_provider)
            self.llm = self.model_loader.load_llm()
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=4000,
                chunk_overlap=200,
                length_function=len
            )
            logger.info(f"Summarizer Utility Class Initialized")

        except Exception as e:
            error_msg = f"Error in Summarizer Utility Class Initialization -> {str(e)}"
            raise Exception(error_msg)
    

    def summarize_text(self, text, max_length=500):
        """Summarize a single text."""

        try:
            if not text or not text.strip():
                return "No text provided for summarization"

            if len(text) <= max_length:
                return text

            # Generate cache key from text hash and max_length
            text_hash = hashlib.md5(text.encode()).hexdigest()
            cache_key = f"summary:{text_hash}:{max_length}"

            # Check cache first
            cached_summary = llm_cache.get(cache_key)
            if cached_summary is not None:
                logger.info(f"Returning cached summary for text hash: {text_hash[:8]}...")
                return cached_summary

            prompt = f"""Please provide a concise summary of the following text in approximately {max_length} words:

                        Text: {text}

                        Summary:"""

            response = self.llm.invoke(prompt)
            summary = response.content.strip()

            if not summary:
                return "Unable to generate summary"

            # Cache the summary (30 min TTL)
            llm_cache.set(cache_key, summary, ttl=1800)

            logger.info(f"Text summarized successfully: {len(text)} -> {len(summary)} characters")
            return summary
            
        except Exception as e:
            error_msg = f"Error in summarize_text utility function -> {str(e)}"
            raise Exception(error_msg)
    
    
    def create_executive_summary(self, documents, topic):
        """Create an executive summary from multiple documents."""
        
        try:
            if not documents:
                return "No documents provided for executive summary"
            
            # First, summarize individual documents
            summaries = []
            for doc in documents:
                try:
                    content = doc.get("content", "")
                    if content:
                        summary = self.summarize_text(content, 300)
                        summaries.append({
                            "title": doc.get("title", "Unknown"),
                            "summary": summary,
                            "url": doc.get("url", "")
                        })
                except Exception as e:
                    logger.warning(f"Failed to summarize document {doc.get('title', 'Unknown')}: {e}")
                    continue
            
            if not summaries:
                return "No valid documents could be summarized"
            
            # Create combined summary
            combined_text = "\n\n".join([f"Source: {s['title']}\n{s['summary']}" for s in summaries])
            
            prompt = f"""Based on the following research summaries about "{topic}", create a comprehensive executive summary that synthesizes the key findings, insights, and conclusions:

                            {combined_text}

                            Executive Summary:"""
            
            response = self.llm.invoke(prompt)
            executive_summary = response.content.strip()
            
            if not executive_summary:
                return "Unable to generate executive summary"
            
            return executive_summary
            
        except Exception as e:
            error_msg = f"Error in create_executive_summary utility function -> {str(e)}"
            raise Exception(error_msg)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    def extract_key_points(self, text, num_points=5):
        """Extract key points from text."""
        
        try:
            if not text or not text.strip():
                return []
            
            prompt = f"""Extract the {num_points} most important key points from the following text. Format as a numbered list:

                        Text: {text}

                        Key Points:"""
            
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            if not content:
                return []
            
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
            
            result = key_points[:num_points]
            return result
            
        except Exception as e:
            error_msg = f"Error in extract_key_points utility function -> {str(e)}"
            raise Exception(error_msg)