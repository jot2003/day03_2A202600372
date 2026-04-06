# Test Cases Theo Doi Tien Do

Tai lieu nay dung de theo doi tien do kiem thu va commit len GitHub.

## Quy uoc cap nhat
- Cap nhat cot `Trang thai` theo mot trong cac gia tri: `Not Run`, `Pass`, `Fail`, `Blocked`.
- Neu `Fail` hoac `Blocked`, them mo ta ngan trong cot `Ghi chu`.
- Moi lan chay test lon, cap nhat ngay thuc hien o muc "Lich su test run".

## Danh sach test case

| ID | Nhom | Muc tieu | Preconditions | Buoc thuc hien | Ket qua mong doi | Trang thai | Ghi chu |
|---|---|---|---|---|---|---|---|
| TC-001 | Setup | Tao va kich hoat virtual environment | Co Python 3.10+ | 1) Tao `.venv` 2) Kich hoat environment | Lenh kich hoat thanh cong, dung duoc python tu `.venv` | Not Run | |
| TC-002 | Setup | Cai dependencies chinh | Da kich hoat `.venv` | Chay `pip install -r requirements.txt` | Cai dat thanh cong, khong loi package conflict nghiem trong | Not Run | |
| TC-003 | Setup | Kiem tra bien moi truong bat buoc | Co file `.env` | Dien key cho provider va weather/flight theo cau hinh | He thong doc duoc `.env`, khong bao thieu key critical | Not Run | |
| TC-004 | Unit Test | Chay toan bo test tu dong | Da cai dependencies | Chay `python -m pytest -q` | Test suite hoan tat, ket qua duoc ghi nhan ro rang | Not Run | |
| TC-005 | Provider | Khoi dong voi OpenAI provider | `DEFAULT_PROVIDER=openai`, co `OPENAI_API_KEY` | Chay `python main.py` va gui cau hoi ngan | Agent/chatbot phan hoi binh thuong | Not Run | |
| TC-006 | Provider | Khoi dong voi Gemini provider | `DEFAULT_PROVIDER=gemini`, co `GEMINI_API_KEY` | Chay `python main.py` va gui cau hoi ngan | Agent/chatbot phan hoi binh thuong | Not Run | |
| TC-007 | Weather Tool | Tra cuu thoi tiet theo thanh pho | Co `OPENWEATHER_API_KEY` hop le | Hoi: "weather in Da Nang" | Tool weather duoc goi, tra ket qua co nhiet do/mo ta thoi tiet | Not Run | |
| TC-008 | Weather Tool | Ho tro city co dau phay va chuoi co quote | Co key weather hop le | Goi: `Action: get_weather(city='Da Nang, VN')` | Parse dung city, khong vo sai argument | Not Run | |
| TC-009 | Weather Tool | Xu ly du lieu khong tim thay thanh pho | Co key weather hop le | Hoi weather voi city khong ton tai | Tra thong bao loi ro rang, khong crash agent | Not Run | |
| TC-010 | Flights Tool | Tim chuyen bay mot chieu | Co token flight hop le (Duffel) | Hoi tim ve one-way voi ngay hop le | Tra ve danh sach offers/chi phi co nghia | Not Run | |
| TC-011 | Flights Tool | Tim chuyen bay khu hoi | Co token flight hop le | Hoi tim ve roundtrip voi ngay di/ve hop le | Tra ve ket qua roundtrip hoac thong bao fallback ro rang | Not Run | |
| TC-012 | Flights Tool | Xu ly thieu token flight | Khong set token flight | Goi tool flights | Tra loi bao thieu token ro rang, khong crash | Not Run | |
| TC-013 | Budget Tool | Tinh ngan sach chuyen di | Khong can API key | Goi budget voi so ngay, so nguoi, muc chi tieu | Tra bang tong hop ngan sach hop ly | Not Run | |
| TC-014 | Agent Loop | Kiem tra chu trinh Thought-Action-Observation | Da cau hinh provider | Dat cau hoi can dung tool (weather/flight) | Log co cac su kien AGENT_LLM_STEP, AGENT_TOOL_CALL, AGENT_OBSERVATION | Not Run | |
| TC-015 | Agent Robustness | Xu ly output parser loi | Da cau hinh provider | Tao prompt de de phat sinh format sai Action | He thong ghi AGENT_PARSE_ERROR va tiep tuc an toan | Not Run | |
| TC-016 | Logging | Tao file log JSON theo ngay | Chay it nhat 1 session | Kiem tra thu muc `logs/` | Co file `YYYY-MM-DD.log` va moi dong la JSON hop le | Not Run | |
| TC-017 | Reporting | Tong hop log thanh CSV | Co log test tu hom nay | Chay `python scripts/summarize_logs.py` | Tao duoc CSV summary/event/metrics khong loi schema | Not Run | |
| TC-018 | Streamlit UI | Chay giao dien app | Da cai streamlit va dependencies | Chay `python -m streamlit run app.py` | App khoi dong thanh cong, mo duoc tren local URL | Not Run | |
| TC-019 | Streamlit UI | Chuc nang export references | App dang chay, co du lieu log | Thuc hien export tren tab lien quan | File export duoc tao, noi dung khop log | Not Run | |
| TC-020 | Regression | Kiem tra sau khi merge tu main | Repo vua pull tu `origin/main` | Chay lai smoke test + pytest | Khong phat sinh loi cu da fix truoc do | Not Run | |

## Lich su test run

| Ngay | Nguoi chay | Pham vi | Ket qua tong | Ghi chu |
|---|---|---|---|---|
| 2026-04-06 | PHAM_QUOC_DUNG | Init testcase file | N/A | Tao moi file testcase de theo doi tien do |

## Ghi chu de commit
- Them file nay vao commit khi bat dau chu ky test:
  - `git add report/TESTCASES_PROGRESS.md`
  - `git commit -m "Add progress test case checklist"`
  - `git push`
