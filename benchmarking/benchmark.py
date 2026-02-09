import json
import os
import sys
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

# Add parent directory to path to allow imports from other modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent_workflow import ResearchAssistantWorkflow
from evaluation.ragas_evaluator import RagasEvaluator
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, ToolMessage
from utils.config_loader import ConfigLoader
from logger.logging import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds to wait on rate limit

def run_agent_and_baseline(agent, baseline_llm, item):
    """Run both agent and baseline for a single query with retry on rate limits."""
    query = item["query"]
    ground_truth = item.get("ground_truth")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # 1. Run Agent
            agent_result = agent.run_research(query, max_results=3)

            agent_response = agent_result["messages"][-1].content

            # Extract context from agent run
            contexts = []
            for msg in agent_result["messages"]:
                if isinstance(msg, ToolMessage):
                    contexts.append(str(msg.content))

            # If no context was found, force a search for benchmark
            if not contexts:
                logger.info(f"No context found for '{query}', forcing a search for benchmark.")
                search_res = agent.web_search_tools.web_search.search(query, num_results=3)
                contexts = [str(r) for r in search_res]

            # 2. Run Baseline (with same context)
            context_str = "\n\n".join(contexts)
            prompt = f"Use the following context to answer the question: {query}\n\nContext:\n{context_str}"
            baseline_response = baseline_llm.invoke([HumanMessage(content=prompt)]).content

            return {
                "query": query,
                "ground_truth": ground_truth,
                "agent_response": agent_response,
                "baseline_response": baseline_response,
                "contexts": contexts
            }
        except Exception as e:
            is_rate_limit = "rate_limit" in str(e).lower() or "413" in str(e) or "429" in str(e)
            if is_rate_limit and attempt < MAX_RETRIES:
                wait = RETRY_DELAY * attempt
                logger.warning(f"Rate limit hit for '{query}' (attempt {attempt}/{MAX_RETRIES}). Retrying in {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"Error processing query '{query}' (attempt {attempt}): {e}")
                return None

def run_benchmark(num_queries=5):
    # Load configuration
    config = ConfigLoader()
    api_key = config.get_api_key("groq")
    
    # Initialize Agent
    print("Initializing Agent...")
    agent = ResearchAssistantWorkflow(model_provider="groq")
    
    # Initialize Baseline Groq Model (Llama 3.3 70b)
    baseline_model_name = "llama-3.3-70b-versatile"
    print(f"Initializing Baseline Model ({baseline_model_name})...")
    baseline_llm = ChatGroq(
        groq_api_key=api_key,
        model_name=baseline_model_name,
        temperature=0
    )
    
    # Initialize Evaluator
    evaluator = RagasEvaluator()
    
    # Load test queries
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    queries_path = os.path.join(base_dir, "evaluation", "test_queries.json")
    
    with open(queries_path, "r") as f:
        test_queries = json.load(f)
    
    # Limit queries for speed if needed
    if num_queries:
        test_queries = test_queries[:num_queries]
        
    print(f"Running benchmark on {len(test_queries)} queries sequentially (with rate-limit delays)...")

    raw_results = []
    failed_queries = []
    for item in tqdm(test_queries, desc="Executing Queries"):
        res = run_agent_and_baseline(agent, baseline_llm, item)
        if res:
            raw_results.append(res)
        else:
            failed_queries.append(item["query"])
        # Delay between queries to avoid rate limits
        time.sleep(2)

    if failed_queries:
        print(f"\n{len(failed_queries)} queries failed: {failed_queries}")

    if not raw_results:
        print("No successful results to evaluate.")
        return

    print(f"Evaluating {len(raw_results)} results in batch...")
    
    # Batch Evaluate Agent
    agent_scores = evaluator.evaluate_batch(
        queries=[r["query"] for r in raw_results],
        responses=[r["agent_response"] for r in raw_results],
        contexts_list=[r["contexts"] for r in raw_results],
        ground_truths=[r["ground_truth"] for r in raw_results]
    )
    
    # Batch Evaluate Baseline
    baseline_scores = evaluator.evaluate_batch(
        queries=[r["query"] for r in raw_results],
        responses=[r["baseline_response"] for r in raw_results],
        contexts_list=[r["contexts"] for r in raw_results],
        ground_truths=[r["ground_truth"] for r in raw_results]
    )
    
    # Aggregate results
    def aggregate(scores_list):
        if not scores_list:
            return {}
        df = pd.DataFrame(scores_list)
        return df.mean().to_dict()

    comparison = {
        "my_agent": aggregate(agent_scores),
        "groq_baseline": aggregate(baseline_scores)
    }
    
    # Save results
    output_dir = os.path.dirname(os.path.abspath(__file__))
    comparison_path = os.path.join(output_dir, "benchmark_comparison.json")
    
    with open(comparison_path, "w") as f:
        json.dump(comparison, f, indent=2)
    
    print(f"Benchmark results saved to {comparison_path}")
    
    # Generate visualization
    generate_chart(comparison, output_dir)

def generate_chart(comparison, output_dir):
    metrics = list(comparison["my_agent"].keys())
    if not metrics:
        print("No metrics to plot.")
        return
        
    agent_scores = [comparison["my_agent"].get(m, 0) or 0 for m in metrics]
    baseline_scores = [comparison["groq_baseline"].get(m, 0) or 0 for m in metrics]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, agent_scores, width, label='My Agent')
    rects2 = ax.bar(x + width/2, baseline_scores, width, label='Groq Baseline')
    
    ax.set_ylabel('Scores')
    ax.set_title('Benchmark Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1.1)
    ax.legend()
    
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')

    autolabel(rects1)
    autolabel(rects2)
    
    fig.tight_layout()
    chart_path = os.path.join(output_dir, "benchmark_chart.png")
    plt.savefig(chart_path)
    print(f"Benchmark chart saved to {chart_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--num", type=int, default=3, help="Number of queries to run")
    args = parser.parse_args()

    run_benchmark(num_queries=args.num)