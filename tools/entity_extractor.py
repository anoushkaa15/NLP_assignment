"""spaCy named-entity extraction tool.

This is the mandatory non-LLM tool stage. It turns the article text into a
structured entity map that later LLM stages use for bias and framing analysis.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

from models.schemas import EntityExtraction
from utils import logger


_SPACY_MODEL = None


def load_spacy_model() -> object | None:
    global _SPACY_MODEL
    if _SPACY_MODEL is not None:
        return _SPACY_MODEL
    try:
        import spacy

        try:
            _SPACY_MODEL = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model en_core_web_sm is not installed. Falling back to regex-based extraction for this run.")
            _SPACY_MODEL = None
    except ImportError:
        logger.warning("spaCy is not installed. Falling back to regex-based extraction for this run.")
        _SPACY_MODEL = None
    return _SPACY_MODEL


def extract_entities(article: str, summary_points: Iterable[str] | None = None) -> EntityExtraction:
    """Extract people, organizations, locations, events, and topics.

    The tool uses spaCy NER when available. A conservative fallback keeps demos
    runnable but records that extraction quality is reduced.
    """

    nlp = load_spacy_model()
    if nlp is None:
        return _fallback_extract_entities(article, summary_points)

    doc = nlp(article)
    people: set[str] = set()
    organizations: set[str] = set()
    locations: set[str] = set()
    events: set[str] = set()

    for ent in doc.ents:
        text = ent.text.strip()
        if not text or len(text) < 2:
            continue
        if ent.label_ == "PERSON":
            people.add(text)
        elif ent.label_ in {"ORG", "GPE_ORG"}:
            organizations.add(text)
        elif ent.label_ in {"GPE", "LOC", "FAC"}:
            locations.add(text)
        elif ent.label_ in {"EVENT", "WORK_OF_ART", "LAW"}:
            events.add(text)

    topics = _extract_topics(article, summary_points)
    return EntityExtraction(
        people=sorted(people),
        organizations=sorted(organizations),
        locations=sorted(locations),
        events=sorted(events),
        topics=topics,
        extraction_notes="Entities extracted with spaCy en_core_web_sm NER plus keyword frequency topics.",
    )


def _fallback_extract_entities(article: str, summary_points: Iterable[str] | None) -> EntityExtraction:
    title_case_phrases = re.findall(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b", article)
    organizations = [phrase for phrase in title_case_phrases if any(word in phrase.lower() for word in ["city", "department", "agency", "council", "ministry", "university"])]
    locations = [phrase for phrase in title_case_phrases if any(word in phrase.lower() for word in ["city", "neighborhood", "river", "county"])]
    topics = _extract_topics(article, summary_points)
    return EntityExtraction(
        people=[],
        organizations=sorted(set(organizations)),
        locations=sorted(set(locations)),
        events=[],
        topics=topics,
        extraction_notes="Fallback regex extraction used because spaCy or en_core_web_sm was unavailable.",
    )


def _extract_topics(article: str, summary_points: Iterable[str] | None) -> list[str]:
    stopwords = {
        "the", "and", "that", "with", "from", "this", "were", "will", "have", "about", "after", "said",
        "into", "their", "they", "while", "also", "over", "under", "before", "article", "officials",
    }
    text = article + " " + " ".join(summary_points or [])
    words = [word.lower() for word in re.findall(r"\b[a-zA-Z]{4,}\b", text)]
    counts = Counter(word for word in words if word not in stopwords)
    return [word for word, _ in counts.most_common(8)]
