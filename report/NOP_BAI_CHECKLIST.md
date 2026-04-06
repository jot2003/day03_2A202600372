# Checklist nộp bài Lab 3 (đối chiếu rubric)

Tài liệu gốc: `SCORING.md`, `EVALUATION.md`, `INSTRUCTOR_GUIDE.md`, template trong `group_report/` và `individual_reports/`.

---

## 1. Nhóm — báo cáo nhóm

| Yêu cầu | Format / vị trí |
|--------|------------------|
| File báo cáo nhóm | Đổi tên template thành **`GROUP_REPORT_[TEN_NHOM].md`** và đặt trong **`report/group_report/`** |
| Nội dung | Theo đúng các mục trong `TEMPLATE_GROUP_REPORT.md` (Executive Summary → Production Readiness) |

### Map rubric nhóm (45 điểm base) → nội dung cần có trong báo cáo

| Điểm (SCORING) | Cần thể hiện trong GROUP_REPORT (gợi ý section) |
|-----------------|--------------------------------------------------|
| Chatbot Baseline (2) | Mô tả / link code baseline; cách chạy (`main.py --mode chatbot`) |
| Agent v1 (7) | §2 ReAct + tools; chứng minh vòng lặp hoạt động, ≥2 tools |
| Agent v2 (7) | §5 Ablation hoặc §4 RCA: thay đổi cụ thể so với v1 (prompt, parse, tool spec) |
| Tool design evolution (4) | Bảng tool v1 vs v2 hoặc mô tả tiến hóa mô tả tham số / use case |
| Trace quality (9) | §4: **cả trace thành công và trace thất bại** (copy từ log hoặc Discord), có Thought/Action/Observation |
| Evaluation & analysis (7) | Bảng số liệu Chatbot vs Agent (theo `EVALUATION.md`: latency, tokens, số bước, lỗi) |
| Flowchart & insight (5) | Sơ đồ luồng agent + insight nhóm (học được gì) |
| Code quality (4) | Telemetry (`logs/`, events), cấu trúc module |

### Bonus nhóm (+15, max tổng nhóm 60)

Ghi rõ trong báo cáo nếu làm: extra monitoring, extra tools, failure handling, demo live, ablation.

---

## 2. Cá nhân — báo cáo từng thành viên

| Yêu cầu | Format / vị trí |
|--------|------------------|
| File | **`REPORT_[HO_TEN].md`** (không dấu hoặc snake_case, thống nhất cả lớp) trong **`report/individual_reports/`** |
| Cấu trúc | Đúng 4 phần I–IV như `TEMPLATE_INDIVIDUAL_REPORT.md` |

**Lưu ý:** `SCORING.md` có câu ghi *"individual_report.md"*; template và NOTE lại yêu cầu **`REPORT_[YOUR_NAME].md`**. Nên **làm theo template + NOTE** (đặt tên `REPORT_...`) trừ khi giảng viên thông báo khác trên LMS/Discord.

| Phần | Điểm | Nội dung bắt buộc |
|------|------|-------------------|
| I. Technical Contribution | 15 | Module/file cụ thể, snippet hoặc tham chiếu dòng code |
| II. Debugging Case Study | 10 | 1 failure thật + trích `logs/YYYY-MM-DD.log` + nguyên nhân + cách sửa |
| III. Personal Insights | 10 | 3 câu hỏi trong template (Reasoning / Reliability / Observation) |
| IV. Future Improvements | 5 | Scalability, Safety, Performance (gợi ý production) |

---

## 3. Discord (theo slide lớp)

- Mỗi nhóm **một scenario** cần agent.
- Post **trace đầy đủ** với **Thought / Action / Observation**.
- **Tối thiểu 3 bước** (3 vòng Thought→Action→Observation hoặc tương đương).
- Trong trace phải thấy rõ: **tool nào**, **tham số**, **Observation trả về**, **khi nào dừng / Final Answer**.

(Giữ bản copy trace trong GROUP_REPORT §4 để chấm điểm Trace quality.)

---

## 4. Code & chứng cứ số liệu (`EVALUATION.md`)

- Log JSON trong **`logs/`** — dùng cho RCA và case study cá nhân.
- Metrics gợi ý khi so sánh Chatbot vs Agent:
  - Token (prompt vs completion), latency, **số bước loop**, loại lỗi (parse, hallucination tool, max_steps).

Có thể export bảng từ log hoặc chạy script parse — quan trọng là **có số liệu** trong GROUP_REPORT.

---

## 5. Trước khi nộp — tick nhanh

- [x] `report/group_report/GROUP_REPORT_[TEAM].md` đủ section + bảng Chatbot vs Agent + trace fail + trace success  
- [x] Mỗi người: có phần cá nhân trong report tổng `report/Lab3__C401-E3.md`  
- [x] Discord: đã post trace ≥3 bước (team)  
- [x] Repo/code có thể chạy được; `.env` không commit (chỉ `.env.example`)  
- [ ] (Tuỳ yêu cầu GV) Link repo / file zip / nộp trên hệ thống lớp — làm theo hướng dẫn riêng trên Canvas/LMS  

---

Checklist việc theo từng nhóm: xem thêm `report/VIEC_CAN_LAM.md`. Xuất số liệu từ log: `python scripts/summarize_logs.py`.

*Tài liệu này chỉ là checklist; rubric chính thức vẫn là `SCORING.md`.*
