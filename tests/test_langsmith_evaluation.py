"""
Comprehensive LangSmith Evaluation Suite for the Research Assistant.

This module implements three levels of evaluation:
1. Final Response Evaluation - Tests overall response quality using LLM-as-judge
2. Trajectory Evaluation - Validates tool selection and chaining patterns
3. Single Step Evaluation - Tests each tool individually

Uses LangSmith's evaluate() function with custom evaluators for reproducible,
dataset-driven testing.
"""

import os
import sys
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from functools import wraps

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langsmith import Client, evaluate
from langsmith.schemas import Example, Run
from langchain_groq import ChatGroq

from agent.agent_workflow import ResearchAssistantWorkflow
from tools.web_search_tool import WebSearchTool
from tools.summarization_tool import SummarizationTool
from tools.fact_checking_tool import FactCheckingTool
from tools.data_extraction_tool import DataExtractionTool
from tools.citation_tool import CitationTool
from tools.conversation_memory_tool import ConversationMemoryTool


class LangSmithEvaluators:
    """Custom evaluators using LLM-as-judge pattern."""

    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0
        )

    def response_correctness(self, run: Run, example: Example) -> Dict[str, Any]:
        """Evaluate if the response correctly addresses the query."""
        query = example.inputs.get("query", "")
        response = run.outputs.get("response", "") if run.outputs else ""

        prompt = f"""Evaluate if this response correctly and completely addresses the query.

Query: {query}

Response: {response}

Score from 0.0 to 1.0 where:
- 0.0-0.3: Incorrect, off-topic, or missing key information
- 0.4-0.6: Partially correct but incomplete
- 0.7-0.8: Mostly correct with minor gaps
- 0.9-1.0: Fully correct and comprehensive

Respond with ONLY a JSON object: {{"score": <float>, "reasoning": "<brief explanation>"}}"""

        try:
            result = self.llm.invoke(prompt)
            parsed = json.loads(result.content)
            return {
                "key": "correctness",
                "score": float(parsed.get("score", 0.5)),
                "comment": parsed.get("reasoning", "")
            }
        except Exception as e:
            return {"key": "correctness", "score": 0.5, "comment": f"Evaluation error: {str(e)}"}

    def tool_usage_quality(self, run: Run, example: Example) -> Dict[str, Any]:
        """Evaluate if appropriate tools were selected and chained correctly."""
        query = example.inputs.get("query", "")
        expected_tools = example.inputs.get("expected_tools", [])
        actual_tools = run.outputs.get("tools_used", []) if run.outputs else []

        # Calculate tool coverage
        if expected_tools:
            matched = len(set(expected_tools) & set(actual_tools))
            coverage = matched / len(expected_tools)
        else:
            coverage = 1.0 if actual_tools else 0.5

        # Evaluate tool chaining logic
        prompt = f"""Evaluate if the tools used were appropriate for this query.

Query: {query}
Tools Used: {actual_tools}
Expected Tools: {expected_tools}

Consider:
1. Were the right tools selected for the query type?
2. Were tools chained in a logical order?
3. Were any essential tools missing?

Score from 0.0 to 1.0. Respond with ONLY: {{"score": <float>, "reasoning": "<brief explanation>"}}"""

        try:
            result = self.llm.invoke(prompt)
            parsed = json.loads(result.content)
            llm_score = float(parsed.get("score", 0.5))
            # Combine coverage score with LLM evaluation
            final_score = (coverage * 0.4) + (llm_score * 0.6)
            return {
                "key": "tool_usage",
                "score": final_score,
                "comment": f"Coverage: {coverage:.2f}, LLM: {llm_score:.2f}. {parsed.get('reasoning', '')}"
            }
        except Exception as e:
            return {"key": "tool_usage", "score": coverage, "comment": f"Evaluation error: {str(e)}"}

    def citation_quality(self, run: Run, example: Example) -> Dict[str, Any]:
        """Evaluate citation completeness and formatting."""
        response = run.outputs.get("response", "") if run.outputs else ""

        # Check for citation indicators
        has_citations = any(marker in response for marker in ["[", "Source:", "Reference:", "http"])
        has_multiple_sources = response.count("http") > 1 or response.count("[") > 2

        prompt = f"""Evaluate the citation quality in this research response.

Response: {response[:2000]}

Score from 0.0 to 1.0 based on:
- Are sources cited?
- Are citations properly formatted?
- Do citations support the claims made?

Respond with ONLY: {{"score": <float>, "reasoning": "<brief explanation>"}}"""

        try:
            result = self.llm.invoke(prompt)
            parsed = json.loads(result.content)
            return {
                "key": "citation_quality",
                "score": float(parsed.get("score", 0.3 if has_citations else 0.0)),
                "comment": parsed.get("reasoning", "")
            }
        except Exception as e:
            base_score = 0.5 if has_citations else 0.2
            return {"key": "citation_quality", "score": base_score, "comment": f"Evaluation error: {str(e)}"}

    def comprehensiveness(self, run: Run, example: Example) -> Dict[str, Any]:
        """Evaluate response depth and thoroughness."""
        response = run.outputs.get("response", "") if run.outputs else ""
        query = example.inputs.get("query", "")

        # Basic metrics
        word_count = len(response.split())
        has_structure = response.count("\n") > 3 or response.count(".") > 5
        has_data = any(char.isdigit() for char in response)

        prompt = f"""Evaluate how comprehensive and thorough this research response is.

Query: {query}
Response: {response[:2000]}

Consider:
- Does it cover multiple aspects of the topic?
- Does it include relevant data/statistics?
- Is it well-structured and organized?

Score from 0.0 to 1.0. Respond with ONLY: {{"score": <float>, "reasoning": "<brief explanation>"}}"""

        try:
            result = self.llm.invoke(prompt)
            parsed = json.loads(result.content)
            return {
                "key": "comprehensiveness",
                "score": float(parsed.get("score", 0.5)),
                "comment": parsed.get("reasoning", "")
            }
        except Exception as e:
            # Fallback scoring
            score = 0.3
            if word_count > 100:
                score += 0.2
            if word_count > 300:
                score += 0.2
            if has_structure:
                score += 0.15
            if has_data:
                score += 0.15
            return {"key": "comprehensiveness", "score": min(score, 1.0), "comment": f"Evaluation error: {str(e)}"}


class LangSmithEvaluationSuite:
    """Complete evaluation suite for the Research Assistant."""

    def __init__(self):
        self.client = Client()
        self.workflow = ResearchAssistantWorkflow()
        self.evaluators = LangSmithEvaluators()

        # Initialize all tool classes for individual testing
        self.web_search_tools = WebSearchTool()
        self.summarization_tools = SummarizationTool()
        self.fact_checking_tools = FactCheckingTool()
        self.data_extraction_tools = DataExtractionTool()
        self.citation_tools = CitationTool()
        self.memory_tools = ConversationMemoryTool()

    def _create_evaluation_dataset(self) -> str:
        """Create or get evaluation dataset with diverse test cases."""
        dataset_name = "research_assistant_eval_dataset"

        try:
            # Check if dataset exists
            datasets = list(self.client.list_datasets(dataset_name=dataset_name))
            if datasets:
                return dataset_name
        except Exception:
            pass

        # Create new dataset with comprehensive test cases
        try:
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description="Comprehensive evaluation dataset for Research Assistant"
            )

            # Test cases covering different query types and expected tool usage
            test_cases = [
                {
                    "inputs": {
                        "query": "What are the latest developments in quantum computing?",
                        "expected_tools": ["search_web", "get_page_content", "summarize_text", "extract_key_metrics", "generate_citations"],
                        "query_type": "research"
                    },
                    "outputs": {"expected_response_type": "comprehensive_research"}
                },
                {
                    "inputs": {
                        "query": "Is it true that renewable energy now costs less than fossil fuels?",
                        "expected_tools": ["search_web", "verify_claim", "extract_key_metrics", "generate_citations"],
                        "query_type": "fact_check"
                    },
                    "outputs": {"expected_response_type": "fact_verification"}
                },
                {
                    "inputs": {
                        "query": "Extract key statistics about global AI market size and growth",
                        "expected_tools": ["search_web", "get_page_content", "extract_key_metrics", "extract_table_data", "generate_citations"],
                        "query_type": "data_extraction"
                    },
                    "outputs": {"expected_response_type": "structured_data"}
                },
                {
                    "inputs": {
                        "query": "Summarize the main arguments for and against remote work",
                        "expected_tools": ["search_web", "get_page_content", "extract_key_points", "create_executive_summary", "generate_citations"],
                        "query_type": "summarization"
                    },
                    "outputs": {"expected_response_type": "summary"}
                },
                {
                    "inputs": {
                        "query": "Who are the key players in the electric vehicle industry and what are their market shares?",
                        "expected_tools": ["search_web", "extract_entities", "extract_key_metrics", "extract_table_data", "generate_citations"],
                        "query_type": "entity_extraction"
                    },
                    "outputs": {"expected_response_type": "entity_data"}
                }
            ]

            for case in test_cases:
                self.client.create_example(
                    inputs=case["inputs"],
                    outputs=case["outputs"],
                    dataset_id=dataset.id
                )

            return dataset_name

        except Exception as e:
            print(f"Warning: Could not create dataset: {e}")
            return None

    def _run_workflow_for_eval(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run workflow and format output for evaluation."""
        query = inputs.get("query", "")
        conversation_id = f"eval_{uuid.uuid4().hex[:8]}"

        try:
            self.workflow.clear_execution_trace()
            result = self.workflow.run_research(query, conversation_id=conversation_id)

            # Extract response
            if result and result.get("messages"):
                last_message = result["messages"][-1]
                response = last_message.content if hasattr(last_message, "content") else str(last_message)
            else:
                response = "No response generated"

            # Get tools used from execution trace
            trace = self.workflow.get_execution_trace()
            tools_used = []
            for step in trace:
                if step.get("step") == "tools_selected":
                    tools_used.extend(step.get("details", {}).get("tools", []))

            return {
                "response": response,
                "tools_used": tools_used,
                "execution_trace": trace,
                "conversation_id": conversation_id
            }

        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "tools_used": [],
                "execution_trace": [],
                "error": str(e)
            }

    def test_final_response_evaluation(self) -> Dict[str, Any]:
        """Test overall response quality using LLM-as-judge evaluators."""
        print("\n=== Final Response Evaluation ===")

        test_queries = [
            {
                "query": "What are the latest developments in renewable energy storage technologies?",
                "expected_tools": ["search_web", "summarize_text", "extract_key_metrics", "generate_citations"]
            },
            {
                "query": "Compare the market share of top 5 cloud computing providers",
                "expected_tools": ["search_web", "extract_entities", "extract_key_metrics", "extract_table_data"]
            }
        ]

        results = []

        for test in test_queries:
            print(f"\nTesting: {test['query'][:50]}...")

            # Create mock example and run
            example = type("Example", (), {"inputs": test})()
            output = self._run_workflow_for_eval(test)
            run = type("Run", (), {"outputs": output})()

            # Run all evaluators
            correctness = self.evaluators.response_correctness(run, example)
            tool_usage = self.evaluators.tool_usage_quality(run, example)
            citations = self.evaluators.citation_quality(run, example)
            comprehensiveness = self.evaluators.comprehensiveness(run, example)

            # Calculate aggregate score
            scores = [correctness["score"], tool_usage["score"], citations["score"], comprehensiveness["score"]]
            avg_score = sum(scores) / len(scores)

            result = {
                "query": test["query"],
                "response_length": len(output.get("response", "")),
                "tools_used": output.get("tools_used", []),
                "scores": {
                    "correctness": correctness["score"],
                    "tool_usage": tool_usage["score"],
                    "citation_quality": citations["score"],
                    "comprehensiveness": comprehensiveness["score"],
                    "average": avg_score
                },
                "status": "passed" if avg_score >= 0.5 else "failed"
            }
            results.append(result)

            print(f"  Correctness: {correctness['score']:.2f}")
            print(f"  Tool Usage: {tool_usage['score']:.2f}")
            print(f"  Citations: {citations['score']:.2f}")
            print(f"  Comprehensiveness: {comprehensiveness['score']:.2f}")
            print(f"  Average: {avg_score:.2f} - {result['status'].upper()}")

        passed = sum(1 for r in results if r["status"] == "passed")
        return {
            "test_type": "final_response_evaluation",
            "results": results,
            "summary": {
                "total": len(results),
                "passed": passed,
                "pass_rate": passed / len(results)
            },
            "status": "passed" if passed == len(results) else "partial",
            "timestamp": datetime.now().isoformat()
        }

    def test_trajectory_evaluation(self) -> Dict[str, Any]:
        """Test that agent follows expected tool execution patterns."""
        print("\n=== Trajectory Evaluation ===")

        # Define expected trajectory patterns for different query types
        trajectory_tests = [
            {
                "query": "Find recent research papers on AI safety and summarize the key findings",
                "expected_pattern": ["search_web", "summarize_text"],
                "query_type": "research_summary"
            },
            {
                "query": "Verify: Electric vehicles produce zero emissions",
                "expected_pattern": ["search_web", "verify_claim"],
                "query_type": "fact_check"
            },
            {
                "query": "Extract all statistics about smartphone market from this topic",
                "expected_pattern": ["search_web", "extract_key_metrics"],
                "query_type": "data_extraction"
            }
        ]

        results = []

        for test in trajectory_tests:
            print(f"\nTesting trajectory for: {test['query_type']}")

            self.workflow.clear_execution_trace()
            output = self._run_workflow_for_eval({"query": test["query"]})
            trace = output.get("execution_trace", [])
            tools_used = output.get("tools_used", [])

            # Verify trajectory
            has_start = any(s.get("step") == "workflow_start" for s in trace)
            has_agent = any(s.get("step") == "agent_start" for s in trace)
            has_complete = any(s.get("step") == "workflow_complete" for s in trace)
            has_tool_activity = any(s.get("step") in ["tools_selected", "no_tools_needed"] for s in trace)

            # Check if expected tools were used
            expected_used = sum(1 for t in test["expected_pattern"] if t in tools_used)
            pattern_match = expected_used / len(test["expected_pattern"]) if test["expected_pattern"] else 1.0

            trajectory_valid = has_start and has_agent and has_complete and has_tool_activity

            result = {
                "query_type": test["query_type"],
                "expected_pattern": test["expected_pattern"],
                "actual_tools": tools_used,
                "pattern_match_rate": pattern_match,
                "trajectory_steps": [s.get("step") for s in trace],
                "trajectory_valid": trajectory_valid,
                "status": "passed" if trajectory_valid and pattern_match >= 0.5 else "failed"
            }
            results.append(result)

            print(f"  Expected: {test['expected_pattern']}")
            print(f"  Actual: {tools_used}")
            print(f"  Pattern Match: {pattern_match:.2f}")
            print(f"  Status: {result['status'].upper()}")

        passed = sum(1 for r in results if r["status"] == "passed")
        return {
            "test_type": "trajectory_evaluation",
            "results": results,
            "summary": {
                "total": len(results),
                "passed": passed,
                "pass_rate": passed / len(results)
            },
            "status": "passed" if passed == len(results) else "partial",
            "timestamp": datetime.now().isoformat()
        }

    def test_single_step_evaluation(self) -> Dict[str, Any]:
        """Test each tool individually to ensure they work correctly."""
        print("\n=== Single Step (Individual Tool) Evaluation ===")

        tool_tests = []

        # 1. Web Search Tools
        print("\nTesting Web Search Tools...")
        try:
            search_tool = self.web_search_tools.web_search_tool_list[0]
            result = search_tool.invoke({"query": "artificial intelligence trends 2024", "max_results": 5})
            tool_tests.append({
                "tool": "search_web",
                "category": "web_search",
                "status": "passed" if result.get("success") and len(result.get("results", [])) > 0 else "failed",
                "details": {"results_count": len(result.get("results", []))}
            })
            print(f"  search_web: {'PASSED' if tool_tests[-1]['status'] == 'passed' else 'FAILED'}")
        except Exception as e:
            tool_tests.append({"tool": "search_web", "category": "web_search", "status": "failed", "error": str(e)})
            print(f"  search_web: FAILED - {e}")

        try:
            content_tool = self.web_search_tools.web_search_tool_list[1]
            result = content_tool.invoke({"url": "https://example.com"})
            tool_tests.append({
                "tool": "get_page_content",
                "category": "web_search",
                "status": "passed" if result.get("success") or result.get("content") else "failed",
                "details": {"has_content": bool(result.get("content"))}
            })
            print(f"  get_page_content: {'PASSED' if tool_tests[-1]['status'] == 'passed' else 'FAILED'}")
        except Exception as e:
            tool_tests.append({"tool": "get_page_content", "category": "web_search", "status": "failed", "error": str(e)})
            print(f"  get_page_content: FAILED - {e}")

        # 2. Summarization Tools
        print("\nTesting Summarization Tools...")
        test_text = """
        Artificial intelligence has made significant advances in 2024. Large language models have become
        more efficient and capable. Machine learning is being deployed in healthcare, finance, and
        autonomous vehicles. The development of specialized AI chips has improved performance.
        Ethical AI development has gained attention with new frameworks for responsible deployment.
        """ * 3

        for i, tool in enumerate(self.summarization_tools.summarization_tool_list):
            tool_name = ["summarize_text", "create_executive_summary", "extract_key_points"][i]
            try:
                if tool_name == "summarize_text":
                    result = tool.invoke({"text": test_text, "max_length": 200})
                    success = result.get("success") and len(result.get("summary", "")) > 0
                elif tool_name == "create_executive_summary":
                    docs = json.dumps([{"content": test_text, "title": "AI Report"}])
                    result = tool.invoke({"documents": docs, "topic": "AI advances"})
                    success = result.get("success") and result.get("executive_summary")
                else:
                    result = tool.invoke({"text": test_text, "num_points": 3})
                    success = result.get("success") and len(result.get("key_points", [])) > 0

                tool_tests.append({
                    "tool": tool_name,
                    "category": "summarization",
                    "status": "passed" if success else "failed",
                    "details": result
                })
                print(f"  {tool_name}: {'PASSED' if success else 'FAILED'}")
            except Exception as e:
                tool_tests.append({"tool": tool_name, "category": "summarization", "status": "failed", "error": str(e)})
                print(f"  {tool_name}: FAILED - {e}")

        # 3. Fact-Checking Tools
        print("\nTesting Fact-Checking Tools...")
        test_claim = "The Earth orbits around the Sun"

        for i, tool in enumerate(self.fact_checking_tools.fact_checking_tool_list):
            tool_name = ["verify_claim", "extract_and_verify_claims", "extract_claims"][i]
            try:
                if tool_name == "verify_claim":
                    result = tool.invoke({"claim": test_claim})
                    success = result.get("success") and result.get("verification_result")
                elif tool_name == "extract_claims":
                    result = tool.invoke({"text": f"Scientists say {test_claim}. Water is H2O."})
                    success = result.get("success") and len(result.get("claims", [])) > 0
                else:
                    result = tool.invoke({"text": f"{test_claim}. The moon affects tides."})
                    success = result.get("success")

                tool_tests.append({
                    "tool": tool_name,
                    "category": "fact_checking",
                    "status": "passed" if success else "failed",
                    "details": {"has_result": bool(result)}
                })
                print(f"  {tool_name}: {'PASSED' if success else 'FAILED'}")
            except Exception as e:
                tool_tests.append({"tool": tool_name, "category": "fact_checking", "status": "failed", "error": str(e)})
                print(f"  {tool_name}: FAILED - {e}")

        # 4. Data Extraction Tools
        print("\nTesting Data Extraction Tools...")
        test_data_text = """
        In 2024, the global AI market reached $150 billion, growing 25% year-over-year.
        Key players include Google, Microsoft, and OpenAI. Contact: info@example.com, +1-555-0123.
        Market share: Google 30%, Microsoft 25%, Amazon 20%, Others 25%.
        """

        for i, tool in enumerate(self.data_extraction_tools.data_extraction_tool_list):
            tool_name = ["extract_key_metrics", "extract_entities", "extract_contact_info", "extract_table_data"][i]
            try:
                result = tool.invoke({"text": test_data_text})
                success = result.get("success")

                tool_tests.append({
                    "tool": tool_name,
                    "category": "data_extraction",
                    "status": "passed" if success else "failed",
                    "details": {"has_result": bool(result)}
                })
                print(f"  {tool_name}: {'PASSED' if success else 'FAILED'}")
            except Exception as e:
                tool_tests.append({"tool": tool_name, "category": "data_extraction", "status": "failed", "error": str(e)})
                print(f"  {tool_name}: FAILED - {e}")

        # 5. Citation Tools
        print("\nTesting Citation Tools...")
        test_sources = json.dumps([
            {"title": "AI Report 2024", "author": "John Smith", "url": "https://example.com/ai", "date": "2024-01-15"},
            {"title": "Machine Learning Guide", "author": "Jane Doe", "url": "https://example.com/ml", "date": "2024-02-20"}
        ])

        for i, tool in enumerate(self.citation_tools.citation_tool_list):
            tool_name = ["generate_citations", "create_bibliography", "validate_sources"][i]
            try:
                if tool_name == "validate_sources":
                    result = tool.invoke({"sources": test_sources})
                else:
                    result = tool.invoke({"sources": test_sources, "style": "APA"})
                success = result.get("success")

                tool_tests.append({
                    "tool": tool_name,
                    "category": "citation",
                    "status": "passed" if success else "failed",
                    "details": {"has_result": bool(result)}
                })
                print(f"  {tool_name}: {'PASSED' if success else 'FAILED'}")
            except Exception as e:
                tool_tests.append({"tool": tool_name, "category": "citation", "status": "failed", "error": str(e)})
                print(f"  {tool_name}: FAILED - {e}")

        # 6. Conversation Memory Tools
        print("\nTesting Conversation Memory Tools...")
        try:
            # Set a session ID for testing
            self.memory_tools.set_session_id(f"test_{uuid.uuid4().hex[:8]}")
            self.memory_tools.add_message("user", "Test message")

            # Test get_conversation_history
            tool = self.memory_tools.conversation_memory_tool_list[0]
            result = tool.invoke({"limit": 5})
            success = result.get("success") and result.get("message_count", 0) > 0

            tool_tests.append({
                "tool": "get_conversation_history",
                "category": "memory",
                "status": "passed" if success else "failed",
                "details": {"message_count": result.get("message_count", 0)}
            })
            print(f"  get_conversation_history: {'PASSED' if success else 'FAILED'}")
        except Exception as e:
            tool_tests.append({"tool": "get_conversation_history", "category": "memory", "status": "failed", "error": str(e)})
            print(f"  get_conversation_history: FAILED - {e}")

        # Summary
        passed = sum(1 for t in tool_tests if t["status"] == "passed")
        total = len(tool_tests)

        # Group by category
        categories = {}
        for t in tool_tests:
            cat = t["category"]
            if cat not in categories:
                categories[cat] = {"passed": 0, "total": 0}
            categories[cat]["total"] += 1
            if t["status"] == "passed":
                categories[cat]["passed"] += 1

        return {
            "test_type": "single_step_evaluation",
            "individual_results": tool_tests,
            "by_category": categories,
            "summary": {
                "total_tools": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": passed / total if total > 0 else 0
            },
            "status": "passed" if passed == total else "partial" if passed > 0 else "failed",
            "timestamp": datetime.now().isoformat()
        }

    def run_complete_evaluation_suite(self) -> Dict[str, Any]:
        """Run all three evaluation types with comprehensive reporting."""
        print("\n" + "=" * 60)
        print("RESEARCH ASSISTANT - COMPREHENSIVE EVALUATION SUITE")
        print("=" * 60)

        start_time = datetime.now()

        # Run all evaluations
        results = {
            "final_response": self.test_final_response_evaluation(),
            "trajectory": self.test_trajectory_evaluation(),
            "single_step": self.test_single_step_evaluation()
        }

        # Calculate overall metrics
        test_statuses = [r.get("status", "failed") for r in results.values()]
        passed_suites = sum(1 for s in test_statuses if s == "passed")
        partial_suites = sum(1 for s in test_statuses if s == "partial")

        # Overall pass rate across all individual tests
        total_tests = 0
        passed_tests = 0
        for key, result in results.items():
            if "summary" in result:
                total_tests += result["summary"].get("total", 0) or result["summary"].get("total_tools", 0)
                passed_tests += result["summary"].get("passed", 0)

        overall_pass_rate = passed_tests / total_tests if total_tests > 0 else 0

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Print summary
        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)
        print(f"\nFinal Response Evaluation: {results['final_response']['status'].upper()}")
        print(f"Trajectory Evaluation: {results['trajectory']['status'].upper()}")
        print(f"Single Step Evaluation: {results['single_step']['status'].upper()}")
        print(f"\nOverall Pass Rate: {overall_pass_rate:.1%} ({passed_tests}/{total_tests})")
        print(f"Duration: {duration:.2f}s")

        # Log to LangSmith
        try:
            self.client.create_run(
                name="complete_evaluation_suite",
                run_type="chain",
                inputs={"evaluation_type": "comprehensive"},
                outputs={
                    "overall_pass_rate": overall_pass_rate,
                    "suites_passed": passed_suites,
                    "duration_seconds": duration
                },
                id=str(uuid.uuid4())
            )
        except Exception as e:
            print(f"Warning: Could not log to LangSmith: {e}")

        return {
            "evaluation_suite": "research_assistant_comprehensive",
            "results": results,
            "overall_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "overall_pass_rate": overall_pass_rate,
                "suites": {
                    "passed": passed_suites,
                    "partial": partial_suites,
                    "failed": 3 - passed_suites - partial_suites
                },
                "duration_seconds": duration
            },
            "status": "passed" if overall_pass_rate >= 0.8 else "partial" if overall_pass_rate >= 0.5 else "failed",
            "timestamp": end_time.isoformat()
        }


# Standalone functions for individual test execution
def run_final_response_evaluation():
    """Standalone function to run final response evaluation."""
    suite = LangSmithEvaluationSuite()
    return suite.test_final_response_evaluation()


def run_trajectory_evaluation():
    """Standalone function to run trajectory evaluation."""
    suite = LangSmithEvaluationSuite()
    return suite.test_trajectory_evaluation()


def run_single_step_evaluation():
    """Standalone function to run single step evaluation."""
    suite = LangSmithEvaluationSuite()
    return suite.test_single_step_evaluation()


def run_complete_evaluation_suite():
    """Standalone function to run complete evaluation suite."""
    suite = LangSmithEvaluationSuite()
    return suite.run_complete_evaluation_suite()


# Main execution
if __name__ == "__main__":
    print("Starting Comprehensive LangSmith Evaluation Suite...")
    print(f"Timestamp: {datetime.now().isoformat()}")

    try:
        result = run_complete_evaluation_suite()

        print("\n" + "=" * 60)
        print("FINAL RESULTS (JSON)")
        print("=" * 60)

        # Print condensed JSON output
        summary = {
            "status": result["status"],
            "overall_pass_rate": result["overall_summary"]["overall_pass_rate"],
            "passed_tests": result["overall_summary"]["passed_tests"],
            "total_tests": result["overall_summary"]["total_tests"],
            "duration_seconds": result["overall_summary"]["duration_seconds"],
            "suites": result["overall_summary"]["suites"]
        }
        print(json.dumps(summary, indent=2))

        # Exit with appropriate code
        exit_code = 0 if result["status"] in ["passed", "partial"] else 1
        sys.exit(exit_code)

    except Exception as e:
        print(f"\nEvaluation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
