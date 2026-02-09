"""
Ragas Evaluation Module for the Research Assistant.

Handles initialization of Ragas metrics and evaluation of agent responses.
"""

import os
import math
from typing import Dict, Any, List, Optional
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.llms import LangchainLLMWrapper
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from utils.config_loader import ConfigLoader
from logger.logging import get_logger

logger = get_logger(__name__)

class RagasEvaluator:
    def __init__(self):
        self.config = ConfigLoader()
        self.metrics_history = []
        self._setup_ragas()

    def _setup_ragas(self):
        """Configure Ragas with available LLM and Embeddings."""
        try:
            # Load LLM (reuse Groq configuration)
            api_key = self.config.get_api_key("groq")
            model_name = self.config.get_env("MODEL_NAME", "llama-3.1-8b-instant")
            
            self.llm = ChatGroq(
                groq_api_key=api_key,
                model_name=model_name,
                temperature=0
            )
            
            # Wrap for Ragas
            self.ragas_llm = LangchainLLMWrapper(self.llm)
            
            # Load Embeddings (use HuggingFace as free alternative to OpenAI)
            # using all-MiniLM-L6-v2 which is small and effective
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            logger.info("RagasEvaluator initialized with Groq LLM and HF Embeddings")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ragas: {e}")
            self.ragas_llm = None
            self.embeddings = None

    def _bind_metrics(self, metrics: List[Any]):
        """Explicitly bind LLM and embeddings to metrics to avoid OpenAI defaults."""
        for metric in metrics:
            if hasattr(metric, "llm"):
                metric.llm = self.ragas_llm
            if hasattr(metric, "embeddings") and self.embeddings:
                metric.embeddings = self.embeddings

    def evaluate_response(
        self, 
        query: str, 
        response: str, 
        contexts: List[str], 
        ground_truth: Optional[str] = None
    ) -> Dict[str, float]:
        """Evaluate a single response using Ragas."""
        results = self.evaluate_batch(
            queries=[query],
            responses=[response],
            contexts_list=[contexts],
            ground_truths=[ground_truth] if ground_truth else None
        )
        return results[0] if results else {}

    def evaluate_batch(
        self, 
        queries: List[str], 
        responses: List[str], 
        contexts_list: List[List[str]], 
        ground_truths: Optional[List[str]] = None
    ) -> List[Dict[str, float]]:
        """
        Evaluate a batch of responses using Ragas for much better performance.
        """
        if not self.ragas_llm or not queries:
            return []

        try:
            # Prepare data
            data = {
                "question": queries,
                "answer": responses,
                "contexts": contexts_list,
            }
            
            metrics = [faithfulness, answer_relevancy]
            
            if ground_truths and any(ground_truths):
                data["ground_truth"] = ground_truths
                metrics.extend([context_precision, context_recall])
            
            self._bind_metrics(metrics)
                
            dataset = Dataset.from_dict(data)
            
            # Run evaluation
            results = evaluate(
                dataset=dataset,
                metrics=metrics,
                llm=self.ragas_llm,
                embeddings=self.embeddings
            )
            
            df = results.to_pandas()
            
            # Convert DataFrame to list of dicts, handling NaNs
            batch_results = []
            metric_names = [m.name for m in metrics]
            
            for _, row in df.iterrows():
                scores = {}
                for col in metric_names:
                    if col in row:
                        val = float(row[col])
                        scores[col] = None if math.isnan(val) else val
                batch_results.append(scores)
            
            # Store in history
            self.metrics_history.extend(batch_results)
            
            return batch_results

        except Exception as e:
            logger.error(f"Ragas batch evaluation failed: {e}")
            return [{} for _ in queries]

    def get_aggregate_metrics(self) -> Dict[str, float]:
        """Calculate average scores from history."""
        if not self.metrics_history:
            return {}
            
        aggregates = {}
        keys = self.metrics_history[0].keys()
        
        for key in keys:
            values = [m.get(key, 0) for m in self.metrics_history if key in m]
            if values:
                aggregates[key] = sum(values) / len(values)
                
        return aggregates

    def clear_history(self):
        self.metrics_history = []