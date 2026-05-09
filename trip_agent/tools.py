"""External tool calls for weather and geocoding data.

Open-Meteo is used because it has a free public API and does not require a
separate key during classroom demos.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from .http_utils import HTTPRequestError, get_json


OPEN_METEO_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


def fetch_weather_for_trip(parsed_request: dict[str, Any], timeout_seconds: int = 20) -> dict[str, Any]:
    """Return structured weather data for the parsed trip request.

    The function never raises for ordinary network/API failures. It returns a
    status field so the next LLM step can reason honestly about missing data.
    """

    destination = parsed_request.get("destination")
    start_date = parsed_request.get("start_date")
    end_date = parsed_request.get("end_date") or start_date
    if not destination:
        return {"status": "unavailable", "reason": "No destination supplied by parsed request."}

    try:
        geo = _geocode(destination, timeout_seconds)
        if not geo:
            return {"status": "unavailable", "reason": f"Open-Meteo found no geocode result for {destination}."}

        if start_date and end_date:
            weather = _weather_by_dates(geo, start_date, end_date, timeout_seconds)
        else:
            weather = {
                "status": "location_only",
                "reason": "No exact dates were supplied, so forecast data was not requested.",
                "daily": [],
            }

        weather.update(
            {
                "destination_query": destination,
                "resolved_location": geo,
                "source": "Open-Meteo geocoding and weather APIs",
            }
        )
        return weather
    except HTTPRequestError as exc:
        return {"status": "unavailable", "reason": f"Weather tool request failed: {exc}"}
    except (KeyError, TypeError, ValueError) as exc:
        return {"status": "unavailable", "reason": f"Weather tool response could not be parsed: {exc}"}


def _geocode(destination: str, timeout_seconds: int) -> dict[str, Any] | None:
    data = get_json(
        OPEN_METEO_GEOCODE,
        params={"name": destination, "count": 1, "language": "en", "format": "json"},
        timeout_seconds=timeout_seconds,
    )
    results = data.get("results") or []
    if not results:
        return None
    first = results[0]
    return {
        "name": first.get("name"),
        "country": first.get("country"),
        "admin1": first.get("admin1"),
        "latitude": first["latitude"],
        "longitude": first["longitude"],
        "timezone": first.get("timezone"),
    }


def _weather_by_dates(geo: dict[str, Any], start_date: str, end_date: str, timeout_seconds: int) -> dict[str, Any]:
    today = date.today()
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    if start >= today:
        endpoint = OPEN_METEO_FORECAST
        params = _base_weather_params(geo, start_date, end_date)
        status = "forecast"
    else:
        endpoint = OPEN_METEO_ARCHIVE
        params = _base_weather_params(geo, start_date, end_date)
        status = "historical"

    data = get_json(endpoint, params=params, timeout_seconds=timeout_seconds)
    daily = data.get("daily", {})
    rows = []
    for index, day in enumerate(daily.get("time", [])):
        rows.append(
            {
                "date": day,
                "temperature_max_c": _at(daily, "temperature_2m_max", index),
                "temperature_min_c": _at(daily, "temperature_2m_min", index),
                "precipitation_sum_mm": _at(daily, "precipitation_sum", index),
                "precipitation_probability_max_pct": _at(daily, "precipitation_probability_max", index),
                "wind_speed_max_kmh": _at(daily, "wind_speed_10m_max", index),
            }
        )

    return {
        "status": status,
        "requested_start_date": start_date,
        "requested_end_date": end_date,
        "retrieved_at_utc": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "daily": rows,
    }


def _base_weather_params(geo: dict[str, Any], start_date: str, end_date: str) -> dict[str, Any]:
    return {
        "latitude": geo["latitude"],
        "longitude": geo["longitude"],
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(
            [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "precipitation_probability_max",
                "wind_speed_10m_max",
            ]
        ),
        "timezone": "auto",
    }


def _at(mapping: dict[str, list[Any]], key: str, index: int) -> Any:
    values = mapping.get(key) or []
    return values[index] if index < len(values) else None
