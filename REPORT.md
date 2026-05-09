# Fake News Verification Agent: Written Report, Prompt Design, and Demo Notes

## Written Report

### Problem Statement

The project I built is a Fake News Verification Agent. It accepts a headline, social media post, article excerpt, or short claim and produces a structured fact-check report. Fake news verification is a good task for multi-step chaining because it is not just a writing problem. A system first has to understand what factual claim is being made, then gather external evidence, then compare the claim with that evidence, then decide how credible the claim is, and finally communicate the result in a careful way. If all of this is done in one prompt, the model may skip steps, use its memory as if it were live evidence, or produce a confident answer even when the evidence is weak. Chaining makes the process easier to inspect because every stage leaves behind an intermediate output.

### Chain Design

The chain has five stages, four of which are LLM calls. Step 1 is claim extraction. It receives the raw user input and returns a JSON object containing the main claim, sub-claims, entities, topics, and claim type. This stage is separate because search works better when the system has extracted the important entities and factual statements instead of searching the whole article blindly. Step 2 is the tool step. It receives the extracted claims and entities and uses DuckDuckGo search to collect source titles, snippets, URLs, and source domains. This output is stored as evidence and evidence-quality metadata. Step 3 is evidence analysis. It receives the claims from Step 1 and the evidence from Step 2, then classifies the claims as supported, contradicted, or uncertain. Step 4 is credibility scoring. It receives the evidence analysis and retrieval quality data and turns them into a score from 0 to 100, a confidence level, a misinformation risk level, and justifications. Step 5 is final report generation. It receives the whole shared state and writes a professional Markdown fact-check report.

The important design choice is that each step depends on the previous one. Step 2 cannot build good search queries without Step 1. Step 3 cannot analyze evidence without both claims and retrieved sources. Step 4 should not score credibility until Step 3 has separated support from contradiction. Step 5 uses everything that came before it, including the retrieval errors and confidence level, so the final report is not just a generic answer.

### Tool Integration

The external tool is DuckDuckGo web search. I used web retrieval because LLMs are not search engines and should not be trusted to know whether a recent claim is true. They can also hallucinate sources if asked to verify a claim from memory. The search tool provides grounding by returning evidence items with titles, snippets, URLs, and source names. The LLM steps after retrieval are instructed to use only this evidence. The tool function includes error handling for timeouts, empty results, API or network failure, and malformed responses. If retrieval fails, the chain still continues, but the evidence-quality metadata says the status is empty or partial. This forces the later LLM calls to give a cautious or uncertain verdict rather than pretending the claim was verified.

### Limitations

The system is still limited. It relies on search snippets, and snippets can be incomplete or misleading. Some topics, such as health or law, require expert interpretation that a simple search pipeline cannot fully provide. Source reliability is also difficult: a search result from an unknown blog should not count the same as a primary source, but the current implementation only stores basic source metadata. Conflicting evidence is another challenge because the model may need more context than five results provide. API or network failures can also weaken the result. Finally, ambiguous claims are hard to check. If a user says “they are hiding the truth,” there may be no concrete factual claim to verify.

### Reflection

If I had more time, I would add a full article fetching step so the model could analyze complete evidence instead of snippets. I would also add source reliability scoring, official-source search filters, and stronger JSON schema validation. One thing I learned while building this is that the hardest part is not calling the LLM; it is deciding what each call should know and what it should not know. The chain becomes easier to debug when each step has a narrow responsibility and a clear output format. I also realized that failure handling is part of the reasoning design: if search fails, the final answer should become more cautious, not more creative.

## Prompt Design Section

### Step 1 — Claim Extraction

**System prompt**

```text
You are a careful fact-checking claim extraction assistant.
Your job is not to decide whether the text is true yet. Your job is only to extract checkable factual claims.
Separate factual statements from opinions, predictions, jokes, or emotional language.
Return only valid JSON. Do not wrap the JSON in Markdown.

Required JSON schema:
{
  "main_claim": "one sentence summary of the central factual claim",
  "sub_claims": ["specific factual sub-claims that can be checked"],
  "entities": ["people, organizations, places, laws, products, datasets, or events mentioned"],
  "topics": ["topic labels such as politics, health, climate, technology, economy"],
  "claim_type": "news headline | social media claim | article excerpt | quote | unclear"
}
```

**User prompt**

```text
Extract factual claims from the user text below.
If the input is vague, keep the main_claim conservative and put uncertain details in sub_claims only when they are actually stated.

USER_NEWS_TEXT:
{user_input}
```

This prompt matters because Step 2 uses the claim and entity fields to build search queries. The JSON constraint prevents the next step from needing to parse unstructured prose.

### Step 3 — Evidence Analysis

**System prompt**

```text
You are an evidence analyst for a fact-checking pipeline.
You must compare extracted claims against retrieved web evidence.
Do not use your memory as evidence. Use only the evidence items provided.
Return only valid JSON. Do not wrap the JSON in Markdown.
```

**User prompt**

```text
Analyze whether the evidence supports or contradicts the extracted claims.
If retrieval failed or evidence is sparse, say that the relevant claims are uncertain rather than guessing.

EXTRACTED_CLAIMS_JSON:
{claims}

RETRIEVED_EVIDENCE_JSON:
{evidence}
```

The key constraint is “use only the evidence items provided.” Without that line, the model might answer from memory and hide the retrieval failure. Step 4 depends on the supported, contradicted, and uncertain lists.

### Step 4 — Credibility Scoring

**System prompt**

```text
You are a fact-checking credibility scorer.
Score credibility using only the claim extraction, retrieved evidence, and evidence analysis supplied by the pipeline.
Return only valid JSON. Do not wrap the JSON in Markdown.
```

**User prompt**

```text
Generate a credibility score for the original claim using the previous step outputs.
Consider evidence quantity, source quality, contradictions, and uncertainty.

EXTRACTED_CLAIMS_JSON:
{claims}

EVIDENCE_QUALITY_JSON:
{evidence_quality}

EVIDENCE_ANALYSIS_JSON:
{analysis}
```

This prompt separates scoring from evidence analysis. That makes the score more explainable because the model has to use the already-classified evidence rather than redoing the whole task informally.

### Step 5 — Final Report

**System prompt**

```text
You are a professional fact-check report writer.
Write a clear Markdown report for a reader who wants to know whether the original claim is credible.
Use only the state data supplied by the pipeline. Do not invent sources, dates, or facts.
The report must include these sections:
1. Original Claim
2. Extracted Factual Claims
3. Evidence Summary
4. Supported vs. Contradicted Points
5. Credibility Score
6. Confidence Level
7. Final Verdict
8. Limitations of Verification
```

**User prompt**

```text
Create the final fact-check report from the complete shared state below.
Use the credibility score and confidence level exactly as provided unless the state is malformed.
Make the verdict cautious if retrieval failed, evidence is weak, or claims are ambiguous.

SHARED_STATE_JSON:
{state}
```

The final prompt is Markdown instead of JSON because the deliverable should be readable by a real person. The previous outputs still remain available in the JSON state file.

### Failed Prompt Iteration Example

An earlier version of the evidence-analysis prompt said, “Use the evidence and your knowledge to decide if the claim is true.” This was a bad prompt because the model sometimes added facts that were not in the retrieved snippets. I changed it to say, “Do not use your memory as evidence. Use only the evidence items provided.” I also forced the output into supported, contradicted, and uncertain lists. This improved the chain because Step 4 could score the claim based on explicit categories instead of vague paragraphs.

## Possible Viva Questions and Answers

**Why not use one prompt?**  
Because fake news verification has several different tasks: extracting claims, retrieving evidence, comparing evidence, scoring credibility, and writing a report. One prompt hides those steps and makes errors hard to inspect.

**Why use external search?**  
LLMs are not reliable databases. Search gives the system current external evidence and reduces the chance that the model invents sources or relies on outdated memory.

**What happens if retrieval fails?**  
The tool records an empty or partial status in `state["evidence_quality"]`, stores errors in `state["errors"]`, and the chain continues. Later prompts are told to mark claims uncertain when evidence is missing.

**What is stored in state?**  
The state stores the original input, extracted claims, retrieved evidence, evidence quality, evidence analysis, credibility scoring, final report, errors, and a trace of each step’s inputs and outputs.

**Where does the chain fail?**  
It can fail on vague claims, weak search results, misleading snippets, source reliability problems, and cases where expert domain knowledge is required.

**Why are outputs structured?**  
Structured outputs make dependencies explicit. Step 2 needs `entities`; Step 3 needs `claims` and `evidence`; Step 4 needs `analysis`; Step 5 needs the whole state.

**How does each step depend on the previous one?**  
Step 2 searches using Step 1 claims. Step 3 compares Step 1 claims with Step 2 evidence. Step 4 scores based on Step 3 analysis and Step 2 evidence quality. Step 5 writes the final report using every previous output.
