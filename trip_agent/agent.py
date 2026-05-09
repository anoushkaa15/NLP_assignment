"""Explicit multi-step chain for the weather-aware trip briefing agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from . import prompts
from .grok_client import GrokClient, MockGrokClient
from .schemas import validate_parsed_request
from .tools import fetch_weather_for_trip


class LLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]: ...

    def complete_text(self, system_prompt: str, user_prompt: str) -> str: ...


def run_agent(
    raw_request: str,
    *,
    llm: LLMClient | None = None,
    mock_llm: bool = False,
    trace: bool = False,
    output_path: str | Path = "outputs/trip_brief.md",
    state_output_path: str | Path = "outputs/state.json",
) -> dict[str, Any]:
    """Run the full chain and return the accumulated shared state."""

    client: LLMClient = llm or (MockGrokClient() if mock_llm else GrokClient())
    state: dict[str, Any] = {"raw_request": raw_request, "steps": []}

    step_parse_request(state, client, trace=trace)
    step_fetch_weather(state, trace=trace)
    step_analyze_conditions(state, client, trace=trace)
    step_draft_itinerary(state, client, trace=trace)
    step_critique_itinerary(state, client, trace=trace)
    step_finalize_report(state, client, trace=trace)
    write_outputs(state, output_path=output_path, state_output_path=state_output_path, trace=trace)
    return state


def step_parse_request(state: dict[str, Any], llm: LLMClient, *, trace: bool = False) -> None:
    step_name = "1_parse_request"
    received = {"raw_request": state["raw_request"]}
    parsed = llm.complete_json(prompts.PARSE_SYSTEM, prompts.parse_user(state["raw_request"]))
    state["parsed_request"] = validate_parsed_request(parsed)
    _record_step(state, step_name, received, {"parsed_request": state["parsed_request"]}, trace)


def step_fetch_weather(state: dict[str, Any], *, trace: bool = False) -> None:
    step_name = "2_fetch_weather_tool"
    received = {"parsed_request": state["parsed_request"]}
    weather = fetch_weather_for_trip(state["parsed_request"])
    state["weather"] = weather
    _record_step(state, step_name, received, {"weather": weather}, trace)


def step_analyze_conditions(state: dict[str, Any], llm: LLMClient, *, trace: bool = False) -> None:
    step_name = "3_analyze_conditions"
    received = {"parsed_request": state["parsed_request"], "weather": state["weather"]}
    analysis = llm.complete_json(
        prompts.ANALYZE_SYSTEM,
        prompts.analyze_user(state["parsed_request"], state["weather"]),
    )
    state["condition_analysis"] = analysis
    _record_step(state, step_name, received, {"condition_analysis": analysis}, trace)


def step_draft_itinerary(state: dict[str, Any], llm: LLMClient, *, trace: bool = False) -> None:
    step_name = "4_draft_itinerary"
    received = {"parsed_request": state["parsed_request"], "condition_analysis": state["condition_analysis"]}
    draft = llm.complete_json(
        prompts.DRAFT_SYSTEM,
        prompts.draft_user(state["parsed_request"], state["condition_analysis"]),
    )
    state["draft_itinerary"] = draft
    _record_step(state, step_name, received, {"draft_itinerary": draft}, trace)


def step_critique_itinerary(state: dict[str, Any], llm: LLMClient, *, trace: bool = False) -> None:
    step_name = "5_critique_itinerary"
    received = {
        "parsed_request": state["parsed_request"],
        "condition_analysis": state["condition_analysis"],
        "draft_itinerary": state["draft_itinerary"],
    }
    critique = llm.complete_json(
        prompts.CRITIQUE_SYSTEM,
        prompts.critique_user(state["parsed_request"], state["condition_analysis"], state["draft_itinerary"]),
    )
    state["critique"] = critique
    _record_step(state, step_name, received, {"critique": critique}, trace)


def step_finalize_report(state: dict[str, Any], llm: LLMClient, *, trace: bool = False) -> None:
    step_name = "6_finalize_report"
    received = {
        "parsed_request": state["parsed_request"],
        "weather": state["weather"],
        "condition_analysis": state["condition_analysis"],
        "draft_itinerary": state["draft_itinerary"],
        "critique": state["critique"],
    }
    final_report = llm.complete_text(prompts.FINAL_SYSTEM, prompts.final_user(received))
    state["final_report_markdown"] = final_report
    _record_step(state, step_name, received, {"final_report_markdown": final_report}, trace)


def write_outputs(
    state: dict[str, Any], *, output_path: str | Path, state_output_path: str | Path, trace: bool = False
) -> None:
    output_path = Path(output_path)
    state_output_path = Path(state_output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    state_output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(state["final_report_markdown"], encoding="utf-8")
    state_output_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    if trace:
        print(f"Wrote final report to {output_path}")
        print(f"Wrote accumulated state to {state_output_path}")


def _record_step(
    state: dict[str, Any], step_name: str, received: dict[str, Any], returned: dict[str, Any], trace: bool
) -> None:
    record = {
        "step": step_name,
        "received_keys": sorted(received.keys()),
        "returned_keys": sorted(returned.keys()),
        "received": received,
        "returned": returned,
    }
    state["steps"].append(record)
    if trace:
        print(f"\n[{step_name}]")
        print(f"received_keys={record['received_keys']}")
        print(f"returned_keys={record['returned_keys']}")
        print(json.dumps(returned, ensure_ascii=False, indent=2)[:2500])
