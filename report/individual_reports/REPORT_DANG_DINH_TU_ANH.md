# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Đặng Đình Tú Anh
- **Student ID**: 2A202600019
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

- **Modules Implementated**: `src/tools/weather.py`, `docs/OPENWEATHER_SETUP_VI.md`, `app.py`.
- **Code Highlights**:
  - Cải thiện weather query retry với biến thể tên thành phố.
  - Bổ sung link kiểm chứng trực tiếp và message lỗi rõ ràng.
  - Cập nhật hiển thị citation theo kết quả tool.
- **Documentation**:
  - Đồng bộ hướng dẫn cấu hình OpenWeather để hỗ trợ debug nhanh cho team.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Agent trả lời sai lý do lỗi weather (hallucination) thay vì dùng observation thật.
- **Log Source**: `logs/YYYY-MM-DD.log` tại chuỗi `AGENT_LLM_STEP` và `AGENT_OBSERVATION`.
- **Diagnosis**: Prompt chưa đủ ràng buộc nên model bịa hạn chế API.
- **Solution**: Cập nhật system prompt: bắt buộc dựa vào Observation, không tự chế nguyên nhân kỹ thuật.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: ReAct giúp tách suy luận và thu thập dữ liệu, giảm trả lời “ảo”.
2. **Reliability**: Agent có thể giảm ổn định khi tool timeout hoặc quota API bị giới hạn.
3. **Observation**: Observation đóng vai trò “mặt đất sự thật”, giúp agent chỉnh chiến lược bước tiếp theo.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Thêm tầng cache weather theo city/time.
- **Safety**: Chuẩn hóa message lỗi thân thiện nhưng trung thực dữ liệu.
- **Performance**: Giảm token qua prompt template ngắn hơn cho weather-only.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
