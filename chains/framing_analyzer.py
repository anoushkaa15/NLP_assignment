"""Step 4: rhetoric, framing, and reader-impact LLM chain."""

from __future__ import annotations

from models.schemas import FramingAnalysis
from prompts.prompt_templates import FRAMING_PROMPT
from utils.helpers import article_excerpt, model_to_dict
from utils import logger


def run_framing_analysis(state: dict, llm_client) -> dict:
    """Analyze framing after summary, entity, and bias stages have completed.

    This stage intentionally avoids factual verification. It exists to show a
    dependent reasoning step focused on rhetoric, persuasive language, and
    likely audience perception.
    """

    logger.info("Running framing analysis...")
    variables = {
        "summary": model_to_dict(state["summary"]),
        "entities": model_to_dict(state["entities"]),
        "bias_analysis": model_to_dict(state["bias_analysis"]),
        "article_excerpt": article_excerpt(state["article"]),
    }
    framing_analysis = llm_client.invoke_structured(FRAMING_PROMPT, FramingAnalysis, variables)
    state["framing_analysis"] = framing_analysis
    logger.success("Framing analysis complete.")
    logger.print_json_preview("Framing analysis output", framing_analysis)
    return state
