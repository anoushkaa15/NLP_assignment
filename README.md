# Weather-Aware Trip Briefing Agent

This repository contains an individual programming assignment submission: a multi-step LLM agent that turns a rough travel request into a structured, weather-aware trip briefing. It uses the Grok API for every LLM call, calls the free Open-Meteo APIs as an external tool, maintains a shared state dictionary across the chain, and writes final Markdown and JSON artifacts.

## What the agent does

The agent accepts a natural-language trip request such as:

> I am visiting Kyoto from 2026-06-12 to 2026-06-15 with my partner. We like food, temples, quiet walks, and photography. Budget is medium and we prefer a relaxed pace.

It then executes a traceable chain:

1. **LLM Step 1 — parse request**: extracts destination, dates, traveler profile, constraints, and interests into JSON.
2. **Tool Step 2 — fetch weather**: geocodes the destination and retrieves forecast or climate-normal weather data from Open-Meteo.
3. **LLM Step 3 — analyze conditions**: converts the parsed trip plus weather data into risks, opportunities, packing advice, and planning assumptions.
4. **LLM Step 4 — draft itinerary**: creates a day-by-day itinerary using the previous analysis.
5. **LLM Step 5 — critique draft**: checks the draft against the parsed request and weather analysis.
6. **LLM Step 6 — finalize report**: produces a polished Markdown briefing with an executive summary, itinerary, weather notes, packing list, contingency plan, and limitations.

Each step reads from and writes to the same Python `state` dictionary. The `--trace` option prints the exact keys each step received and returned so the chain can be explained during a live demo.

## Why this is multi-step instead of one prompt

A single prompt could hallucinate weather and skip validation. This chain separates extraction, real data retrieval, analysis, drafting, critique, and final formatting. Step 3 cannot run until Steps 1 and 2 have produced structured inputs. Step 5 cannot critique the itinerary without both the draft from Step 4 and constraints extracted in Step 1.

## Installation

Python 3.10+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## API key setup

The agent uses the Grok API through xAI's OpenAI-compatible chat-completions endpoint.

Set one of these environment variables:

```bash
export XAI_API_KEY="your-grok-api-key"
# or
export GROK_API_KEY="your-grok-api-key"
```

Optional environment variables:

```bash
export GROK_MODEL="grok-3-mini"      # default used by the code
export XAI_BASE_URL="https://api.x.ai/v1"
```

## Running the agent

Run with a request string:

```bash
python -m trip_agent.cli \
  --request "I am visiting Kyoto from 2026-06-12 to 2026-06-15 with my partner. We like food, temples, quiet walks, and photography. Budget is medium and we prefer a relaxed pace." \
  --output outputs/kyoto_brief.md \
  --state-output outputs/kyoto_state.json \
  --trace
```

Or read the request from a text file:

```bash
python -m trip_agent.cli --input-file examples/sample_request.txt --trace
```

For a no-key classroom smoke test, use deterministic mock LLM responses:

```bash
python -m trip_agent.cli --input-file examples/sample_request.txt --mock-llm --trace
```

The mock mode is only for testing the program flow. The real assignment demo should run without `--mock-llm` and with a Grok API key.

## Inputs expected

The best input includes:

- destination city or region;
- travel dates, or at least month/season and trip length;
- traveler count or profile;
- interests;
- constraints such as budget, mobility, dietary needs, pace, or must-see places.

Malformed input is handled by Step 1. If the LLM cannot find a destination, the program raises a readable `AgentInputError` before calling the weather tool. If exact dates are missing, the chain can continue with climate-normal weather instead of forecast weather.

## Tool integration and failure behavior

The tool step uses two Open-Meteo endpoints:

- geocoding API to convert the extracted destination into latitude and longitude;
- forecast or archive/climate fallback logic to retrieve weather-like planning data.

If the tool fails or returns no results, the state records `weather.status = "unavailable"` and the later LLM steps must explicitly label weather-dependent recommendations as uncertain instead of inventing facts.

## Repository structure

```text
trip_agent/
  agent.py          # orchestration and shared state updates
  cli.py            # command-line interface
  grok_client.py    # Grok API client and deterministic mock client
  prompts.py        # full system/user prompts for every LLM step
  tools.py          # Open-Meteo tool calls and fallback handling
  schemas.py        # lightweight validation helpers and defaults
examples/
  sample_request.txt
REPORT.md           # written report and prompt-design appendix
requirements.txt
```

## Academic integrity note

This repository is scaffolded as a transparent, inspectable assignment submission. If you use an LLM to modify it further, record that use in the reflection section of `REPORT.md` and be prepared to explain what you accepted, rejected, and changed.
