"""Reusable LangChain prompt templates.

When LangChain is installed, these are real ChatPromptTemplate objects. A small
fallback class keeps the mock demo runnable in restricted environments.
"""

from __future__ import annotations

from typing import Any, Iterable, Tuple

try:
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:  # pragma: no cover - used only before dependencies are installed
    class ChatPromptTemplate:  # type: ignore[override]
        def __init__(self, messages: Iterable[Tuple[str, str]]) -> None:
            self.messages = list(messages)

        @classmethod
        def from_messages(cls, messages: Iterable[Tuple[str, str]]) -> "ChatPromptTemplate":
            return cls(messages)

        def __or__(self, other: Any) -> Any:
            return _FallbackChain(self, other)

        def format_messages(self, **kwargs: Any) -> list[dict[str, str]]:
            return [{"role": role, "content": template.format(**kwargs)} for role, template in self.messages]

    class _FallbackChain:
        def __init__(self, prompt: ChatPromptTemplate, model: Any) -> None:
            self.prompt = prompt
            self.model = model

        def invoke(self, variables: dict[str, Any]) -> Any:
            return self.model.invoke({"messages": self.prompt.format_messages(**variables), "variables": variables})


SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an academic news-analysis assistant. Summarize the article without deciding whether it is true or false. Focus on what the article says, which issues it raises, and what readers need to understand before later bias and framing analysis. Return output that matches the ArticleSummary schema.""",
        ),
        (
            "human",
            """Analyze the article below for Step 1 of a sequential NLP pipeline.

ARTICLE:
{article}

Return a concise summary, 3-6 main points, a topic overview, a confidence value from 0 to 1, and a short reasoning_summary explaining what you preserved.""",
        ),
    ]
)

BIAS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You analyze bias and sentiment indicators in news writing. Do not perform factual verification and do not call the article fake or true. Identify tone, sentiment, emotionally loaded wording, social or political bias indicators, and sensationalism. Return output that matches the BiasAnalysis schema.""",
        ),
        (
            "human",
            """Step 3 depends on Step 1 and Step 2. Use the summary and entities to analyze bias indicators.

SUMMARY_JSON:
{summary}

ENTITY_JSON:
{entities}

SOURCE_RELIABILITY_HEURISTICS:
{source_reliability}

Return sentiment, bias_score, political_leaning, social_bias_indicators, emotionally_loaded_terms, tone_analysis, sensationalism_score, confidence, and explanation.""",
        ),
    ]
)

FRAMING_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a rhetoric and framing analyst. Study how language choices may influence reader perception emotionally, socially, or politically. This is not truth verification. Focus only on framing, rhetoric, persuasive techniques, tone, emotional intensity, and likely audience impact. Return output that matches the FramingAnalysis schema.""",
        ),
        (
            "human",
            """Step 4 depends on the previous summary, entity extraction, and bias analysis.

SUMMARY_JSON:
{summary}

ENTITY_JSON:
{entities}

BIAS_ANALYSIS_JSON:
{bias_analysis}

ARTICLE_EXCERPT:
{article_excerpt}

Return headline_style, emotional_intensity, persuasive_techniques, language_patterns, framing_style, tone_style, tone_consistency, target_audience_tone, emotionally_charged_phrases, reader_impact, confidence, and reasoning_summary.""",
        ),
    ]
)

REPORT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You generate academic news credibility-indicator reports. Do not label articles as true or false and do not make definitive truth classifications. Synthesize the pipeline state into a structured JSON report and a polished Markdown report. Return output that matches the FinalReport schema.""",
        ),
        (
            "human",
            """Step 5 receives the complete shared state from the multi-step pipeline.

PIPELINE_STATE_JSON:
{state}

Generate a final report with: title, overall_assessment, credibility_indicator_score from 0 to 100, confidence from 0 to 1, key_findings, recommendations, limitations, pipeline_reasoning_summary, and markdown_report. The markdown report should contain clear headings and be suitable for a university submission screenshot.""",
        ),
    ]
)
