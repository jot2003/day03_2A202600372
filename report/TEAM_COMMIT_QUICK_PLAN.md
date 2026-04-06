# Kế hoạch nhanh: mỗi thành viên 1 commit thật

Mục tiêu: hoàn tất yêu cầu “mỗi thành viên có ít nhất 1 commit” trong repo team, không giả mạo danh tính.

## 1) Cách làm chung cho từng thành viên

1. `git pull`
2. Sửa **1 thay đổi nhỏ nhưng hợp lệ** theo phân công dưới.
3. `git add <file>`
4. `git commit -m "docs(personal): update <ten_thanh_vien> contribution note"`
5. `git push`

> Lưu ý: commit phải được tạo bằng tài khoản/tên thật của chính thành viên đó.

## 2) Phân công thay đổi siêu nhanh (gợi ý)

- **Hoàng Kim Trí Thành**: cập nhật 1 dòng insight trong `report/Lab3__C401-E3.md` (mục B.1).
- **Đặng Đình Tú Anh**: cập nhật 1 dòng future improvement trong `report/Lab3__C401-E3.md` (mục B.2).
- **Quách Gia Được**: cập nhật 1 dòng technical contribution trong `report/Lab3__C401-E3.md` (mục B.3).
- **Phạm Quốc Dũng**: cập nhật 1 dòng testing note trong `report/Lab3__C401-E3.md` (mục B.4).
- **Nguyễn Thành Nam**: cập nhật 1 dòng telemetry note trong `report/Lab3__C401-E3.md` (mục B.5).

## 3) Check nhanh sau khi xong

- `git shortlog -sne HEAD` phải thấy đủ tên/email các thành viên.
- Không commit `.env`.
- Nội dung report vẫn thống nhất và không xung đột.
