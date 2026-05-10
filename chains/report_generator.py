"""Step 5: final report generation LLM chain."""

from __future__ import annotations

from models.schemas import FinalReport
from prompts.prompt_templates import REPORT_PROMPT
from utils.helpers import state_to_jsonable
from utils import logger


def run_report_generation(state: dict, llm_client) -> dict:
    """Generate final JSON + Markdown report from the complete shared state.

    Chaining value: the final report synthesizes every previous artifact rather
    than asking a single prompt to analyze raw text all at once.
    """

    logger.info("Generating report...")
    variables = {"state": state_to_jsonable(state)}
    final_report = llm_client.invoke_structured(REPORT_PROMPT, FinalReport, variables)
    state["final_report"] = final_report
    logger.success("Final report generated.")
    logger.print_json_preview("Final report metadata", {
        "title": final_report.title,
        "credibility_indicator_score": final_report.credibility_indicator_score,
        "confidence": final_report.confidence,
    })
    return state
