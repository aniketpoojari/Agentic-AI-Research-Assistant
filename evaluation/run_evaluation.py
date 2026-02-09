"""
Ragas Evaluation Script for Research Assistant.

Runs the agent on test queries, computes Ragas metrics, and uploads
results to LangSmith as feedback for full traceability.
"""

import json
import asyncio
import os
import sys
import time
import uuid
from datetime import datetime
from tqdm import tqdm
from langsmith import Client

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent_workflow import ResearchAssistantWorkflow
from evaluation.ragas_evaluator import RagasEvaluator
from langchain_core.messages import ToolMessage

MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds to wait on rate limit
QUERY_DELAY = 2   # seconds between queries
MAX_QUERIES = int(os.getenv("EVAL_MAX_QUERIES", "10"))


def extract_contexts(messages):
    """Extract contexts from ToolMessages."""
    contexts = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            contexts.append(str(msg.content))
    return contexts


def run_single_query(workflow, query, max_results=3):
    """Run a single query with retry on rate limits."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return workflow.run_research(query, max_results=max_results)
        except Exception as e:
            is_rate_limit = "rate_limit" in str(e).lower() or "413" in str(e) or "429" in str(e)
            if is_rate_limit and attempt < MAX_RETRIES:
                wait = RETRY_DELAY * attempt
                print(f"  Rate limit hit (attempt {attempt}/{MAX_RETRIES}). Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


def run_evaluation():
    # Initialize LangSmith Client
    ls_client = Client()

    # Load test queries
    queries_path = os.path.join(os.path.dirname(__file__), "test_queries.json")
    print(f"Loading test queries from {queries_path}...")
    try:
        with open(queries_path, "r") as f:
            test_queries = json.load(f)
    except FileNotFoundError:
        print("Error: test_queries.json not found.")
        return

    # Limit queries to avoid excessive API usage
    test_queries = test_queries[:MAX_QUERIES]
    print(f"Running evaluation on {len(test_queries)} queries (max: {MAX_QUERIES}).")

    # Initialize Workflow and Evaluator
    workflow = ResearchAssistantWorkflow()
    evaluator = RagasEvaluator()

    results = []

    print("Starting evaluation loop...")
    session_id = f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    for i, item in enumerate(tqdm(test_queries)):
        query = item["query"]
        ground_truth = item.get("ground_truth")
        category = item.get("category", "General")

        try:
            result = run_single_query(workflow, query, max_results=3)

            # Extract output
            response = "No response"
            if result.get("messages"):
                last_msg = result["messages"][-1]
                response = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

            contexts = extract_contexts(result.get("messages", []))

            # Run Ragas Evaluation
            scores = {}
            if contexts and response:
                scores = evaluator.evaluate_response(
                    query=query,
                    response=response,
                    contexts=contexts,
                    ground_truth=ground_truth,
                )

            # Log Scores to LangSmith as Feedback
            if scores:
                try:
                    runs = list(
                        ls_client.list_runs(
                            project_name=os.getenv("LANGCHAIN_PROJECT", "default"),
                            limit=1,
                        )
                    )
                    if runs:
                        target_run_id = runs[0].id
                        for metric_name, score_value in scores.items():
                            ls_client.create_feedback(
                                target_run_id,
                                key=metric_name,
                                score=score_value,
                                comment=f"Ragas automated metric: {metric_name}",
                            )
                except Exception as ls_err:
                    print(f"Warning: Could not log feedback to LangSmith: {ls_err}")

            result_entry = {
                "query": query,
                "category": category,
                "response": response,
                "ground_truth": ground_truth,
                "contexts_count": len(contexts),
                "scores": scores,
                "timestamp": datetime.now().isoformat(),
            }
            results.append(result_entry)

        except Exception as e:
            print(f"Error processing query '{query}': {e}")
            results.append({"query": query, "error": str(e)})

        # Delay between queries to avoid rate limits
        time.sleep(QUERY_DELAY)

    # Save Results
    output_file = os.path.join(os.path.dirname(__file__), "evaluation_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_file}")

    # Compute Averages
    print("\n" + "="*30)
    print("   EVALUATION SUMMARY")
    print("="*30)

    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    for metric in metrics:
        values = [r["scores"].get(metric, 0) for r in results if "scores" in r and r["scores"]]
        if values:
            avg = sum(values) / len(values)
            print(f"{metric:18}: {avg:.4f}")
        else:
            print(f"{metric:18}: N/A")
    print("="*30)

if __name__ == "__main__":
    run_evaluation()
