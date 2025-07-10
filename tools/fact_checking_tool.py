"""Fact-checking tool for the Dynamic Research Assistant."""

import os
from typing import List
from langchain.tools import tool
from dotenv import load_dotenv
from utils.fact_checker import FactChecker

class FactCheckingTool:
    def __init__(self, model_provider: str = "groq"):
        load_dotenv()
        self.fact_checker = FactChecker(model_provider)
        self.fact_checking_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
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
                return {
                    "success": False,
                    "error": "Claim verification failed: " + str(e),
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
                return {
                    "success": False,
                    "error": "Claim extraction and verification failed: " + str(e)
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
                return {
                    "success": False,
                    "error": "Claim extraction failed: " + str(e)
                }
        
        return [verify_claim, extract_and_verify_claims, extract_claims]
