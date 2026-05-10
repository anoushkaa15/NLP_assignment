# Academic Report: Multi-Step NLP Pipeline for News Credibility Analysis

## Problem Statement

This project analyzes news articles for credibility indicators, rhetorical framing, bias signals, and likely audience impact. It is intentionally not designed as a definitive truth-verification system. A single prompt could produce a quick opinion about an article, but it would hide the intermediate reasoning and make it difficult to explain which parts of the article influenced the output. A multi-step pipeline is better for this assignment because each stage has a narrow role: summarizing the article, extracting entities with a tool, analyzing bias, analyzing framing, and then synthesizing a report.

## Chain Design

Step 1 uses a Gemini-powered LangChain chain to summarize the raw article into a structured Pydantic object. This reduces noise and gives later stages a concise representation of the article. Step 2 uses spaCy NER as a non-LLM tool. It extracts people, organizations, locations, events, and keywords so later LLM steps can discuss language around specific actors and topics. Step 3 receives the summary and entity map and produces sentiment, bias indicators, loaded terms, tone analysis, and a sensationalism score. Step 4 depends on the previous stages and focuses on rhetoric rather than factual truth. It analyzes persuasive techniques, framing style, emotional intensity, tone consistency, target audience, and possible reader impact. Step 5 receives the complete shared state and generates both a structured JSON report and a Markdown report.

## Tool Integration

The tool step is spaCy Named Entity Recognition. I used spaCy because entity extraction is a standard NLP task that does not require an LLM, and using a deterministic tool makes the pipeline more explainable. The tool output enters the shared state as `state["entities"]`, and the bias and framing chains explicitly use that object in their prompts. The code also includes a fallback extractor so a demo can still run in a restricted environment, but the intended setup uses `en_core_web_sm`.

## Limitations

The system does not prove whether an article is true or false. It only analyzes credibility indicators and rhetorical signals. spaCy can miss entities, especially local names or unusual organizations. LLM judgments about bias and framing are interpretive, so a human reviewer should treat the output as an analytical aid rather than a final judgment. The source reliability heuristics are simple text-based cues and cannot replace full source auditing. Gemini rate limits can also interrupt live demos, so the code includes retry logic and a mock mode.

## Reflection

If I had more time, I would compare multiple articles about the same event to show framing differences across outlets. I would also add citation extraction, URL metadata analysis, and a small Streamlit interface for screenshots. The main lesson from building the project is that chaining is useful because it forces the system to expose intermediate artifacts. When the final report seems wrong, I can inspect whether the problem began in summarization, entity extraction, bias analysis, or framing analysis.
