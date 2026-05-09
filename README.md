# Fake News Verification Agent

A submission-ready **Multi-Step LLM Agent** programming assignment project using the **Grok API** in Python. The agent accepts a news headline, article excerpt, or viral claim and verifies its credibility through a visible, multi-stage reasoning pipeline.

This is **not** a single-prompt chatbot. Each stage reads from and writes to a shared dictionary state object, and later stages explicitly depend on structured outputs from earlier stages.

## Project Overview

The agent performs a small fact-checking workflow:

1. Extract factual claims from the user text.
2. Retrieve external evidence with DuckDuckGo search.
3. Analyze whether the evidence supports, contradicts, or fails to verify the claims.
4. Score the credibility of the claim.
5. Produce a structured Markdown fact-check report and a JSON state file.

The goal is not to replace professional fact-checkers. The goal is to demonstrate applied NLP engineering: decomposition, retrieval augmentation, state management, prompt design, error handling, and synthesis.

## Architecture

```text
project/
│
├── main.py
├── requirements.txt
├── README.md
├── REPORT.md
├── prompts/
│   ├── claim_extraction.txt
│   ├── evidence_analysis.txt
│   ├── credibility_scoring.txt
│   └── final_report.txt
│
├── tools/
│   └── web_search.py
│
├── outputs/
│   ├── final_report.md
│   └── final_report.json
│
├── examples/
│   └── sample_claim.txt
│
└── utils/
    ├── grok_client.py
    └── state_manager.py
```

No LangChain, LlamaIndex, or agent framework is used. The chain is written directly in Python so it is easy to explain during a viva or live demo.

## Chain Explanation

The shared state starts as:

```python
state = {
    "user_input": "",
    "claims": {},
    "evidence": [],
    "evidence_quality": {},
    "analysis": {},
    "credibility": {},
    "final_report": "",
    "errors": [],
    "trace": []
}
```

### Step 1 — Claim Extraction (LLM)

**Input:** raw user news text from `state["user_input"]`.

**Output:** JSON stored in `state["claims"]`:

```json
{
  "main_claim": "",
  "sub_claims": [],
  "entities": [],
  "topics": [],
  "claim_type": ""
}
```

This step separates factual claims from opinions and identifies entities that Step 2 uses for search queries.

### Step 2 — Web Evidence Retrieval (Tool Call)

**Input:** `state["claims"]` from Step 1.

**Tool:** DuckDuckGo HTML search through `tools/web_search.py` using `requests`.

**Output:** evidence list in `state["evidence"]` and quality metadata in `state["evidence_quality"]`:

```json
[
  {
    "title": "",
    "snippet": "",
    "url": "",
    "source": ""
  }
]
```

The tool attempts to gather at least five evidence items. If search fails, times out, returns no results, or returns malformed HTML, the program records the problem and continues with partial or empty evidence.

### Step 3 — Evidence Analysis (LLM)

**Input:** `state["claims"]` and `state["evidence"]`.

**Output:** JSON stored in `state["analysis"]`:

```json
{
  "supported_claims": [],
  "contradicted_claims": [],
  "uncertain_claims": [],
  "reasoning": []
}
```

The LLM is instructed to use only retrieved evidence, not its memory.

### Step 4 — Credibility Scoring (LLM)

**Input:** `state["analysis"]` and `state["evidence_quality"]`.

**Output:** JSON stored in `state["credibility"]`:

```json
{
  "credibility_score": 0,
  "confidence_level": "",
  "misinformation_risk": "",
  "justification": []
}
```

This step converts evidence analysis into a practical score while considering retrieval quality.

### Step 5 — Final Fact-Check Report (LLM)

**Input:** all previous state fields.

**Output:** Markdown saved to `outputs/final_report.md` and full state JSON saved to `outputs/final_report.json`.

The report contains:

1. Original claim
2. Extracted factual claims
3. Evidence summary
4. Supported vs. contradicted points
5. Credibility score
6. Confidence level
7. Final verdict
8. Limitations of verification

## Setup Instructions

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## API Setup

Create a `.env` file in the project root:

```bash
XAI_API_KEY=your_grok_api_key_here
GROK_MODEL=grok-3-mini
```

The code also accepts `GROK_API_KEY` instead of `XAI_API_KEY`.

## Run Instructions

Run with a direct claim:

```bash
python main.py --claim "Viral posts claim that NASA announced Earth will experience six days of total darkness next month because of a solar storm."
```

Run with a file:

```bash
python main.py --input-file examples/sample_claim.txt
```

Run a no-key smoke test with deterministic local outputs:

```bash
python main.py --input-file examples/sample_claim.txt --mock-llm --mock-search
```

Run a malformed input demo:

```bash
python main.py --claim "asdf" --mock-llm --mock-search
```

Expected behavior: the program exits gracefully and explains that no checkable factual claim was found.

## Example Input

```text
Viral posts claim that NASA announced Earth will experience six days of total darkness next month because of a solar storm.
```

## Example Output Summary

```text
Credibility Score: 12 / 100
Confidence Level: Medium
Final Verdict: The claim is very likely false because retrieved evidence does not show a NASA announcement and describes similar claims as recurring hoaxes.
```

The actual output is a full Markdown report plus a JSON file containing the whole state and trace.

## Sample Execution Log

```text
===== STEP 1 - CLAIM EXTRACTION (LLM) =====
{
  "claims": {
    "main_claim": "NASA announced Earth will experience six days of total darkness next month because of a solar storm.",
    "sub_claims": [...],
    "entities": ["NASA", "Earth", "solar storm"],
    "topics": ["science", "space", "misinformation"],
    "claim_type": "social media claim"
  }
}

===== STEP 2 - WEB EVIDENCE RETRIEVAL (TOOL) =====
{
  "evidence_quality": {
    "requested_results": 5,
    "retrieved_results": 5,
    "status": "ok"
  }
}
```

## Limitations

- Search snippets are weaker than full article text.
- DuckDuckGo HTML structure may change.
- Some claims require domain experts, official datasets, or paid news archives.
- Conflicting sources can make scoring uncertain.
- The LLM can still misread evidence, so the report should be treated as an assisted verification draft.
- The agent does not automatically rank source reliability beyond simple retrieval metadata.

## Future Improvements

- Add full-page article fetching and citation extraction.
- Add source reliability scoring.
- Add official-site targeted search for government, health, and science claims.
- Add claim-by-claim confidence scores.
- Add a small web UI for demos.
- Add tests for prompt output schema validation.
