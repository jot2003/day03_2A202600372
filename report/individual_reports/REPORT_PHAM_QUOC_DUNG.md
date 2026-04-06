# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Phạm Quốc Dũng
- **Student ID**: 2A202600490
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

- **Modules Implementated**: `tests/test_travel_tools.py`, `src/tools/demo_fallback.py`, `.env.example`.
- **Code Highlights**:
  - Bổ sung test cho parser, date tự nhiên, roundtrip, itinerary.
  - Chuẩn hóa dữ liệu mock để đồng nhất format với dữ liệu thật.
  - Cập nhật biến môi trường cho tích hợp Duffel và chế độ search.
- **Documentation**:
  - Đảm bảo test phản ánh đúng các case demo và case biên thường gặp.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Một số test date parsing fail do khác format giữa crawl và API.
- **Log Source**: output test local + file log khi chạy scenario tương ứng.
- **Diagnosis**: Assert bám vào trường thời gian thô không ổn định theo nguồn dữ liệu.
- **Solution**: Chuyển assert sang trường chuẩn hóa `departure_date_normalized`, thêm test cho ambiguity note.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Agent có khả năng “tự kiểm tra lại” nhờ vòng lặp và phản hồi từ tool.
2. **Reliability**: Chatbot có thể ổn định hơn với câu hỏi đơn giản vì không phụ thuộc tool.
3. **Observation**: Observation biến sai sót thành dữ liệu học tức thời cho bước kế tiếp.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Thiết lập test matrix tự động theo nhiều provider.
- **Safety**: Thêm test bảo vệ cho input độc hại và format lạ.
- **Performance**: Tạo benchmark CI cho latency/token theo phiên bản prompt.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
