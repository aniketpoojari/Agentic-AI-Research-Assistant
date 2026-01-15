"""Fact-checking tool for the Dynamic Research Assistant."""

from langchain_core.tools import tool
from utils.fact_checker import FactChecker
from logger.logging import get_logger

logger = get_logger(__name__)

class FactCheckingTool:
    def __init__(self, model_provider="groq"):
        try:
            self.fact_checker = FactChecker(model_provider)
            self.fact_checking_tool_list = self._setup_tools()
            logger.info("FactCheckingTool Class Initialized")

        except Exception as e:
            error_msg = f"Error in FactCheckingTool Class Initialization -> {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _setup_tools(self):
        """Setup all tools for fact-checking"""
        
        @tool
        def verify_claim(claim: str):
            """Verify a specific factual claim"""

            try:
                result = self.fact_checker.verify_claim(claim)
                return {
                    "success": True,
                    "verification_result": result
                }
            
            except Exception as e:
                error_msg = f"Error in verify_claim tool -> {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "claim": claim
                }
        
        @tool
        def extract_and_verify_claims(text: str):
            """Extract claims from text and verify them"""
            
            try:
                results = self.fact_checker.extract_and_verify_claims(text)
                return {
                    "success": True,
                    "verification_results": results,
                    "total_claims": len(results)
                }
            
            except Exception as e:
                error_msg = f"Error in extract_and_verify_claims tool -> {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        @tool
        def extract_claims(text: str):
            """Extract factual claims from text"""

            try:
                claims = self.fact_checker.extract_claims(text)
                return {
                    "success": True,
                    "claims": claims,
                    "total_claims": len(claims)
                }
            
            except Exception as e:
                error_msg = f"Error in extract_claims tool -> {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        return [verify_claim, extract_and_verify_claims, extract_claims]
