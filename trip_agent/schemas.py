"""Lightweight validation utilities for the assignment agent."""

from __future__ import annotations

from datetime import date
from typing import Any


class AgentInputError(ValueError):
    """Raised when the user request is too incomplete for the chain to continue."""


REQUIRED_PARSE_KEYS = {
    "destination",
    "start_date",
    "end_date",
    "trip_length_days",
    "travelers",
    "budget",
    "pace",
    "interests",
    "constraints",
    "missing_information",
    "confidence",
}


def require_keys(name: str, payload: dict[str, Any], required: set[str]) -> None:
    missing = sorted(required.difference(payload))
    if missing:
        raise AgentInputError(f"{name} is missing required keys: {', '.join(missing)}")


def validate_parsed_request(parsed: dict[str, Any]) -> dict[str, Any]:
    require_keys("parsed_request", parsed, REQUIRED_PARSE_KEYS)
    if not parsed.get("destination"):
        raise AgentInputError(
            "The request does not contain a destination. Please include a city or region and rerun the agent."
        )

    for list_key in ("interests", "constraints", "missing_information"):
        if parsed.get(list_key) is None:
            parsed[list_key] = []
        if not isinstance(parsed[list_key], list):
            parsed[list_key] = [str(parsed[list_key])]

    for date_key in ("start_date", "end_date"):
        value = parsed.get(date_key)
        if value:
            try:
                date.fromisoformat(value)
            except ValueError as exc:
                raise AgentInputError(f"{date_key} must be ISO YYYY-MM-DD, got {value!r}") from exc

    return parsed
