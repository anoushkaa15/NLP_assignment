"""Step 3: bias and sentiment LLM chain."""

from __future__ import annotations

from models.schemas import BiasAnalysis
from prompts.prompt_templates import BIAS_PROMPT
from utils.helpers import model_to_dict
from utils import logger


def run_bias_detection(state: dict, llm_client) -> dict:
    """Analyze bias indicators using summary + entity tool outputs.

    Chaining value: this stage depends on the article summary and extracted
    entities, so it can discuss tone around specific actors and topics instead
    of reading the raw article in isolation.
    """

    logger.info("Detecting bias and sentiment indicators...")
    variables = {
        "summary": model_to_dict(state["summary"]),
        "entities": model_to_dict(state["entities"]),
        "source_reliability": model_to_dict(state["source_reliability"]),
    }
    bias_analysis = llm_client.invoke_structured(BIAS_PROMPT, BiasAnalysis, variables)
    state["bias_analysis"] = bias_analysis
    logger.success("Bias and sentiment analysis complete.")
    logger.print_json_preview("Bias analysis output", bias_analysis)
    return state
