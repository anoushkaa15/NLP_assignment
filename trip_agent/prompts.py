"""Prompt templates for every LLM step in the trip briefing chain."""

from __future__ import annotations

import json
from typing import Any


def as_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


PARSE_SYSTEM = """STEP_ID: parse_request
You are a travel-request parser. Return only valid JSON. Extract the user's trip request into fields that downstream tools can use. Do not invent missing dates or destinations. If information is absent, put null or an empty list and describe it in missing_information.
Required JSON keys: destination, start_date, end_date, trip_length_days, travelers, budget, pace, interests, constraints, missing_information, confidence.
Dates must be ISO YYYY-MM-DD when present. confidence must be low, medium, or high."""


def parse_user(raw_request: str) -> str:
    return f"""Parse this travel request into the required JSON schema.

RAW_REQUEST:
{raw_request}
"""


ANALYZE_SYSTEM = """STEP_ID: analyze_conditions
You are a practical travel risk analyst. Return only valid JSON. Use the parsed request and tool weather data to identify planning assumptions, weather risks, weather opportunities, packing advice, daily strategy, and uncertainties. If weather.status is unavailable, explicitly mark weather-specific advice as uncertain instead of fabricating weather facts.
Required JSON keys: planning_assumptions, weather_risks, weather_opportunities, packing_advice, daily_strategy, uncertainties."""


def analyze_user(parsed_request: dict[str, Any], weather: dict[str, Any]) -> str:
    return f"""Use Step 1 and Step 2 outputs to produce weather-aware planning analysis.

STEP_1_PARSED_REQUEST:
{as_json(parsed_request)}

STEP_2_TOOL_WEATHER:
{as_json(weather)}
"""


DRAFT_SYSTEM = """STEP_ID: draft_itinerary
You are a travel itinerary drafter. Return only valid JSON. Create a realistic day-by-day itinerary that obeys the parsed user constraints and uses the condition analysis. Keep the pace consistent with the parsed pace field. Every day must include a rain_backup.
Required JSON keys: title, days. Each item in days must include day, theme, morning, afternoon, evening, rain_backup."""


def draft_user(parsed_request: dict[str, Any], condition_analysis: dict[str, Any]) -> str:
    return f"""Draft an itinerary from the previous structured outputs.

STEP_1_PARSED_REQUEST:
{as_json(parsed_request)}

STEP_3_CONDITION_ANALYSIS:
{as_json(condition_analysis)}
"""


CRITIQUE_SYSTEM = """STEP_ID: critique_itinerary
You are a strict itinerary reviewer. Return only valid JSON. Compare the draft against the original parsed request and weather analysis. Identify mismatches, unsupported claims, missing backups, and places where the final answer should warn the user.
Required JSON keys: overall_score, strengths, issues, required_revisions. overall_score must be an integer from 1 to 10."""


def critique_user(parsed_request: dict[str, Any], condition_analysis: dict[str, Any], draft: dict[str, Any]) -> str:
    return f"""Critique Step 4 using the earlier chain outputs. Do not rewrite the itinerary; produce revision instructions.

STEP_1_PARSED_REQUEST:
{as_json(parsed_request)}

STEP_3_CONDITION_ANALYSIS:
{as_json(condition_analysis)}

STEP_4_DRAFT_ITINERARY:
{as_json(draft)}
"""


FINAL_SYSTEM = """STEP_ID: final_report
You are a travel briefing editor. Produce a polished Markdown report, not JSON. The report must be structured with headings and be directly useful to the traveler. Use the critique to revise the draft. Include: executive summary, planning assumptions, day-by-day itinerary, weather/packing notes, contingency plan, and limitations. Do not claim bookings, opening hours, or live conditions unless present in the state."""


def final_user(state: dict[str, Any]) -> str:
    return f"""Create the final Markdown report from the accumulated chain state. The final report must use Step 5's critique to improve Step 4's draft.

ACCUMULATED_STATE:
{as_json(state)}
"""
