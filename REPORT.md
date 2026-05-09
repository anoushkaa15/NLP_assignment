# Written Report and Prompt Design Appendix

## Written report

The agent solves a practical travel-planning problem: it converts a rough natural-language trip request into a weather-aware itinerary brief. This task benefits from multi-step chaining because the answer depends on several different kinds of reasoning that should not be mixed together. First, the system must identify factual planning variables such as destination, dates, interests, pace, and constraints. Second, it must retrieve external weather data instead of asking the LLM to guess. Third, it must interpret those conditions in relation to the traveler’s goals. Fourth, it must draft a plan, critique whether that plan actually obeys the earlier constraints, and then revise the result into a usable report. A single prompt could produce a nice-looking itinerary, but it would be harder to inspect, more likely to hallucinate weather, and less useful during a demo because there would be no clear intermediate artifacts to explain.

The chain has six steps, five of which are Grok LLM calls. Step 1 receives only the raw user request and returns a structured JSON parse with destination, dates, travelers, budget, pace, interests, constraints, missing information, and confidence. This step is separate because the tool cannot safely run until the destination and dates are available in predictable fields. Step 2 is the external tool call. It receives the parsed request, geocodes the destination with Open-Meteo, and then requests forecast or historical daily weather rows when exact dates are present. It writes a structured `weather` object into shared state, including a status field so later steps can distinguish real data from unavailable data. Step 3 receives the parsed request and weather object and returns a planning analysis: assumptions, risks, opportunities, packing advice, daily strategy, and uncertainties. This is separate from drafting because it forces the model to reason about conditions before it starts producing attractive itinerary text. Step 4 receives the parsed request and condition analysis and returns a day-by-day itinerary draft in JSON. Step 5 receives the draft plus earlier constraints and produces a critique with required revisions. Step 6 receives the accumulated state and produces the final Markdown report, using the critique as explicit revision instructions.

The external tool is Open-Meteo, specifically its geocoding and weather APIs. I chose it because it is free, does not require another API key, and returns structured data that can be passed directly into a later prompt. Its output enters the chain through the shared `state["weather"]` object. If the tool fails, finds no location, or cannot parse the response, it returns `status: "unavailable"` and a reason instead of crashing. Step 3’s prompt then instructs the LLM to mark weather-specific recommendations as uncertain rather than inventing facts. This failure behavior is important for the live demo question about what happens when the tool call returns nothing.

The chain has several limitations. It does not book tickets, verify opening hours, or calculate travel times between every attraction, so a polished itinerary can still contain activities that are closed, sold out, or too far apart. Forecast data is only meaningful near the travel dates; when dates are far in the future, the weather API may return limited data or fail. The parser also depends on the LLM returning valid JSON with the requested keys. The code validates the most important fields, but it does not fully validate every nested item in later LLM outputs. Very vague input such as “plan something fun” breaks the chain because there is no destination for the weather tool. Multi-city trips are also only partially supported because the parser returns one destination field and the weather tool geocodes only that first destination.

If I had more time, I would add a second tool for places or transit data so the itinerary could verify travel time and opening hours. I would also add stronger schema validation with Pydantic, support multi-city requests by looping over destinations, and cache tool responses for repeat demos. The most useful improvement would be an interactive repair step: when Step 1 finds missing destination or dates, the CLI could ask a follow-up question instead of simply stopping or continuing with uncertainty. During development I used LLM assistance to scaffold some boilerplate and to think through prompt boundaries, but I kept the chain design simple and inspectable so I can explain every state transition during evaluation.

## Prompt design appendix

### Step 1: parse request

**System prompt**

```text
STEP_ID: parse_request
You are a travel-request parser. Return only valid JSON. Extract the user's trip request into fields that downstream tools can use. Do not invent missing dates or destinations. If information is absent, put null or an empty list and describe it in missing_information.
Required JSON keys: destination, start_date, end_date, trip_length_days, travelers, budget, pace, interests, constraints, missing_information, confidence.
Dates must be ISO YYYY-MM-DD when present. confidence must be low, medium, or high.
```

**User prompt template**

```text
Parse this travel request into the required JSON schema.

RAW_REQUEST:
{raw_request}
```

This prompt is strict because the next step is a tool call. The geocoder needs a destination string and the weather API needs ISO dates, so the system prompt forbids invented destinations and dates. The `missing_information` and `confidence` fields are included so malformed input can be handled honestly.

### Step 3: analyze conditions

**System prompt**

```text
STEP_ID: analyze_conditions
You are a practical travel risk analyst. Return only valid JSON. Use the parsed request and tool weather data to identify planning assumptions, weather risks, weather opportunities, packing advice, daily strategy, and uncertainties. If weather.status is unavailable, explicitly mark weather-specific advice as uncertain instead of fabricating weather facts.
Required JSON keys: planning_assumptions, weather_risks, weather_opportunities, packing_advice, daily_strategy, uncertainties.
```

**User prompt template**

```text
Use Step 1 and Step 2 outputs to produce weather-aware planning analysis.

STEP_1_PARSED_REQUEST:
{parsed_request_json}

STEP_2_TOOL_WEATHER:
{weather_json}
```

This prompt isolates reasoning about conditions from itinerary writing. The next step depends on `daily_strategy`, `packing_advice`, and `uncertainties`; without those fields, the itinerary drafter would be tempted to bury weather caveats in prose or omit them entirely.

### Step 4: draft itinerary

**System prompt**

```text
STEP_ID: draft_itinerary
You are a travel itinerary drafter. Return only valid JSON. Create a realistic day-by-day itinerary that obeys the parsed user constraints and uses the condition analysis. Keep the pace consistent with the parsed pace field. Every day must include a rain_backup.
Required JSON keys: title, days. Each item in days must include day, theme, morning, afternoon, evening, rain_backup.
```

**User prompt template**

```text
Draft an itinerary from the previous structured outputs.

STEP_1_PARSED_REQUEST:
{parsed_request_json}

STEP_3_CONDITION_ANALYSIS:
{condition_analysis_json}
```

This prompt requires a JSON draft rather than a final report so the critique step can inspect day-level structure. The `rain_backup` requirement is included because the domain is weather-aware planning and because the final report needs concrete contingency options.

### Step 5: critique itinerary

**System prompt**

```text
STEP_ID: critique_itinerary
You are a strict itinerary reviewer. Return only valid JSON. Compare the draft against the original parsed request and weather analysis. Identify mismatches, unsupported claims, missing backups, and places where the final answer should warn the user.
Required JSON keys: overall_score, strengths, issues, required_revisions. overall_score must be an integer from 1 to 10.
```

**User prompt template**

```text
Critique Step 4 using the earlier chain outputs. Do not rewrite the itinerary; produce revision instructions.

STEP_1_PARSED_REQUEST:
{parsed_request_json}

STEP_3_CONDITION_ANALYSIS:
{condition_analysis_json}

STEP_4_DRAFT_ITINERARY:
{draft_itinerary_json}
```

This prompt deliberately says not to rewrite the itinerary. The purpose of Step 5 is to create targeted revision instructions, not another competing final answer. Step 6 then depends on `required_revisions` to improve the draft.

### Step 6: final report

**System prompt**

```text
STEP_ID: final_report
You are a travel briefing editor. Produce a polished Markdown report, not JSON. The report must be structured with headings and be directly useful to the traveler. Use the critique to revise the draft. Include: executive summary, planning assumptions, day-by-day itinerary, weather/packing notes, contingency plan, and limitations. Do not claim bookings, opening hours, or live conditions unless present in the state.
```

**User prompt template**

```text
Create the final Markdown report from the accumulated chain state. The final report must use Step 5's critique to improve Step 4's draft.

ACCUMULATED_STATE:
{state_json}
```

The final prompt switches from JSON to Markdown because the user needs an actionable document, not raw model text or internal state. It includes a limitation instruction to prevent the report from overstating what the chain knows.

### Prompt iteration example

An earlier version of the Step 3 system prompt said only, “Analyze the weather and give advice.” In testing, that produced prose paragraphs and sometimes implied confidence even when the weather tool returned no data. I changed it to require JSON keys and added the sentence, “If `weather.status` is unavailable, explicitly mark weather-specific advice as uncertain instead of fabricating weather facts.” This made the output safer and easier for Step 4 to consume because risks, opportunities, and uncertainties were separated into predictable fields.
