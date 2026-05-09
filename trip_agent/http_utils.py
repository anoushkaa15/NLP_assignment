"""Tiny JSON HTTP helpers built on the Python standard library."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class HTTPRequestError(RuntimeError):
    """Raised when a JSON HTTP request fails."""


def get_json(url: str, params: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
    query = urlencode({key: value for key, value in params.items() if value is not None})
    full_url = f"{url}?{query}" if query else url
    request = Request(full_url, headers={"Accept": "application/json"})
    return _open_json(request, timeout_seconds)


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout_seconds: int) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, headers=headers, method="POST")
    return _open_json(request, timeout_seconds)


def _open_json(request: Request, timeout_seconds: int) -> dict[str, Any]:
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            text = response.read().decode("utf-8")
            return json.loads(text)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise HTTPRequestError(f"HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPRequestError(str(exc)) from exc
