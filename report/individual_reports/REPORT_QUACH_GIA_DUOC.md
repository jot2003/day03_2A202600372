# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Quách Gia Được
- **Student ID**: 2A202600423
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

- **Modules Implementated**: `src/agent/agent.py`, `main.py`, `app.py`.
- **Code Highlights**:
  - Xây dựng luồng ReAct với `iter_run()` để stream Thought/Action/Observation.
  - Tối ưu cách dừng vòng lặp và gom final answer.
  - Đồng bộ hành vi CLI và Streamlit theo cùng một core agent.
- **Documentation**:
  - Làm rõ quy tắc gọi tool trong prompt và mô tả cách trace phiên làm việc.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Agent đôi lúc gọi sai tool ở câu hỏi chỉ weather.
- **Log Source**: `logs/YYYY-MM-DD.log` với chuỗi Action sai ngữ cảnh.
- **Diagnosis**: Prompt điều hướng tool chưa rõ ưu tiên theo intent.
- **Solution**: Tăng ràng buộc mapping intent -> tool và thêm ví dụ few-shot trong prompt hệ thống.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Thought làm agent “nghĩ theo bước”, khác chatbot trả lời một phát.
2. **Reliability**: Khi số bước nhiều, agent có rủi ro tích lũy lỗi cao hơn chatbot.
3. **Observation**: Observation giúp agent tự sửa ở bước sau, nhất là khi action đầu chưa chuẩn.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Thiết kế planner-executor tách lớp cho nhiều tool hơn.
- **Safety**: Thêm policy chặn action nguy hiểm và kiểm tra tham số trước khi thực thi.
- **Performance**: Dùng chiến lược early-stop nếu đủ dữ liệu để trả lời.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
