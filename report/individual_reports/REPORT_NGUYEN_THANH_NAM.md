# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Thành Nam
- **Student ID**: 2A202600205
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

- **Modules Implementated**: `src/reporting/log_summary.py`, `scripts/summarize_logs.py`, `report/exports/*`.
- **Code Highlights**:
  - Tổng hợp log JSON thành bảng số liệu phục vụ chấm điểm.
  - Xuất CSV cho latency, token, event count, session summary.
  - Hỗ trợ phân tích chatbot vs agent theo phiên chạy.
- **Documentation**:
  - Chuẩn hóa quy trình lấy số liệu để điền report nhóm và case study cá nhân.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Số liệu dashboard chưa đồng nhất giữa các lần chạy.
- **Log Source**: `logs/YYYY-MM-DD.log` và file export trong `report/exports/`.
- **Diagnosis**: Có phiên demo fallback lẫn với phiên API thật làm méo so sánh.
- **Solution**: Thêm lọc/ghi chú theo nguồn dữ liệu, và chuẩn hóa tiêu chí lấy mẫu khi tổng hợp.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Agent cho phép giải thích “vì sao trả lời như vậy” bằng trace.
2. **Reliability**: Agent kém hơn khi tool phụ thuộc mạng/API và thiếu cơ chế retry hợp lý.
3. **Observation**: Observation giúp kết luận dựa dữ liệu đo được thay vì chỉ dựa suy đoán.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Thu thập telemetry theo batch và lưu kho dữ liệu dài hạn.
- **Safety**: Ẩn thông tin nhạy cảm trong log trước khi chia sẻ.
- **Performance**: Thiết lập cảnh báo tự động khi độ trễ hoặc tỉ lệ lỗi vượt ngưỡng.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
