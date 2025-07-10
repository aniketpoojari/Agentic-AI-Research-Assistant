"""Summarization utility for the Dynamic Research Assistant."""

import logging
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from utils.model_loader import ModelLoader

logger = logging.getLogger(__name__)

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
            logger.info(f"Summarizer initialized with {model_provider} provider")
        except Exception as e:
            error_msg = f"Error in Summarizer.__init__: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            raise Exception(error_msg)
    
    def summarize_text(self, text, max_length=500):
        """Summarize a single text."""
        try:
            if not text or not text.strip():
                return "No text provided for summarization"
            
            if len(text) <= max_length:
                return text
            
            prompt = f"""Please provide a concise summary of the following text in approximately {max_length} words:

Text: {text}

Summary:"""
            
            response = self.llm.invoke(prompt)
            summary = response.content.strip()
            
            if not summary:
                return "Unable to generate summary"
            
            logger.info(f"Text summarized successfully: {len(text)} -> {len(summary)} characters")
            return summary
            
        except Exception as e:
            error_msg = f"Error in summarize_text: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
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
            
            logger.info(f"Executive summary created for topic: {topic}")
            return executive_summary
            
        except Exception as e:
            error_msg = f"Error in create_executive_summary: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
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
            logger.info(f"Extracted {len(result)} key points from text")
            return result
            
        except Exception as e:
            error_msg = f"Error in extract_key_points: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            raise Exception(error_msg)
    
    def summarize_multiple_texts(self, texts, max_length=500):
        """Summarize multiple texts into a single summary."""
        try:
            if not texts:
                return "No texts provided for summarization"
            
            # Combine all texts
            combined_text = "\n\n".join([str(text) for text in texts if text])
            
            if not combined_text:
                return "No valid text content found"
            
            return self.summarize_text(combined_text, max_length)
            
        except Exception as e:
            error_msg = f"Error in summarize_multiple_texts: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            raise Exception(error_msg)
    
    def get_text_statistics(self, text):
        """Get basic statistics about the text."""
        try:
            if not text:
                return {
                    "character_count": 0,
                    "word_count": 0,
                    "sentence_count": 0,
                    "paragraph_count": 0
                }
            
            # Basic statistics
            char_count = len(text)
            word_count = len(text.split())
            sentence_count = len([s for s in text.split('.') if s.strip()])
            paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
            
            stats = {
                "character_count": char_count,
                "word_count": word_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count
            }
            
            logger.info(f"Text statistics calculated: {stats}")
            return stats
            
        except Exception as e:
            error_msg = f"Error in get_text_statistics: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            return {
                "character_count": 0,
                "word_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "error": error_msg
            }
