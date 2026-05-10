"""Gemini API client for the Fake News Verification Agent.

The client calls Google's Gemini REST API directly. No LangChain, LlamaIndex,
or agent framework is used, so each LLM call remains visible in the pipeline
code.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any


class GeminiClientError(RuntimeError):
    """Raised when Gemini cannot produce a usable response."""


@dataclass
class GeminiClient:
    """Small wrapper around the Gemini generateContent API."""

    api_key: str | None = None
    model: str = "gemini-2.0-flash"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    timeout: int = 60

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", self.model)
        self.base_url = os.getenv("GEMINI_BASE_URL", self.base_url).rstrip("/")
        if not self.api_key:
            raise GeminiClientError(
                "Missing Gemini API key. Set GEMINI_API_KEY or GOOGLE_API_KEY in your environment or .env file."
            )

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Call Gemini and parse a JSON object response."""

        text = self._complete(system_prompt, user_prompt, response_mime_type="application/json")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise GeminiClientError(f"Expected JSON from Gemini, received: {text[:500]}") from exc

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini and return plain text, used for the final Markdown report."""

        return self._complete(system_prompt, user_prompt, response_mime_type="text/plain")

    def _complete(self, system_prompt: str, user_prompt: str, response_mime_type: str) -> str:
        import requests

        payload: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": response_mime_type,
            },
        }
        url = f"{self.base_url}/models/{self.model}:generateContent"

        try:
            response = requests.post(url, params={"key": self.api_key}, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.Timeout as exc:
            raise GeminiClientError("Gemini API request timed out.") from exc
        except requests.RequestException as exc:
            raise GeminiClientError(f"Gemini API request failed: {exc}") from exc

        data = response.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(part.get("text", "") for part in parts).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise GeminiClientError(f"Unexpected Gemini response shape: {data}") from exc


class MockGeminiClient:
    """Deterministic LLM replacement for demos when no API key is available."""

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        lowered_system = system_prompt.lower()
        if "credibility scorer" in lowered_system:
            return {
                "credibility_score": 12,
                "confidence_level": "medium",
                "misinformation_risk": "high",
                "justification": [
                    "The central claim is contradicted by retrieved fact-checking evidence.",
                    "Search results do not show a NASA announcement supporting the claim.",
                    "Confidence is medium because mock evidence is snippet-level rather than full article text.",
                ],
            }
        if "evidence analyst" in lowered_system:
            return {
                "supported_claims": [],
                "contradicted_claims": [
                    "NASA announced Earth will experience six days of total darkness next month because of a solar storm."
                ],
                "uncertain_claims": ["Whether a specific viral post used altered NASA branding is not verifiable from snippets alone."],
                "reasoning": [
                    "Retrieved fact-check and science-source snippets describe the six-days-of-darkness claim as a recurring hoax.",
                    "No evidence item reports an actual NASA announcement matching the claim.",
                ],
            }
        if "fact-checking claim extraction assistant" in lowered_system:
            if len(user_prompt.strip()) < 30 or "asdf" in user_prompt.lower():
                return {
                    "main_claim": "",
                    "sub_claims": [],
                    "entities": [],
                    "topics": ["unclear"],
                    "claim_type": "unclear",
                }
            return {
                "main_claim": "NASA announced Earth will experience six days of total darkness next month because of a solar storm.",
                "sub_claims": [
                    "NASA announced an upcoming six-day period of total darkness on Earth.",
                    "A solar storm will cause global darkness next month.",
                ],
                "entities": ["NASA", "Earth", "solar storm"],
                "topics": ["science", "space", "misinformation"],
                "claim_type": "social media claim",
            }
        return {}

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        return """# Fake News Verification Report

## 1. Original Claim
Viral posts claim that NASA announced Earth will experience six days of total darkness next month because of a solar storm.

## 2. Extracted Factual Claims
- NASA allegedly announced a six-day global darkness event.
- A solar storm allegedly will cause this event next month.

## 3. Evidence Summary
The retrieved evidence does not support the alleged NASA announcement. The available snippets describe similar claims as recurring misinformation or hoaxes.

## 4. Supported vs. Contradicted Points
- **Supported:** None of the main factual claims were supported by retrieved evidence.
- **Contradicted:** The central claim is contradicted by fact-check style evidence and lack of corroborating NASA reporting.
- **Uncertain:** Snippet-level search cannot verify every version of the viral post.

## 5. Credibility Score
**12 / 100**

## 6. Confidence Level
**Medium**

## 7. Final Verdict
The claim is very likely false. Based on the retrieved evidence, it resembles a known misinformation pattern rather than a real NASA announcement.

## 8. Limitations of Verification
This result depends on search snippets and available sources. A stronger version would fetch and analyze full article text and check NASA's official website directly.
"""
