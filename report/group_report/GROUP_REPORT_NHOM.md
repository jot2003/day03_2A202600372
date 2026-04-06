# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Nhóm C401-E3
- **Team Members**: Hoang Kim Tri Thanh (2A202600372), Dang Dinh Tu Anh (2A202600019), Quach Gia Duoc (2A202600423), Pham Quoc Dung (2A202600490), Nguyen Thanh Nam (2A202600205)
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

Mục tiêu hệ thống là xây dựng trợ lý du lịch dùng ReAct để giải bài toán nhiều bước (thời tiết, vé máy bay, ngân sách), sau đó so sánh hiệu quả với chatbot baseline không dùng tool.

- **Success Rate**:
  - Agent: 55/56 phiên có kết quả hợp lệ (`final_answer`) ~ 98.2%.
  - Chatbot: 4/4 phiên có câu trả lời (`chatbot_single_shot`) = 100%.
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

### 2.1.1 Team Contribution Split (final)
- Hoàng Kim Trí Thành: mảng weather (`get_weather`, OpenWeather citation, weather reliability).
- Đặng Đình Tú Anh: mảng flight (`search_flights`, roundtrip/itinerary, parser và citation kiểm chứng).
- Các thành viên còn lại: agent loop, test/telemetry và đóng gói báo cáo.

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

- **Số phiên đánh giá**: 60 phiên (56 agent, 4 chatbot).
- **Average Latency (P50)**: ~15,316.5 ms/phiên (agent).
- **Max Latency (P99)**: phiên chậm nhất trong tập ghi nhận ~82,272 ms.
- **Average Tokens per Task**:
  - Agent: ~11,751.2 prompt tokens/phiên.
  - Chatbot: ~314.2 prompt tokens/phiên.
- **Total Cost of Test Suite**: dùng `cost_estimate` trong CSV, mức chi phí ước tính tăng theo số vòng lặp và số lần gọi tool của agent.

Nhận xét: chatbot rẻ token hơn do single-shot, trong khi agent tốn tài nguyên hơn nhưng cung cấp được lời giải có chứng cứ từ tool.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study (Success Trace): Multi-step weather + flight + budget
- **Input**: Câu multi-step HAN -> DAD + weather + budget.
- **Trace tóm tắt**:
  - `Thought/Action 1`: gọi `get_weather(Da Nang, VN)`.
  - `Thought/Action 2`: gọi `search_flights(HAN, DAD, 2026-04-15)`.
  - `Thought/Action 3`: gọi `calculate_travel_budget(...)`.
  - `Final Answer`: kết luận khả thi ngân sách dựa trên dữ liệu tool.
- **Kết quả**: Chuỗi suy luận có đủ dữ liệu và dừng đúng ở `final_answer`.

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

## 5.1 Flowchart & Group Insights

### Flowchart hệ thống (rút gọn cho demo)

```text
Người dùng nhập câu hỏi
        |
        v
LLM tạo Thought + chọn Action
        |
        v
Gọi đúng 1 tool mỗi bước
  - get_weather
  - search_flights / roundtrip / itinerary
  - calculate_travel_budget
        |
        v
Nhận Observation (JSON)
        |
        v
Nếu đủ dữ liệu -> Final Answer
Nếu chưa đủ -> lặp Thought/Action tiếp
```

### Insight nhóm (rút ra sau triển khai)

- **Insight 1 - Trải nghiệm quan trọng hơn “trả lời hay”**: khi có trace từng bước + citation bấm được, người dùng tin hệ thống hơn rõ rệt.
- **Insight 2 - Tool design quyết định chất lượng agent**: parse tham số và chuẩn hóa input (city/date) ảnh hưởng trực tiếp đến tỉ lệ thành công.
- **Insight 3 - Nên ưu tiên workflow thực tế**: mặc định one-way, chỉ chuyển roundtrip khi user nói rõ giúp giảm lỗi logic khi demo.
- **Insight 4 - Dữ liệu thời gian thực cần fallback rõ ràng**: crawl/API có thể trả rỗng theo tuyến/ngày, nên fallback + thông báo minh bạch là bắt buộc.

---

## 6. Production Readiness Review

- **Security**: khóa API lưu trong `.env`, không commit; đầu vào tool có kiểm tra định dạng IATA/date.
- **Guardrails**: giới hạn `max_steps`, cơ chế fallback (crawl -> API -> demo), log sự kiện chi tiết.
- **Scaling**: tách module rõ (`agent`, `tools`, `reporting`), có thể mở rộng cache/queue/schema validation chặt hơn.

---

> [!NOTE]
> Submit this report by renaming it to `GROUP_REPORT_[TEAM_NAME].md` and placing it in this folder.
