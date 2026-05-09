"""DuckDuckGo evidence retrieval tool.

This module is intentionally a tool call, not an LLM call. It retrieves current
external evidence that the model should not invent from memory.
"""

from __future__ import annotations

import re
from html import unescape
from typing import Any
from urllib.parse import quote_plus, urlparse


def retrieve_evidence(claims: dict[str, Any], max_results: int = 5, timeout: int = 15) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Retrieve at least five evidence items when possible.

    Returns (evidence_items, quality_metadata). The function handles empty
    results, API/network failure, timeouts, and malformed responses by returning
    partial evidence plus metadata instead of crashing the chain.
    """

    queries = build_queries(claims)
    evidence: list[dict[str, str]] = []
    errors: list[str] = []

    for query in queries:
        if len(evidence) >= max_results:
            break
        try:
            items = search_duckduckgo_html(query, timeout=timeout)
            evidence.extend(_deduplicate(evidence + items)[:max_results])
            evidence = _deduplicate(evidence)[:max_results]
        except TimeoutError as exc:
            errors.append(f"Timeout for query {query!r}: {exc}")
        except ValueError as exc:
            errors.append(f"Malformed response for query {query!r}: {exc}")
        except Exception as exc:
            errors.append(f"Search failure for query {query!r}: {exc}")

    quality = {
        "requested_results": max_results,
        "retrieved_results": len(evidence),
        "queries": queries,
        "status": "ok" if len(evidence) >= max_results else "partial" if evidence else "empty",
        "errors": errors,
    }
    if not evidence and not errors:
        quality["errors"] = ["DuckDuckGo returned no usable results."]
    return evidence, quality


def build_queries(claims: dict[str, Any]) -> list[str]:
    main_claim = claims.get("main_claim") or ""
    entities = " ".join((claims.get("entities") or [])[:4])
    topics = " ".join((claims.get("topics") or [])[:2])
    queries = [
        f"{main_claim} fact check",
        f"{entities} {topics} verification",
        main_claim,
    ]
    return [query.strip() for query in queries if query.strip()]


def search_duckduckgo_html(query: str, timeout: int) -> list[dict[str, str]]:
    import requests

    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 fact-check-agent"}, timeout=timeout)
    response.raise_for_status()
    html = response.text
    if "result__a" not in html and "result__snippet" not in html:
        raise ValueError("DuckDuckGo response did not contain recognizable result blocks.")
    return parse_duckduckgo_html(html)


def parse_duckduckgo_html(html: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    blocks = re.split(r'<div class="result results_links', html)
    for block in blocks[1:]:
        title_match = re.search(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL)
        snippet_match = re.search(r'class="result__snippet"[^>]*>(.*?)</a>|class="result__snippet"[^>]*>(.*?)</div>', block, re.DOTALL)
        if not title_match:
            continue
        url = unescape(title_match.group(1))
        title = _clean_html(title_match.group(2))
        snippet_html = (snippet_match.group(1) or snippet_match.group(2)) if snippet_match else ""
        snippet = _clean_html(snippet_html)
        source = urlparse(url).netloc.replace("www.", "") or "DuckDuckGo result"
        items.append({"title": title, "snippet": snippet, "url": url, "source": source})
    return items


def _clean_html(value: str) -> str:
    no_tags = re.sub(r"<.*?>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(no_tags)).strip()


def _deduplicate(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for item in items:
        key = item.get("url") or item.get("title")
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def mock_evidence() -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Deterministic evidence for classroom smoke tests without network access."""

    evidence = [
        {
            "title": "NASA did not warn of six days of darkness",
            "snippet": "Fact-checkers report that viral posts about six days of darkness are a recurring hoax and not a NASA announcement.",
            "url": "https://example.com/fact-check-nasa-darkness",
            "source": "Example Fact Check",
        },
        {
            "title": "Solar storms do not cause global multi-day darkness",
            "snippet": "Space weather can disrupt communications and power systems, but it does not block sunlight worldwide for days.",
            "url": "https://example.com/space-weather-explainer",
            "source": "Example Science Desk",
        },
        {
            "title": "NASA official updates show no global darkness announcement",
            "snippet": "Recent NASA updates discuss solar activity but contain no warning about total darkness on Earth.",
            "url": "https://example.com/nasa-updates",
            "source": "Example NASA Monitor",
        },
        {
            "title": "Old viral darkness claim returns on social media",
            "snippet": "The same claim has circulated in previous years with changing dates and no supporting evidence.",
            "url": "https://example.com/viral-hoax-history",
            "source": "Example News",
        },
        {
            "title": "How to verify viral space claims",
            "snippet": "Experts recommend checking official agency releases and multiple reputable science outlets before sharing viral claims.",
            "url": "https://example.com/verify-space-claims",
            "source": "Example Media Literacy",
        },
    ]
    quality = {"requested_results": 5, "retrieved_results": 5, "queries": ["mock query"], "status": "ok", "errors": []}
    return evidence, quality
