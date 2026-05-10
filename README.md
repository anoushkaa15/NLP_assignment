# Multi-Step NLP Pipeline for News Credibility Analysis

A professional academic project for analyzing news articles through **summarization**, **entity extraction**, **bias detection**, **framing analysis**, and **credibility indicator reporting**.

This project does **not** label articles as true or false and does **not** make definitive truth classifications. It is a multi-step NLP/LLM system for studying how a news article communicates information, which entities it foregrounds, what tone it uses, and what credibility indicators or caution flags appear in the writing.

## Project Overview

The system accepts a raw news article and processes it through five dependent stages:

1. **Article Summarization (LLM)** — compresses long-form article text into a structured summary.
2. **Entity Extraction (spaCy Tool)** — extracts people, organizations, locations, events, and topics.
3. **Bias & Sentiment Analysis (LLM)** — analyzes sentiment, bias indicators, loaded language, and sensationalism.
4. **Framing & Language Analysis (LLM)** — studies rhetoric, framing, persuasive techniques, and likely reader impact.
5. **Final Report Generation (LLM)** — synthesizes all prior outputs into Markdown and JSON reports.

## Architecture Diagram

```text
Raw Article
     ↓
Summarizer LLM
     ↓
spaCy Entity Tool
     ↓
Bias Analysis LLM
     ↓
Framing & Language Analysis LLM
     ↓
Final Report Generator
     ↓
outputs/report.json + outputs/report.md
```

## Folder Structure

```text
project_root/
│
├── main.py
├── requirements.txt
├── .env.example
├── README.md
├── sample_article.txt
│
├── chains/
│   ├── summarizer.py
│   ├── bias_detector.py
│   ├── framing_analyzer.py
│   └── report_generator.py
│
├── tools/
│   └── entity_extractor.py
│
├── prompts/
│   └── prompt_templates.py
│
├── models/
│   └── schemas.py
│
├── utils/
│   ├── llm.py
│   ├── helpers.py
│   └── logger.py
│
└── outputs/
    ├── report.json
    └── report.md
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Gemini API Setup

Copy the example environment file and add your key:

```bash
cp .env.example .env
```

`.env`:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
```

The code also accepts `GOOGLE_API_KEY` if that is how your environment stores Gemini credentials.

## Execution Steps

Run with Gemini:

```bash
python main.py --article-file sample_article.txt
```

Run a deterministic no-key demo:

```bash
python main.py --article-file sample_article.txt --mock
```

Outputs are written automatically to:

```text
outputs/report.json
outputs/report.md
```

## Sample Console Output

```text
▶ Running summarization...
✓ Summarization complete.
▶ Extracting entities with spaCy NER tool...
✓ Entity extraction complete.
▶ Detecting bias and sentiment indicators...
✓ Bias and sentiment analysis complete.
▶ Running framing analysis...
✓ Framing analysis complete.
▶ Generating report...
✓ Final report generated.
✓ Saved outputs to outputs/report.json and outputs/report.md
```

## Sample Output

```json
{
  "overall_assessment": "The article shows moderate credibility indicators and relatively balanced framing...",
  "credibility_indicator_score": 78.0,
  "confidence": 0.82,
  "key_findings": [
    "The article includes policy details and multiple perspectives.",
    "Bias indicators are present but not dominant."
  ]
}
```

## Why Multi-Step Pipelines Outperform Single Prompts

A single prompt can produce a polished answer, but it hides intermediate reasoning and makes failures difficult to inspect. This project uses multiple stages because:

1. **Summarization reduces noise** and compresses long-form articles into a manageable representation.
2. **Entity extraction identifies important actors, organizations, locations, events, and topics** with a tool rather than relying only on LLM interpretation.
3. **Bias analysis depends on both summary and extracted entities**, allowing the system to discuss tone around specific actors and topics.
4. **Framing analysis depends on previous sentiment and bias outputs**, so rhetoric and reader-impact analysis is grounded in earlier findings.
5. **Final report generation synthesizes all prior analyses** into a structured assessment instead of starting from raw text again.

## Screenshots Placeholders

Add screenshots after running the project:

```text
docs/screenshots/console_run.png
docs/screenshots/report_markdown.png
docs/screenshots/report_json.png
```

## Limitations

- This system analyzes credibility indicators, rhetoric, framing, and audience impact; it does not verify truth.
- spaCy NER may miss domain-specific entities or misclassify names.
- LLM bias and framing judgments are interpretive and should be reviewed by a human.
- Source reliability heuristics are simple text signals, not a substitute for full source auditing.
- Gemini rate limits may require retries or shorter inputs.

## Future Improvements

- Add a web interface for live demos.
- Add source metadata extraction from article URLs.
- Compare multiple articles about the same event for framing differences.
- Add human annotation mode for classroom evaluation.
- Add automated tests with fixed mock outputs.
