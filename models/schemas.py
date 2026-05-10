"""Structured schemas for every pipeline output.

The project uses Pydantic when installed. A tiny fallback is included so the
mock demo can still run in restricted teaching sandboxes before dependencies
are installed; normal project execution should use the packages in
requirements.txt.
"""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover - only for restricted sandboxes
    class BaseModel:  # type: ignore[override]
        def __init__(self, **data: Any) -> None:
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self) -> Dict[str, Any]:
            return dict(self.__dict__)

        def model_dump_json(self, indent: int = 2) -> str:
            import json

            return json.dumps(self.model_dump(), indent=indent, ensure_ascii=False)

    def Field(default: Any = None, description: str = "", ge: float | None = None, le: float | None = None, default_factory: Any = None) -> Any:
        if default_factory is not None:
            return default_factory()
        return default


class ArticleSummary(BaseModel):
    summary: str = Field(description="Concise summary of the article's main message.")
    main_points: List[str] = Field(default_factory=list, description="Important article points, claims, or developments.")
    topic_overview: str = Field(description="Short overview of the broad issue area.")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence that the summary preserves the article's main content.")
    reasoning_summary: str = Field(description="Brief explanation of summarization choices.")


class EntityExtraction(BaseModel):
    people: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    events: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    extraction_notes: str = Field(default="")


class BiasAnalysis(BaseModel):
    sentiment: str = Field(description="Overall sentiment: negative, neutral, mixed, or positive.")
    bias_score: float = Field(ge=0.0, le=10.0, description="0 means minimal bias indicators; 10 means strong bias indicators.")
    political_leaning: str = Field(description="Observed leaning or 'not clearly partisan' if unsupported.")
    social_bias_indicators: List[str] = Field(default_factory=list)
    emotionally_loaded_terms: List[str] = Field(default_factory=list)
    tone_analysis: str = Field(description="Analysis of tone and stance.")
    sensationalism_score: float = Field(ge=0.0, le=10.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str = Field(description="Evidence-based explanation of the bias assessment.")


class FramingAnalysis(BaseModel):
    headline_style: str = Field(description="Headline or lead style, e.g. neutral, analytical, sensational.")
    emotional_intensity: float = Field(ge=0.0, le=10.0)
    persuasive_techniques: List[str] = Field(default_factory=list)
    language_patterns: List[str] = Field(default_factory=list)
    framing_style: str = Field(description="How the article frames the issue.")
    tone_style: str = Field(description="Dominant tone style.")
    tone_consistency: str = Field(description="Whether tone remains consistent across the article.")
    target_audience_tone: str = Field(description="Likely audience addressed by the tone.")
    emotionally_charged_phrases: List[str] = Field(default_factory=list)
    reader_impact: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning_summary: str = Field(description="Explanation of framing and rhetoric findings.")


class SourceReliabilityHeuristics(BaseModel):
    transparency_score: float = Field(ge=0.0, le=10.0)
    evidence_density_score: float = Field(ge=0.0, le=10.0)
    attribution_quality: str
    reliability_indicators: List[str] = Field(default_factory=list)
    caution_flags: List[str] = Field(default_factory=list)


class FinalReport(BaseModel):
    title: str
    overall_assessment: str
    credibility_indicator_score: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=1.0)
    key_findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    pipeline_reasoning_summary: str
    markdown_report: str


class PipelineState(BaseModel):
    article: str
    summary: ArticleSummary | None = None
    entities: EntityExtraction | None = None
    bias_analysis: BiasAnalysis | None = None
    framing_analysis: FramingAnalysis | None = None
    source_reliability: SourceReliabilityHeuristics | None = None
    final_report: FinalReport | None = None
