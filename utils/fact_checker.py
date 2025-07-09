"""Fact-checking utility for the Dynamic Research Assistant."""

import logging
from typing import List, Dict, Any
from utils.websearch import WebSearch
from utils.model_loader import ModelLoader
from exception.exception_handling import ToolException

logger = logging.getLogger(__name__)

class FactChecker:
    """Handles fact-checking operations."""
    
    def __init__(self, model_provider: str = "groq"):
        self.model_loader = ModelLoader(model_provider)
        self.llm = self.model_loader.load_llm()
        self.web_search = WebSearch()
    

    def extract_and_verify_claims(self, text: str) -> List[Dict[str, Any]]:
        """Extract claims from text and verify them."""
        try:
            # Extract claims
            claims = self.extract_claims(text)
            
            # Verify each claim
            verification_results = []
            for claim in claims:
                result = self.verify_claim(claim)
                verification_results.append(result)
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Claim extraction and verification failed: {e}")
            raise ToolException(f"Claim extraction and verification failed: {e}")
    
    
    def extract_claims(self, text: str) -> List[str]:
        """Extract factual claims from text."""
        try:
            prompt = f"""Extract the main factual claims from the following text. List only specific, verifiable statements:

                        Text: {text}

                        Factual Claims:"""
            
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Parse claims
            lines = content.split('\n')
            claims = []
            
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                    clean_line = line.lstrip('0123456789.-* ').strip()
                    if clean_line:
                        claims.append(clean_line)
            
            return claims
            
        except Exception as e:
            logger.error(f"Claim extraction failed: {e}")
            raise ToolException(f"Claim extraction failed: {e}")
    
    def verify_claim(self, claim: str) -> Dict[str, Any]:
        """Verify a specific claim using web search."""
        try:
            # Search for evidence
            search_results = self.web_search.search(f"fact check {claim}", 5)
            
            if not search_results:
                return {
                    "claim": claim,
                    "verification": "insufficient_evidence",
                    "confidence": 0.0,
                    "evidence": [],
                    "explanation": "No search results found to verify this claim."
                }
            
            # Analyze evidence
            evidence_text = "\n\n".join([
                f"Source: {result['title']}\nContent: {result['content'][:500]}..."
                for result in search_results
            ])
            
            prompt = f"""As a fact-checker, analyze the following claim and evidence. Provide a verification assessment:

                        Claim: {claim}

                        Evidence:
                        {evidence_text}

                        Please provide:
                        1. Verification status (true/false/partially_true/unverified)
                        2. Confidence level (0.0-1.0)
                        3. Brief explanation of your assessment

                        Response format:
                        Status: [status]
                        Confidence: [0.0-1.0]
                        Explanation: [your explanation]"""
            
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Parse response
            lines = content.split('\n')
            verification_result = {
                "claim": claim,
                "verification": "unverified",
                "confidence": 0.0,
                "evidence": search_results,
                "explanation": content
            }
            
            for line in lines:
                if line.startswith("Status:"):
                    status = line.split(":", 1)[1].strip().lower()
                    verification_result["verification"] = status
                elif line.startswith("Confidence:"):
                    try:
                        confidence = float(line.split(":", 1)[1].strip())
                        verification_result["confidence"] = confidence
                    except ValueError:
                        pass
                elif line.startswith("Explanation:"):
                    explanation = line.split(":", 1)[1].strip()
                    verification_result["explanation"] = explanation
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Claim verification failed: {e}")
            raise ToolException(f"Fact-checking failed: {e}")