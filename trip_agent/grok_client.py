"""Small Grok API client used by the assignment agent.

The project intentionally avoids LangChain, LlamaIndex, and other agent frameworks so
that every LLM call and state transition remains visible for the demo.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping

from .http_utils import HTTPRequestError, post_json


class GrokAPIError(RuntimeError):
    """Raised when the Grok API cannot return a usable response."""


@dataclass
class GrokClient:
    """OpenAI-compatible chat completions client for xAI/Grok."""

    api_key: str | None = None
    model: str = "grok-3-mini"
    base_url: str = "https://api.x.ai/v1"
    timeout_seconds: int = 60

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        self.model = os.getenv("GROK_MODEL", self.model)
        self.base_url = os.getenv("XAI_BASE_URL", self.base_url).rstrip("/")
        if not self.api_key:
            raise GrokAPIError(
                "Missing Grok API key. Set XAI_API_KEY or GROK_API_KEY, "
                "or run with --mock-llm for a local smoke test."
            )

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        content = self._complete(system_prompt, user_prompt, response_format={"type": "json_object"})
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise GrokAPIError(f"Grok returned non-JSON content: {content[:500]}") from exc

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        return self._complete(system_prompt, user_prompt, response_format=None)

    def _complete(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Mapping[str, str] | None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        if response_format:
            payload["response_format"] = response_format

        try:
            data = post_json(
                f"{self.base_url}/chat/completions",
                payload=payload,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                timeout_seconds=self.timeout_seconds,
            )
        except HTTPRequestError as exc:
            raise GrokAPIError(f"Grok API request failed: {exc}") from exc
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GrokAPIError(f"Unexpected Grok API response shape: {data}") from exc


class MockGrokClient:
    """Deterministic local client for testing chain mechanics without an API key."""

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if "STEP_ID: parse_request" in system_prompt:
            if "plan something fun" in user_prompt.lower():
                return {
                    "destination": None,
                    "start_date": None,
                    "end_date": None,
                    "trip_length_days": None,
                    "travelers": None,
                    "budget": None,
                    "pace": None,
                    "interests": ["fun"],
                    "constraints": [],
                    "missing_information": ["destination", "dates", "traveler profile"],
                    "confidence": "low",
                }
            return {
                "destination": "Kyoto, Japan",
                "start_date": "2026-06-12",
                "end_date": "2026-06-15",
                "trip_length_days": 4,
                "travelers": "two adults / partners",
                "budget": "medium",
                "pace": "relaxed",
                "interests": ["food", "temples", "quiet walks", "photography"],
                "constraints": ["avoid nightlife-heavy plans", "include rainy-day backup ideas"],
                "missing_information": [],
                "confidence": "high",
            }
        if "STEP_ID: analyze_conditions" in system_prompt:
            return {
                "planning_assumptions": ["June in Kyoto can be humid and rainy."],
                "weather_risks": ["Rain may affect outdoor photography walks."],
                "weather_opportunities": ["Cloudy weather can improve temple photography lighting."],
                "packing_advice": ["compact umbrella", "breathable layers", "comfortable walking shoes"],
                "daily_strategy": [
                    {"day": 1, "strategy": "Keep arrival day light and near the hotel."},
                    {"day": 2, "strategy": "Schedule major outdoor temples early."},
                    {"day": 3, "strategy": "Pair walks with covered markets."},
                    {"day": 4, "strategy": "Leave flexible time for weather changes."},
                ],
                "uncertainties": ["Mock weather is not a live forecast."],
            }
        if "STEP_ID: draft_itinerary" in system_prompt:
            return {
                "title": "Relaxed Kyoto Food, Temple, and Photography Plan",
                "days": [
                    {
                        "day": 1,
                        "theme": "Arrival and gentle orientation",
                        "morning": "Arrive and settle in.",
                        "afternoon": "Walk through Nishiki Market for snacks and photos.",
                        "evening": "Quiet dinner in Gion or Pontocho before crowds peak.",
                        "rain_backup": "Kyoto International Manga Museum or a covered shopping arcade.",
                    },
                    {
                        "day": 2,
                        "theme": "Eastern temples",
                        "morning": "Kiyomizu-dera early for views and photos.",
                        "afternoon": "Sannenzaka, Ninenzaka, and Kodai-ji at a slow pace.",
                        "evening": "Tea house or relaxed kaiseki-style dinner.",
                        "rain_backup": "Tea ceremony class.",
                    },
                    {
                        "day": 3,
                        "theme": "Quiet walks and food",
                        "morning": "Philosopher's Path and Honen-in.",
                        "afternoon": "Covered market tasting route.",
                        "evening": "Early ramen or izakaya dinner without nightlife focus.",
                        "rain_backup": "Cooking class.",
                    },
                    {
                        "day": 4,
                        "theme": "Flexible final morning",
                        "morning": "Fushimi Inari early if weather allows.",
                        "afternoon": "Pack, cafe, and depart.",
                        "evening": "Departure buffer.",
                        "rain_backup": "Kyoto Station architecture photography.",
                    },
                ],
            }
        if "STEP_ID: critique_itinerary" in system_prompt:
            return {
                "overall_score": 8,
                "strengths": ["Matches relaxed pace", "Includes rainy-day backups"],
                "issues": ["Add clearer weather caveat", "Mention booking constraints for classes"],
                "required_revisions": ["Add a contingency section", "State that live availability must be checked"],
            }
        return {"message": "mock json fallback"}

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        return """# Weather-Aware Kyoto Trip Briefing\n\n## Executive summary\nThis relaxed four-day plan prioritizes temples, food, quiet walks, and photography while keeping rain backups available each day.\n\n## Day-by-day plan\n- **Day 1:** Arrive, settle in, and explore Nishiki Market. Rain backup: covered arcade or museum.\n- **Day 2:** Visit Kiyomizu-dera early, then Sannenzaka, Ninenzaka, and Kodai-ji. Rain backup: tea ceremony.\n- **Day 3:** Walk the Philosopher's Path and pair it with food stops. Rain backup: cooking class.\n- **Day 4:** Try Fushimi Inari early if weather allows, then keep a departure buffer. Rain backup: Kyoto Station photography.\n\n## Weather and packing\nPack a compact umbrella, breathable layers, and comfortable shoes. Treat weather-dependent activities as flexible until a live forecast is checked.\n\n## Limitations\nThis mock output demonstrates formatting and chain flow only; use a real Grok API key for final evaluation.\n"""
