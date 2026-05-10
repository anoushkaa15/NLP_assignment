"""Fake News Verification Agent.

A complete multi-step LLM agent for the programming assignment. The pipeline is
explicitly chained through a shared dictionary state:

1. LLM claim extraction
2. DuckDuckGo web evidence retrieval tool
3. LLM evidence analysis
4. LLM credibility scoring
5. LLM final Markdown report
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.web_search import mock_evidence, retrieve_evidence
from utils.gemini_client import GeminiClient, GeminiClientError, MockGeminiClient
from utils.state_manager import create_initial_state, print_step_debug, record_step, save_report_markdown, save_state_json

PROMPT_DIR = Path("prompts")


class AgentInputError(ValueError):
    """Raised when the user input is too vague to fact-check."""


def load_dotenv_if_available() -> None:
    """Load .env variables for real Gemini runs.

    python-dotenv is listed in requirements.txt. It is imported here so mock
    classroom runs can still execute in restricted environments before packages
    are installed.
    """

    from dotenv import load_dotenv

    load_dotenv()


def load_prompt(name: str) -> tuple[str, str]:
    """Load a prompt file and split it into system/user templates."""

    text = (PROMPT_DIR / name).read_text(encoding="utf-8")
    if "USER:" not in text:
        raise ValueError(f"Prompt {name} must contain SYSTEM: and USER: sections.")
    system_part, user_part = text.split("USER:", 1)
    system_prompt = system_part.replace("SYSTEM:", "", 1).strip()
    user_prompt = user_part.strip()
    return system_prompt, user_prompt


def step_extract_claims(state: dict[str, Any], llm: Any, debug: bool = True) -> dict[str, Any]:
    """STEP 1: Read raw user input and write structured claims to state."""

    system_prompt, user_template = load_prompt("claim_extraction.txt")
    inputs = {"user_input": state["user_input"]}
    user_prompt = user_template.replace("{user_input}", state["user_input"])
    claims = llm.complete_json(system_prompt, user_prompt)
    validate_claims(claims)
    state["claims"] = claims
    outputs = {"claims": claims}
    record_step(state, "STEP 1 - CLAIM EXTRACTION (LLM)", inputs, outputs)
    if debug:
        print_step_debug("STEP 1 - CLAIM EXTRACTION (LLM)", outputs)
    return state


def step_retrieve_evidence(state: dict[str, Any], use_mock_search: bool = False, debug: bool = True) -> dict[str, Any]:
    """STEP 2: Use extracted claims/entities to retrieve web evidence."""

    inputs = {"claims": state["claims"]}
    if use_mock_search:
        evidence, quality = mock_evidence()
    else:
        evidence, quality = retrieve_evidence(state["claims"], max_results=5)
    state["evidence"] = evidence
    state["evidence_quality"] = quality
    if quality.get("errors"):
        state["errors"].extend(quality["errors"])
    outputs = {"evidence": evidence, "evidence_quality": quality}
    record_step(state, "STEP 2 - WEB EVIDENCE RETRIEVAL (TOOL)", inputs, outputs)
    if debug:
        print_step_debug("STEP 2 - WEB EVIDENCE RETRIEVAL (TOOL)", outputs)
    return state


def step_analyze_evidence(state: dict[str, Any], llm: Any, debug: bool = True) -> dict[str, Any]:
    """STEP 3: Compare retrieved evidence against the extracted claims."""

    system_prompt, user_template = load_prompt("evidence_analysis.txt")
    inputs = {"claims": state["claims"], "evidence": state["evidence"]}
    user_prompt = (
        user_template
        .replace("{claims}", json.dumps(state["claims"], indent=2, ensure_ascii=False))
        .replace("{evidence}", json.dumps(state["evidence"], indent=2, ensure_ascii=False))
    )
    analysis = llm.complete_json(system_prompt, user_prompt)
    state["analysis"] = analysis
    outputs = {"analysis": analysis}
    record_step(state, "STEP 3 - EVIDENCE ANALYSIS (LLM)", inputs, outputs)
    if debug:
        print_step_debug("STEP 3 - EVIDENCE ANALYSIS (LLM)", outputs)
    return state


def step_score_credibility(state: dict[str, Any], llm: Any, debug: bool = True) -> dict[str, Any]:
    """STEP 4: Score credibility using analysis and evidence quality."""

    system_prompt, user_template = load_prompt("credibility_scoring.txt")
    inputs = {"analysis": state["analysis"], "evidence_quality": state["evidence_quality"]}
    user_prompt = (
        user_template
        .replace("{claims}", json.dumps(state["claims"], indent=2, ensure_ascii=False))
        .replace("{evidence_quality}", json.dumps(state["evidence_quality"], indent=2, ensure_ascii=False))
        .replace("{analysis}", json.dumps(state["analysis"], indent=2, ensure_ascii=False))
    )
    credibility = llm.complete_json(system_prompt, user_prompt)
    state["credibility"] = credibility
    outputs = {"credibility": credibility}
    record_step(state, "STEP 4 - CREDIBILITY SCORING (LLM)", inputs, outputs)
    if debug:
        print_step_debug("STEP 4 - CREDIBILITY SCORING (LLM)", outputs)
    return state


def step_generate_final_report(state: dict[str, Any], llm: Any, debug: bool = True) -> dict[str, Any]:
    """STEP 5: Generate a professional Markdown report from all prior state."""

    system_prompt, user_template = load_prompt("final_report.txt")
    inputs = {
        "user_input": state["user_input"],
        "claims": state["claims"],
        "evidence": state["evidence"],
        "analysis": state["analysis"],
        "credibility": state["credibility"],
        "evidence_quality": state["evidence_quality"],
    }
    user_prompt = user_template.replace("{state}", json.dumps(inputs, indent=2, ensure_ascii=False))
    final_report = llm.complete_text(system_prompt, user_prompt)
    state["final_report"] = final_report
    outputs = {"final_report": final_report}
    record_step(state, "STEP 5 - FINAL FACT-CHECK REPORT (LLM)", inputs, outputs)
    if debug:
        print("\n===== STEP 5 - FINAL FACT-CHECK REPORT (LLM) =====")
        print(final_report[:4000])
    return state


def run_agent(
    user_input: str,
    *,
    mock_llm: bool = False,
    mock_search: bool = False,
    output_md: str = "outputs/final_report.md",
    output_json: str = "outputs/final_report.json",
    debug: bool = True,
) -> dict[str, Any]:
    """Run the complete chained agent and return the final shared state."""

    if not mock_llm:
        load_dotenv_if_available()
    llm = MockGeminiClient() if mock_llm else GeminiClient()
    state = create_initial_state(user_input)

    state = step_extract_claims(state, llm, debug=debug)
    state = step_retrieve_evidence(state, use_mock_search=mock_search, debug=debug)
    state = step_analyze_evidence(state, llm, debug=debug)
    state = step_score_credibility(state, llm, debug=debug)
    state = step_generate_final_report(state, llm, debug=debug)

    save_report_markdown(state["final_report"], output_md)
    save_state_json(state, output_json)
    if debug:
        print(f"\nSaved Markdown report to {output_md}")
        print(f"Saved JSON state to {output_json}")
    return state


def validate_claims(claims: dict[str, Any]) -> None:
    required = {"main_claim", "sub_claims", "entities", "topics", "claim_type"}
    missing = required.difference(claims)
    if missing:
        raise AgentInputError(f"Claim extraction failed. Missing keys: {sorted(missing)}")
    if not claims.get("main_claim"):
        raise AgentInputError("No checkable factual claim was found. Please provide a clearer news claim or article excerpt.")
    for key in ("sub_claims", "entities", "topics"):
        if not isinstance(claims.get(key), list):
            raise AgentInputError(f"Claim extraction field {key!r} must be a list.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Fake News Verification Agent.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--claim", help="News headline, article excerpt, or claim to verify.")
    group.add_argument("--input-file", help="Path to a text file containing the claim/article.")
    parser.add_argument("--output-md", default="outputs/final_report.md", help="Markdown report output path.")
    parser.add_argument("--output-json", default="outputs/final_report.json", help="Full state JSON output path.")
    parser.add_argument("--mock-llm", action="store_true", help="Use deterministic mock LLM responses for local smoke tests.")
    parser.add_argument("--mock-search", action="store_true", help="Use deterministic mock evidence instead of live DuckDuckGo retrieval.")
    parser.add_argument("--quiet", action="store_true", help="Do not print intermediate step outputs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    user_input = args.claim if args.claim else Path(args.input_file).read_text(encoding="utf-8")
    try:
        run_agent(
            user_input,
            mock_llm=args.mock_llm,
            mock_search=args.mock_search,
            output_md=args.output_md,
            output_json=args.output_json,
            debug=not args.quiet,
        )
    except (AgentInputError, GeminiClientError, OSError, ValueError, ImportError) as exc:
        print(f"Agent failed: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
