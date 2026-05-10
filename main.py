"""Multi-Step NLP Pipeline for News Credibility Analysis.

This project is intentionally positioned as news/rhetoric analysis, not as a
article truth-labeling system or definitive verification system. The goal is to
show sequential LLM chaining, a spaCy tool step, shared state, and structured
outputs in a way that is easy to demo and explain.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from chains.bias_detector import run_bias_detection
from chains.framing_analyzer import run_framing_analysis
from chains.report_generator import run_report_generation
from chains.summarizer import run_summarization
from tools.entity_extractor import extract_entities
from utils.helpers import compute_source_reliability_heuristics, save_outputs
from utils.llm import GeminiLLMClient, MockLLMClient
from utils import logger


def create_initial_state(article: str) -> dict[str, Any]:
    """Create the shared dictionary required by the assignment."""

    return {
        "article": article,
        "summary": None,
        "entities": None,
        "bias_analysis": None,
        "framing_analysis": None,
        "source_reliability": None,
        "final_report": None,
    }


def run_entity_extraction(state: dict[str, Any]) -> dict[str, Any]:
    """Step 2: run the spaCy NER tool and store structured entities.

    This is deliberately not an LLM call. It gives later LLM steps a grounded
    list of actors, organizations, locations, events, and topics from the text.
    """

    logger.info("Extracting entities with spaCy NER tool...")
    summary_points = state["summary"].main_points if state.get("summary") else []
    state["entities"] = extract_entities(state["article"], summary_points)
    logger.success("Entity extraction complete.")
    logger.print_json_preview("Entity extraction output", state["entities"])
    return state


def run_pipeline(article: str, *, mock: bool = False, output_dir: str = "outputs") -> dict[str, Any]:
    """Run all five dependent stages in order.

    Every stage reads from and writes to the same state dictionary. Removing any
    stage weakens or breaks the dependency chain: bias analysis needs summary
    and entities; framing needs bias; final reporting needs the complete state.
    """

    if not article or len(article.split()) < 30:
        raise ValueError("Please provide a news article with at least 30 words so the pipeline has enough context.")

    llm_client = MockLLMClient() if mock else GeminiLLMClient()
    state = create_initial_state(article)

    state = run_summarization(state, llm_client)
    state = run_entity_extraction(state)

    logger.info("Computing source reliability heuristics...")
    state["source_reliability"] = compute_source_reliability_heuristics(state["article"])
    logger.success("Source reliability heuristics complete.")
    logger.print_json_preview("Source reliability heuristics", state["source_reliability"])

    state = run_bias_detection(state, llm_client)
    state = run_framing_analysis(state, llm_client)
    state = run_report_generation(state, llm_client)

    save_outputs(state, output_dir=output_dir)
    logger.success(f"Saved outputs to {output_dir}/report.json and {output_dir}/report.md")
    return state


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Multi-Step NLP Pipeline for News Credibility Analysis.")
    parser.add_argument("--article-file", default="sample_article.txt", help="Path to a text file containing a news article.")
    parser.add_argument("--output-dir", default="outputs", help="Directory for report.json and report.md.")
    parser.add_argument("--mock", action="store_true", help="Run with deterministic mock LLM outputs for demos without an API key.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        article = Path(args.article_file).read_text(encoding="utf-8")
        run_pipeline(article, mock=args.mock, output_dir=args.output_dir)
    except Exception as exc:
        logger.error(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
