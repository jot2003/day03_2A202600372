# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Hoàng Kim Trí Thành
- **Student ID**: 2A202600372
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

- **Modules Implementated**: `src/tools/flights.py`, `src/tools/registry.py`, `app.py`.
- **Code Highlights**:
  - Triển khai tìm vé nâng cao: crawl ưu tiên, fallback API/demo.
  - Bổ sung tool `search_roundtrip_flights`, `search_itinerary_flights`.
  - Cập nhật citation theo nguồn thực tế (crawl/API).
- **Documentation**:
  - Luồng Agent gọi tool qua `registry.py`, parse tham số an toàn, và xuất observation có metadata để LLM tổng hợp câu trả lời.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Lỗi 422 khi tìm chuyến bay dù input nhìn đúng.
- **Log Source**: `logs/YYYY-MM-DD.log` với sự kiện `AGENT_OBSERVATION` chứa lỗi Duffel.
- **Diagnosis**: Parser chưa bóc nháy đơn nên `'SGN'` được gửi nguyên văn thành IATA không hợp lệ.
- **Solution**: Sửa parser để chuẩn hóa cả nháy đơn/nháy kép, thêm test hồi quy trong `tests/test_travel_tools.py`.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: `Thought` giúp LLM chia bài toán thành từng bước rõ ràng và quyết định đúng thời điểm gọi tool.
2. **Reliability**: Agent có thể kém hơn chatbot khi tool lỗi liên tục hoặc prompt quá mơ hồ làm tăng vòng lặp.
3. **Observation**: Observation là tín hiệu phản hồi quan trọng giúp agent tự sửa Action ở bước sau thay vì trả lời đoán.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Tách worker cho tool call bất đồng bộ và cache kết quả truy vấn lặp.
- **Safety**: Thêm lớp kiểm duyệt Action trước khi gọi API ngoài.
- **Performance**: Áp dụng schema output cứng + heuristic giảm số bước loop không cần thiết.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
