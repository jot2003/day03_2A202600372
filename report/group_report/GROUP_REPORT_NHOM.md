# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Nhom Lab 3 (Travel Agent)
- **Team Members**: Hoang Kim Tri Thanh (2A202600372), Dang Dinh Tu Anh (2A202600019), Quach Gia Duoc (2A202600423), Pham Quoc Dung (2A202600490), Nguyen Thanh Nam (2A202600205)
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

Mục tiêu hệ thống là xây dựng trợ lý du lịch dùng ReAct để giải bài toán nhiều bước (thời tiết, vé máy bay, ngân sách), sau đó so sánh hiệu quả với chatbot baseline không dùng tool.

- **Success Rate**:
  - Agent: 42/43 phiên có kết quả hợp lệ (`final_answer`) ~ 97.7%.
  - Chatbot: 2/2 phiên có câu trả lời (`chatbot_single_shot`) = 100%.
- **Key Outcome**: Agent xử lý tốt các truy vấn nhiều bước, hỗ trợ vé khứ hồi/tour nhiều chặng, hiểu ngày tự nhiên và có trích dẫn nguồn theo dữ liệu tool.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
Hệ thống dùng vòng lặp Thought -> Action -> Observation:

1. LLM phân rã yêu cầu và tạo `Thought`.
2. LLM gọi đúng một tool ở mỗi bước qua `Action`.
3. Tool trả JSON làm `Observation`.
4. Lặp lại đến `Final Answer` hoặc dừng tại `max_steps`.

Ứng dụng Streamlit hiển thị tiến độ từng bước (streaming) để demo và truy vết rõ ràng.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `get_weather` | `city` (string) | Lấy thời tiết hiện tại + dự báo ngắn hạn (OpenWeather), có retry biến thể query. |
| `search_flights` | `origin, destination, departure_date` | Tìm vé một chiều, ưu tiên crawl `fast-flights`, fallback Duffel API/demo. |
| `search_roundtrip_flights` | `origin, destination, departure_date, return_date` | Tìm vé khứ hồi bằng hai lượt one-way. |
| `search_itinerary_flights` | `segments_text` | Tìm vé tour nhiều chặng (JSON list hoặc chuỗi tuyến). |
| `calculate_travel_budget` | 4 số | Tính chi phí và tính khả thi ngân sách. |

### 2.3 LLM Providers Used
- **Primary**: Gemini (`gemini-2.5-flash`)
- **Secondary (Backup)**: Provider factory hỗ trợ OpenAI/local (không dùng trong run chính).

---

## 3. Telemetry & Performance Dashboard

Nguồn dữ liệu: `report/exports/*.csv` tổng hợp từ `logs/`.

- **Average Latency (P50)**: ~14,757.0 ms/phiên (agent).
- **Max Latency (P99)**: phiên chậm nhất trong tập ghi nhận ~82,272 ms.
- **Average Tokens per Task**:
  - Agent: ~9,946.8 prompt tokens/phiên.
  - Chatbot: ~313.5 prompt tokens/phiên.
- **Total Cost of Test Suite**: dùng `cost_estimate` trong CSV, mức chi phí ước tính tăng theo số vòng lặp và số lần gọi tool của agent.

Nhận xét: chatbot rẻ token hơn do single-shot, trong khi agent tốn tài nguyên hơn nhưng cung cấp được lời giải có chứng cứ từ tool.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study: Parser lỗi tham số tool và định dạng input
- **Input**: `get_weather(Da Nang, VN)` và `search_flights(origin='SGN', destination='HAN', departure_date='2026-05-10')`
- **Observation**:
  - Weather từng gặp `expected 1 args, got 2` do dấu phẩy trong city.
  - Flight từng gặp 422 do tham số còn nháy đơn.
- **Root Cause**:
  - Parser cũ tách dấu phẩy cho mọi tool.
  - Parser cũ chưa strip đầy đủ nháy đơn/nháy kép ở token.
- **Fix**:
  - Với tool một tham số: giữ nguyên chuỗi đầy đủ.
  - Chuẩn hóa parse cho cả `'...'` và `"..."`.
  - Bổ sung test hồi quy trong `tests/test_travel_tools.py`.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2
- **Diff**: thêm guardrails gọi tool, cấm model bịa giới hạn API, hướng dẫn rõ tool cho bài toán khứ hồi/tour.
- **Result**: giảm parse error/hallucination và tăng độ ổn định ở câu hỏi weather-only + multi-step.

### Experiment 2 (Bonus): Chatbot vs Agent
| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Simple Q | Trả lời nhanh nhưng chung chung | Có tool + citation + observation JSON | **Agent** |
| Multi-step | Dễ thiếu bước và thiếu căn cứ | Xử lý tuần tự weather/flights/budget có trace | **Agent** |

---

## 6. Production Readiness Review

- **Security**: khóa API lưu trong `.env`, không commit; đầu vào tool có kiểm tra định dạng IATA/date.
- **Guardrails**: giới hạn `max_steps`, cơ chế fallback (crawl -> API -> demo), log sự kiện chi tiết.
- **Scaling**: tách module rõ (`agent`, `tools`, `reporting`), có thể mở rộng cache/queue/schema validation chặt hơn.

---

> [!NOTE]
> Submit this report by renaming it to `GROUP_REPORT_[TEAM_NAME].md` and placing it in this folder.
