# Việc cần làm — Lab 3 (checklist nhóm & cá nhân)

Đối chiếu `SCORING.md`, `EVALUATION.md`, `report/NOP_BAI_CHECKLIST.md`.

---

## A. Code & chạy thử (đã có sẵn — chỉ cần dùng đúng)

- [ ] Mỗi người `git pull`, copy `.env.example` → `.env`, **không** commit `.env`.
- [ ] Cài: `pip install -r requirements-travel.txt`.
- [ ] **Bộ câu hỏi mẫu:** `data/preset_questions.json` — đã tích hợp trong Streamlit (chọn kịch bản + sửa ô tuỳ ý).
- [ ] Chạy agent: `python main.py --mode agent` hoặc `python -m streamlit run app.py`.
- [ ] Chạy baseline: `python main.py --mode chatbot` (cùng câu hỏi để so sánh).

## B. Tổng hợp số liệu cho báo cáo (Evaluation)

- [x] Sau khi chạy nhiều lần, xuất CSV từ log:
  ```bash
  python scripts/summarize_logs.py
  ```
  File tạo trong `report/exports/` (thư mục này **gitignore** — copy bảng vào báo cáo Word/Google Doc nếu cần nộp).
- [x] Đọc `llm_metrics.csv`: latency, tokens, **completion_ratio**; gom theo session **agent** vs **chatbot**.
- [x] Đọc `sessions_summary.csv`: **steps**, **outcome** (`final_answer` / `max_steps`), **llm_calls**.

## C. Báo cáo nhóm (`report/group_report/GROUP_REPORT_[TEN].md`)

- [x] Executive summary + tỷ lệ thành công (số câu test tự định nghĩa).
- [x] Kiến trúc ReAct + bảng tool (tiến hóa mô tả / tham số nếu có v2).
- [x] **Agent v1 vs v2** (mô tả thay đổi: prompt, parse `Action`, demo/API, retry Gemini, resolve model…).
- [x] **Hai trace**: một **thành công**, một **thất bại** (parse / 429 / thiếu key) — trích `logs/` hoặc Discord.
- [x] Bảng **Chatbot vs Agent** (đúng/sai hoặc chất lượng câu trả lời + token/latency từ CSV).
- [x] Flowchart + insight nhóm.
- [x] RCA ngắn (1 case failure).

## D. Discord / lớp

- [x] Post trace Thought → Action → Observation, **≥ 3 bước**, ghi tool + tham số + Observation.

## E. Báo cáo cá nhân (`report/individual_reports/REPORT_[HO_TEN].md`)

- [x] I. Đóng góp code (file cụ thể).
- [x] II. Một **debug case** có trích log.
- [x] III. Insight Chatbot vs ReAct (3 câu hỏi template).
- [x] IV. Hướng phát triển production.

## F. Bonus (tùy thời gian)

- [ ] Extra tool (hotel, search…).
- [ ] Bảng ablation prompt (2 phiên bản, đếm lỗi).
- [ ] Demo trực tiếp với GV (+5).

---

Ghi chú hiện trạng:
- Đã tổng hợp lại số liệu CSV bằng `python scripts/summarize_logs.py` (mới nhất).
- Báo cáo nhóm đã cập nhật lại phần Telemetry và Success Rate theo dữ liệu mới.
- Đã hoàn tất Discord trace và flowchart/insight.
- Nộp theo format report tổng: `report/Lab3__C401-E3.md` và `report/Lab3__C401-E3.pdf`.
