"""Step 1: article summarization LLM chain."""

from __future__ import annotations

from models.schemas import ArticleSummary
from prompts.prompt_templates import SUMMARY_PROMPT
from utils import logger


def run_summarization(state: dict, llm_client) -> dict:
    """Summarize the raw article and store structured output in shared state.

    Chaining value: the summary compresses long article text before later stages
    reason about sentiment, bias indicators, and framing.
    """

    logger.info("Running summarization...")
    summary = llm_client.invoke_structured(SUMMARY_PROMPT, ArticleSummary, {"article": state["article"]})
    state["summary"] = summary
    logger.success("Summarization complete.")
    logger.print_json_preview("Summary output", summary)
    return state
