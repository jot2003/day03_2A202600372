# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Nhom Lab 3 (Travel Agent)
- **Team Members**:
  - Hoang Kim Tri Thanh (2A202600372)
  - Dang Dinh Tu Anh (2A202600019)
  - Quach Gia Duoc (2A202600423)
  - Pham Quoc Dung (2A202600490)
  - Nguyen Thanh Nam (2A202600205)
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

Muc tieu he thong la tu dong lap ke hoach du lich (thoi tiet + ve may bay + ngan sach) theo ReAct, co telemetry de so sanh voi chatbot baseline.

- **Success Rate**:
  - Agent: 42/43 session co ket qua hop le (`final_answer`) ~ 97.7%
  - Chatbot: 2/2 session co cau tra loi (`chatbot_single_shot`) = 100%
- **Key Outcome**: Agent giai duoc bai toan nhieu buoc (weather + flights + budget), ho tro duoc cau hoi mo rong nhu ve khu hoi, tour nhieu chang, va parser ngay tu nhien (today/tomorrow/next week/...).

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

Kien truc su dung vong lap:

1. `Thought` (LLM phan ra buoc can lam)
2. `Action` (goi dung 1 tool)
3. `Observation` (ket qua JSON tu tool)
4. Lap lai den khi `Final Answer` hoac dat `max_steps`

He thong co `iter_run()` de stream tung buoc trong Streamlit (thay vi spinner tron), nen de theo doi trace khi demo.

### 2.2 Tool Definitions (Inventory)

| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `get_weather` | `city` (chuoi) | Lay thoi tiet hien tai + du bao ngan han (OpenWeather), co retry bien the ten thanh pho. |
| `search_flights` | `origin, destination, departure_date` | Tim ve 1 chieu, uu tien crawl (`fast-flights`), fallback Duffel API/demo. |
| `search_roundtrip_flights` | `origin, destination, departure_date, return_date` | Tim ve khu hoi bang 2 luot tim 1 chieu va gom ket qua. |
| `search_itinerary_flights` | `segments_text` | Tim ve cho tour nhieu chang (JSON list hoac chuoi `HAN-DAD:...; DAD-SGN:...`). |
| `calculate_travel_budget` | 4 tham so so hoc | Tinh tong chi phi, tien con lai, kha thi/khong kha thi. |

### 2.3 LLM Providers Used

- **Primary**: Gemini (`gemini-2.5-flash`)
- **Secondary (Backup)**: Co ho tro provider factory cho OpenAI/local, nhung trong dot run chinh su dung Google.

---

## 3. Telemetry & Performance Dashboard

Nguon du lieu: `report/exports/*.csv` duoc tong hop tu `logs/`.

- **Agent sessions**: 43
- **Chatbot sessions**: 2
- **Average Latency (Agent)**: ~22,221.8 ms/session
- **P50 Latency (Agent)**: ~14,757.0 ms/session
- **Average Prompt Tokens (Agent)**: ~9,946.8 tokens/session
- **Average LLM Calls (Agent)**: ~8.74 calls/session
- **Average Latency (Chatbot)**: ~22,827.0 ms/session
- **Average Prompt Tokens (Chatbot)**: ~313.5 tokens/session

Nhan xet nhanh:

- Chatbot it token prompt hon (khong loop, khong tool), nhung chat luong bai toan nhieu buoc thap hon.
- Agent ton token/loop nhieu hon, doi lai co kha nang verify bang tool va trich dan nguon.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study A: Tool parser tach sai doi so city co dau phay

- **Input**: Cau hoi weather co thanh pho dang `Da Nang, VN`.
- **Observation**: Tool bao `expected 1 args, got 2`.
- **Root Cause**: Parser cu tach theo dau phay cho moi tool, khong truong hop tool 1 tham so.
- **Fix**: Trong `registry.py`, neu tool co 1 tham so thi giu nguyen toan bo chuoi (ho tro `city=...` va `Da Nang, VN`).

### Case Study B: Flight API 422 du lieu co dau nhay don

- **Input**: `search_flights(origin='SGN', destination='HAN', departure_date='2026-05-10')`
- **Observation**: Duffel bao invalid IATA/date.
- **Root Cause**: Parser cu khong bo duoc nhay don, gui `'SGN'` thay vi `SGN`.
- **Fix**: Cap nhat parser bo ca nhay don/nhay kep va bo sung test.

### Case Study C: Citation Duffel 404

- **Observation**: Link docs cu khong con hop le.
- **Fix**: Doi sang URL docs dung + them citation tai nguyen realtime theo `offer_request_id` (khi co).

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2 (guardrails tool call)

- **Diff**:
  - Cam model "bua" ly do loi API.
  - Nhac ro quy tac goi weather/flights.
  - Huong dan dung tool roundtrip/itinerary cho bai toan phuc tap.
- **Result**:
  - Giam ro ret parse error va hallucination ve gioi han API.
  - Tang do on dinh o cac bai toan weather-only va multi-step.

### Experiment 2: Chatbot vs Agent (thuc te trong log)

| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Weather simple | Tra loi nhanh, it chung cu | Co goi tool + citation + JSON observation | **Agent** |
| Multi-step budget + weather + flights | De tra loi chung chung | Co trace day du, tinh ngan sach theo du lieu tool | **Agent** |
| Prompt mo ho ve ngay bay | Thuong doan nghia tu do | Parser ngay tu nhien + metadata ambiguity | **Agent** |

---

## 6. Production Readiness Review

- **Security**:
  - API key nam trong `.env`, khong commit.
  - Tool parse co validation input (IATA/date).
- **Guardrails**:
  - Gioi han `max_steps`.
  - Retry/fallback ro rang (crawl -> API -> demo theo cau hinh).
  - Log su kien de truy vet full pipeline.
- **Scaling**:
  - Da tach module ro (`tools`, `agent`, `reporting`).
  - Co the nang cap them cache cho truy van lap, queue background, va bo loc output theo schema chat che hon.

---

## 7. Submission Evidence Map

- **Code so sanh Chatbot vs Agent**: `main.py`, `app.py`
- **ReAct core**: `src/agent/agent.py`
- **Tools**: `src/tools/weather.py`, `src/tools/flights.py`, `src/tools/budget.py`, `src/tools/registry.py`
- **Telemetry & summary**: `logs/`, `src/reporting/log_summary.py`, `scripts/summarize_logs.py`
- **CSV phan tich**: `report/exports/llm_metrics.csv`, `report/exports/sessions_summary.csv`, `report/exports/event_counts.csv`

---

> [!NOTE]
> Bao cao nay da duoc doi ten theo quy dinh: `GROUP_REPORT_NHOM.md` trong thu muc `report/group_report/`.
