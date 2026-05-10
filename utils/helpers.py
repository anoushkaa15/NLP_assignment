"""Helper functions for state serialization and output files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from models.schemas import SourceReliabilityHeuristics


def model_to_dict(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return {key: model_to_dict(item) for key, item in value.items()}
    if isinstance(value, list):
        return [model_to_dict(item) for item in value]
    return value


def state_to_jsonable(state: dict[str, Any]) -> dict[str, Any]:
    return {key: model_to_dict(value) for key, value in state.items()}


def save_outputs(state: dict[str, Any], output_dir: str = "outputs") -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    json_state = state_to_jsonable(state)
    (output_path / "report.json").write_text(json.dumps(json_state, indent=2, ensure_ascii=False), encoding="utf-8")
    final_report = state.get("final_report")
    markdown = getattr(final_report, "markdown_report", None) if final_report else None
    if not markdown:
        markdown = "# News Credibility Analysis Report\n\nNo final report was generated."
    (output_path / "report.md").write_text(markdown, encoding="utf-8")


def article_excerpt(article: str, max_chars: int = 2500) -> str:
    article = re.sub(r"\s+", " ", article).strip()
    return article[:max_chars]


def compute_source_reliability_heuristics(article: str) -> SourceReliabilityHeuristics:
    """Compute simple non-LLM source reliability indicators from article text.

    This does not verify factual truth. It gives the final report transparent
    cues about attribution, sourcing density, and caution flags.
    """

    lowered = article.lower()
    reliability_indicators: list[str] = []
    caution_flags: list[str] = []

    quote_count = article.count('"') + article.count("“") + article.count("”")
    has_numbers = bool(re.search(r"\b\d+(?:\.\d+)?\b", article))
    has_attribution = any(term in lowered for term in ["said", "according to", "reported", "cited", "statement", "data"])
    has_named_source = any(term in lowered for term in ["official", "agency", "university", "ministry", "department", "report"])
    loaded_markers = ["shocking", "disaster", "traitor", "destroy", "panic", "outrage", "secret", "exposed"]
    found_loaded = [term for term in loaded_markers if term in lowered]

    if quote_count >= 2:
        reliability_indicators.append("includes direct quotations")
    if has_numbers:
        reliability_indicators.append("includes quantitative details")
    if has_attribution:
        reliability_indicators.append("uses attribution language")
    if has_named_source:
        reliability_indicators.append("mentions institutional or official sources")
    if not has_attribution:
        caution_flags.append("limited visible attribution")
    if found_loaded:
        caution_flags.append("contains potentially loaded terms: " + ", ".join(found_loaded))
    if len(article.split()) < 120:
        caution_flags.append("article is short, so analysis has limited context")

    transparency_score = min(10.0, 2.0 + 2.0 * quote_count + (2.0 if has_attribution else 0.0) + (2.0 if has_named_source else 0.0))
    evidence_density_score = min(10.0, 2.0 + (2.5 if has_numbers else 0.0) + (2.5 if has_attribution else 0.0) + (1.5 if quote_count else 0.0))
    attribution_quality = "moderate" if has_attribution else "low"
    if has_attribution and has_named_source and quote_count >= 2:
        attribution_quality = "strong"

    return SourceReliabilityHeuristics(
        transparency_score=round(transparency_score, 1),
        evidence_density_score=round(evidence_density_score, 1),
        attribution_quality=attribution_quality,
        reliability_indicators=reliability_indicators,
        caution_flags=caution_flags,
    )
