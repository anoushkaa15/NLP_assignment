"""Gemini + LangChain LLM helpers with retry handling."""

from __future__ import annotations

import os
import time
from typing import Any, Type

from models.schemas import ArticleSummary, BiasAnalysis, FinalReport, FramingAnalysis
from utils import logger


class GeminiLLMClient:
    """Wrapper that uses LangChain's ChatGoogleGenerativeAI with structured output."""

    def __init__(self, model_name: str | None = None, temperature: float = 0.1, max_retries: int = 3) -> None:
        try:
            from dotenv import load_dotenv
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:  # pragma: no cover - depends on installed requirements
            raise RuntimeError(
                "Missing runtime dependencies. Run `pip install -r requirements.txt` before using the real Gemini client."
            ) from exc

        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GEMINI_API_KEY or GOOGLE_API_KEY. Copy .env.example to .env and add your key.")

        self.max_retries = max_retries
        self.llm = ChatGoogleGenerativeAI(
            model=model_name or os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            google_api_key=api_key,
            temperature=temperature,
            max_retries=0,  # custom retry below makes 429 behavior easier to explain in demos
        )

    def invoke_structured(self, prompt: Any, schema: Type[Any], variables: dict[str, Any]) -> Any:
        structured_llm = self.llm.with_structured_output(schema)
        chain = prompt | structured_llm
        for attempt in range(1, self.max_retries + 1):
            try:
                return chain.invoke(variables)
            except Exception as exc:  # LangChain/Google exceptions vary by version
                message = str(exc).lower()
                is_rate_limit = "429" in message or "rate" in message or "quota" in message or "resource exhausted" in message
                if is_rate_limit and attempt < self.max_retries:
                    delay = 2**attempt
                    logger.warning(f"Gemini rate limit detected. Retrying in {delay}s (attempt {attempt}/{self.max_retries})...")
                    time.sleep(delay)
                    continue
                raise


class MockLLMClient:
    """Deterministic offline LLM for smoke tests and classroom demos."""

    def invoke_structured(self, prompt: Any, schema: Type[Any], variables: dict[str, Any]) -> Any:
        if schema is ArticleSummary:
            return ArticleSummary(
                summary="City officials announced a climate resilience plan after flooding damaged several neighborhoods.",
                main_points=[
                    "The plan expands drainage systems and restores wetlands.",
                    "Emergency cooling centers are planned before next summer.",
                    "Supporters frame the plan as public-safety investment, while critics question funding detail.",
                    "The article cites residents and a municipal budget summary.",
                ],
                topic_overview="Local climate adaptation, infrastructure planning, flood response, and public spending.",
                confidence=0.91,
                reasoning_summary="The summary preserves the article's policy proposal, competing reactions, and cited evidence without judging factual truth.",
            )
        if schema is BiasAnalysis:
            return BiasAnalysis(
                sentiment="mixed",
                bias_score=3.4,
                political_leaning="not clearly partisan",
                social_bias_indicators=["contrasts supporters and critics", "emphasizes public safety and funding concerns"],
                emotionally_loaded_terms=["frustrated", "rushed", "damaged"],
                tone_analysis="Mostly informational with mild urgency around flood damage and resident frustration.",
                sensationalism_score=2.8,
                confidence=0.86,
                explanation="The article includes both supportive and critical perspectives and uses limited emotionally loaded wording.",
            )
        if schema is FramingAnalysis:
            return FramingAnalysis(
                headline_style="Policy-focused and moderately urgent",
                emotional_intensity=4.1,
                persuasive_techniques=["problem-solution framing", "appeal to public safety", "balanced contrast"],
                language_patterns=["institutional announcement framing", "resident-impact language", "cost and timeline details"],
                framing_style="The article frames climate resilience as a practical governance and infrastructure issue.",
                tone_style="analytical with mild emotional emphasis",
                tone_consistency="generally consistent, moving from announcement to reactions and budget context",
                target_audience_tone="civic-minded local readers",
                emotionally_charged_phrases=["heavy flooding damaged", "frustrated by repeated flood warnings", "rushed"],
                reader_impact=["may increase concern about infrastructure preparedness", "may encourage attention to budget accountability"],
                confidence=0.84,
                reasoning_summary="The rhetoric relies more on policy framing than sensational claims, while still highlighting resident frustration.",
            )
        if schema is FinalReport:
            return FinalReport(
                title="News Credibility Indicator Analysis: Climate Resilience Plan Article",
                overall_assessment="The article shows moderate credibility indicators and relatively balanced framing, with mild emotional emphasis around flood impacts and funding uncertainty.",
                credibility_indicator_score=78.0,
                confidence=0.82,
                key_findings=[
                    "The article summarizes a local policy proposal and includes multiple perspectives.",
                    "Named institutions, resident reactions, and budget details improve evidence density.",
                    "Bias and sensationalism indicators are present but not dominant.",
                    "Framing emphasizes public safety, infrastructure, and accountability rather than definitive blame.",
                ],
                recommendations=[
                    "Check the full municipal budget document for funding details.",
                    "Compare coverage from additional local outlets for framing differences.",
                    "Look for follow-up reporting on implementation timelines and community response.",
                ],
                limitations=[
                    "This pipeline analyzes rhetoric and credibility indicators, not factual truth.",
                    "The spaCy entity stage may miss local names or classify entities imperfectly.",
                    "LLM judgments about tone and bias are interpretive and should be reviewed by a human.",
                ],
                pipeline_reasoning_summary="The system summarized the article, extracted entities with a tool, analyzed bias indicators from the summary and entities, then used those results for rhetoric and framing analysis before synthesizing a final report.",
                markdown_report="# News Credibility Indicator Analysis\n\n## Overall Assessment\nThe article shows moderate credibility indicators and relatively balanced framing. It is not treated as true or false; the pipeline evaluates language, attribution, rhetoric, and reader-impact signals.\n\n## Key Findings\n- The story includes policy details, resident reactions, and a budget figure.\n- Bias indicators are mild and mostly connected to urgency around flood damage.\n- Framing centers on public safety, infrastructure, and accountability.\n\n## Recommendations\n- Compare with additional local reporting.\n- Check the municipal budget source directly.\n- Track follow-up coverage on implementation.\n\n## Limitations\nThis is a credibility-indicator and rhetoric analysis, not a definitive verification system.\n",
            )
        raise ValueError(f"MockLLMClient does not know how to produce schema {schema}")
