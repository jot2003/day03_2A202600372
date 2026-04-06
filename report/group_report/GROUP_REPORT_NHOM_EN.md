# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Nhom Lab 3 (Travel Agent)
- **Team Members**: Hoang Kim Tri Thanh (2A202600372), Dang Dinh Tu Anh (2A202600019), Quach Gia Duoc (2A202600423), Pham Quoc Dung (2A202600490), Nguyen Thanh Nam (2A202600205)
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

The project goal is to build a ReAct travel assistant that solves multi-step queries (weather, flights, budget) and compare it against a chatbot baseline.

- **Success Rate**:
  - Agent: 42/43 sessions reached a valid `final_answer` (~97.7%).
  - Chatbot: 2/2 sessions returned an answer (100%).
- **Key Outcome**: The agent handles complex travel planning (round-trip, multi-leg itinerary, natural-language dates) with tool-backed evidence and citations.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
The system follows a Thought -> Action -> Observation loop:

1. The LLM decomposes user intent into a `Thought`.
2. It executes one tool call via `Action`.
3. The tool returns structured JSON as `Observation`.
4. The loop continues until `Final Answer` or `max_steps`.

In Streamlit, step events are streamed live to show agent progress during demos.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `get_weather` | `city` (string) | Fetch current weather + short forecast from OpenWeather with query variants/retry. |
| `search_flights` | `origin, destination, departure_date` | Search one-way flights; prioritize `fast-flights` crawl, fallback to Duffel API/demo. |
| `search_roundtrip_flights` | `origin, destination, departure_date, return_date` | Build round-trip options by combining two one-way searches. |
| `search_itinerary_flights` | `segments_text` | Search multi-leg tour routes (JSON list or compact route string). |
| `calculate_travel_budget` | 4 numeric fields | Compute total cost, remaining budget, and feasibility. |

### 2.3 LLM Providers Used
- **Primary**: Gemini (`gemini-2.5-flash`)
- **Secondary (Backup)**: Provider factory supports OpenAI/local providers when needed.

---

## 3. Telemetry & Performance Dashboard

Data source: `report/exports/*.csv`, aggregated from `logs/`.

- **Average Latency (P50)**: ~14,757.0 ms/session (agent).
- **Max Latency (P99)**: slowest observed session ~82,272 ms.
- **Average Tokens per Task**:
  - Agent: ~9,946.8 prompt tokens/session.
  - Chatbot: ~313.5 prompt tokens/session.
- **Total Cost of Test Suite**: estimated via `cost_estimate` in exported metrics; rises with loop/tool depth.

Quick reading: chatbot is cheaper in tokens, while the agent is stronger on factual multi-step tasks due to tool grounding.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study: Tool-argument parsing failures
- **Input**: `get_weather(Da Nang, VN)` and `search_flights(origin='SGN', destination='HAN', departure_date='2026-05-10')`
- **Observation**:
  - Weather failed with `expected 1 args, got 2` when city contained a comma.
  - Flight failed with 422 because quoted IATA/date values were not normalized.
- **Root Cause**:
  - Old parser split commas too aggressively for single-argument tools.
  - Old parser did not consistently strip single and double quotes.
- **Fix**:
  - Preserve full input for one-parameter tools.
  - Normalize both `'...'` and `"..."` argument values.
  - Add regression tests in `tests/test_travel_tools.py`.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2
- **Diff**: added stricter tool-call guardrails, prohibited fabricated API limitations, and clarified when to use round-trip/itinerary tools.
- **Result**: fewer invalid actions and better stability on weather-only and multi-step queries.

### Experiment 2 (Bonus): Chatbot vs Agent
| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Simple Q | Fast but generic | Tool-backed answer with citations | **Agent** |
| Multi-step | Often misses steps or evidence | Structured weather/flights/budget chain with trace | **Agent** |

---

## 6. Production Readiness Review

- **Security**: API keys are in `.env` (not committed); tool inputs are validated (IATA/date format checks).
- **Guardrails**: loop limit via `max_steps`, fallback policy (crawl -> API -> demo), event logging for full traceability.
- **Scaling**: modular design (`agent`, `tools`, `reporting`) is ready for future cache/queue/schema-hardening improvements.

---

> [!NOTE]
> Submit this report by renaming it to `GROUP_REPORT_[TEAM_NAME].md` and placing it in this folder.
