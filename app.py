"""
Giao diện Streamlit: câu hỏi mẫu + tự nhập, chạy agent/chatbot, xuất CSV, trích dẫn nguồn.

  python -m streamlit run app.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from src.agent.agent import ReActAgent
from src.chatbot import TravelChatbotBaseline
from src.core.provider_factory import build_llm_from_env
from src.reporting.log_summary import append_feedback, summarize_logs_to_csv
from src.tools.registry import get_tool_specs

_LLM_CACHE_VERSION = "v4-keyed-cache"


@st.cache_data
def load_preset_questions() -> list:
    path = ROOT / "data" / "preset_questions.json"
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _llm_resource_cache_key() -> tuple:
    load_dotenv(ROOT / ".env", override=True)
    key = os.getenv("GEMINI_API_KEY", "") or ""
    hint = (key[:12] + key[-8:]) if len(key) > 20 else key
    return (
        os.getenv("DEFAULT_PROVIDER", "google"),
        os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
        hint,
        _LLM_CACHE_VERSION,
    )


@st.cache_resource
def _cached_llm(_cache_key: tuple):
    try:
        return build_llm_from_env()
    except ModuleNotFoundError as e:
        name = (e.name or str(e)).lower()
        if "google" in name or "generativeai" in str(e).lower():
            py = sys.executable
            raise RuntimeError(
                "Thiếu package `google-generativeai`.\n\n"
                f'Chay: `"{py}" -m pip install google-generativeai` roi `"{py}" -m streamlit run app.py`'
            ) from e
        raise


def observation_citation_markdown(tool: str, obs_raw: str) -> str:
    """Trích dẫn nguồn để người đọc tự kiểm chứng."""
    try:
        d = json.loads(obs_raw)
    except (json.JSONDecodeError, TypeError):
        return f"**Nguồn:** raw observation (không parse JSON). Tool `{tool}`."

    if d.get("_demo") is True:
        demo_url = d.get("public_weather_page_url")
        demo_link = (
            f" [Minh hoa: trang thoi tiet cung dia diem tren OpenWeather]({demo_url})"
            if demo_url
            else ""
        )
        return (
            "**Nguồn (kiểm chứng):** Dữ liệu **MÔ PHỎNG** trong tool — `DEMO_TRAVEL_APIS=1` hoặc thiếu key. "
            f"Không phải snapshot API thật.{demo_link} "
            "Mã: `src/tools/demo_fallback.py` — cấu hình: `.env.example`."
        )
    if d.get("error"):
        return (
            f"**Nguồn / lỗi:** `{d.get('error')}` — "
            f"{d.get('hint', '(xem huong dan trong JSON)')}"
        )
    if tool == "get_weather":
        pub = d.get("public_weather_page_url")
        cname = d.get("city") or ""
        cc = d.get("country") or ""
        if d.get("source") == "openweathermap.org/data/2.5" and pub:
            wq = d.get("weather_query") or ""
            return (
                f"**Nguồn (kiểm chứng nhanh):** [Thời tiết hiện tại tại {cname}, {cc} (OpenWeatherMap)]({pub}) "
                f"— trang cùng địa điểm với dữ liệu API (`q` đã dùng: `{wq}`). "
                "[Tài liệu kỹ thuật API](https://openweathermap.org/api) — hướng dẫn key / lỗi 401: `docs/OPENWEATHER_SETUP_VI.md`."
            )
        if pub:
            return (
                f"**Nguồn:** [Thời tiết tại {cname}, {cc} (OpenWeatherMap)]({pub}) — "
                "[API docs](https://openweathermap.org/api), ma: `src/tools/weather.py`."
            )
        if d.get("source") == "openweathermap.org/data/2.5":
            return (
                "**Nguồn:** [OpenWeatherMap API](https://openweathermap.org/api) — endpoint `data/2.5/weather` + `forecast`. "
                "Hướng dẫn key / lỗi 401: `docs/OPENWEATHER_SETUP_VI.md`."
            )
        return (
            "**Nguồn:** [OpenWeatherMap](https://openweathermap.org/api) — xem `src/tools/weather.py`."
        )
    if tool in {"search_flights", "search_roundtrip_flights", "search_itinerary_flights"}:
        src = d.get("source")
        if src == "fast_flights_crawl":
            curl = d.get("crawl_source_url")
            crawl_link = f"[Trang dữ liệu crawl]({curl})" if curl else "Không có crawl_source_url."
            return (
                f"**Nguồn (ưu tiên crawl):** {crawl_link}. "
                "[Thu vien fast-flights](https://pypi.org/project/fast-flights/) "
                "(có thể lệch nhẹ theo thời điểm crawl)."
            )
        req_id = d.get("duffel_offer_request_id")
        req_url = d.get("duffel_offer_request_url")
        public_url = d.get("public_search_url")
        if not req_url and tool == "search_roundtrip_flights":
            out_r = d.get("outbound") or {}
            in_r = d.get("inbound") or {}
            # Prioritize crawl citation if any leg uses crawl mode
            if (out_r.get("source") == "fast_flights_crawl") or (in_r.get("source") == "fast_flights_crawl"):
                first = out_r if out_r.get("source") == "fast_flights_crawl" else in_r
                curl = first.get("crawl_source_url")
                crawl_link = f"[Trang dữ liệu crawl]({curl})" if curl else "Không có crawl_source_url."
                return (
                    f"**Nguồn (ưu tiên crawl):** {crawl_link}. "
                    "[Thư viện fast-flights](https://pypi.org/project/fast-flights/)."
                )
            req_url = out_r.get("duffel_offer_request_url") or in_r.get("duffel_offer_request_url")
            req_id = out_r.get("duffel_offer_request_id") or in_r.get("duffel_offer_request_id")
            public_url = out_r.get("public_search_url") or in_r.get("public_search_url")
        if not req_url and tool == "search_itinerary_flights":
            for leg in d.get("legs") or []:
                rr = (leg.get("result") or {})
                if rr.get("source") == "fast_flights_crawl":
                    curl = rr.get("crawl_source_url")
                    crawl_link = f"[Trang dữ liệu crawl]({curl})" if curl else "Không có crawl_source_url."
                    return (
                        f"**Nguồn (ưu tiên crawl):** {crawl_link}. "
                        "[Thư viện fast-flights](https://pypi.org/project/fast-flights/)."
                    )
                req_url = rr.get("duffel_offer_request_url")
                req_id = rr.get("duffel_offer_request_id")
                public_url = rr.get("public_search_url")
                if req_url:
                    break
        req_info = f" (offer_request_id: `{req_id}`)" if req_id else ""
        realtime = (
            f"[Du lieu realtime cua lan tim nay]({req_url}) (can `Authorization: Bearer ...` de xem JSON)"
            if req_url
            else "Không có `offer_request_id`, nên không tạo được link tài nguyên realtime."
        )
        public_verify = (
            f"[Mở kết quả tìm kiếm công khai (Google Flights)]({public_url})"
            if public_url
            else "Không tạo được deep-link công khai."
        )
        return (
            f"**Nguồn:** {public_verify}. {realtime}{req_info}. "
            "[Tài liệu endpoint tạo offer request](https://duffel.com/docs/api/offer-requests/create-offer-request). "
            "Chi tiết gọi API trong `src/tools/flights.py`."
        )
    if tool == "calculate_travel_budget":
        return "**Nguồn:** Tính toán cục bộ (Python), không gọi API ngoài — `src/tools/budget.py`."

    return f"**Nguồn:** Kết quả tool `{tool}`; đối chiếu với mã trong `src/tools/`."


def _render_agent_step(ev: dict) -> None:
    """Hiển thị một sự kiện từ iter_run (Streamlit)."""
    k = ev.get("kind")
    if k == "start":
        st.caption(f"Model: `{ev.get('model', '')}`")
    elif k == "llm_step":
        st.markdown(f"##### Buoc {ev.get('step', '')} — LLM")
        st.code(ev.get("content") or "", language="markdown")
    elif k == "parse_error":
        st.warning(
            f"Không parse được Action ở bước {ev.get('step', '')} — agent sẽ thử lại trong bước tiếp theo."
        )
        st.code(ev.get("content") or "", language="markdown")
    elif k == "tool":
        step = ev.get("step", "")
        tool = ev.get("tool", "")
        obs = ev.get("observation") or ""
        st.markdown(f"##### Buoc {step} — Tool `{tool}`")
        st.markdown(observation_citation_markdown(tool, obs))
        try:
            st.json(json.loads(obs))
        except (json.JSONDecodeError, TypeError):
            st.text(obs)
    elif k == "final":
        st.success(f"Final Answer (buoc {ev.get('step', '')})")
    elif k == "max_steps":
        st.error(ev.get("text") or "Max steps")


def run_export_summaries() -> dict:
    log_dir = ROOT / "logs"
    out_dir = ROOT / "report" / "exports"
    return summarize_logs_to_csv(log_dir, out_dir, "*.log")


def _render_answer_feedback(question: str, answer: str, mode: str) -> None:
    """Nhận feedback ngay sau mỗi câu trả lời để phục vụ review nhanh."""
    st.divider()
    st.markdown("### Danh gia cau tra loi")
    c1, c2 = st.columns([1, 1])
    with c1:
        quick = st.radio(
            "Danh gia nhanh",
            options=["👍 Tốt", "👎 Chưa tốt"],
            horizontal=True,
            key=f"quick_fb_{mode}",
        )
    with c2:
        score = st.slider("Diem chat luong (1-5)", min_value=1, max_value=5, value=4, key=f"score_fb_{mode}")

    note = st.text_area(
        "Nhan xet chi tiet (tu chon)",
        height=90,
        key=f"note_fb_{mode}",
        placeholder="Vi du: thong tin day du, can cu ro rang, hoac con thieu chi tiet...",
    )
    if st.button("Lưu feedback cho câu trả lời này", key=f"save_fb_{mode}"):
        payload = (
            f"- mode: {mode}\n"
            f"- quick: {quick}\n"
            f"- score_1_5: {score}\n"
            f"- question: {question.strip()[:500]}\n"
            f"- answer_preview: {(answer or '').strip()[:1500]}\n"
            f"- note: {(note or '').strip()}\n"
        )
        p = append_feedback(ROOT, payload, context="Answer Review")
        st.success(f"Da luu feedback: `{p.relative_to(ROOT)}`")


def main() -> None:
    load_dotenv(ROOT / ".env", override=True)

    st.set_page_config(
        page_title="Lab 3 — Travel Agent",
        page_icon="✈️",
        layout="wide",
    )

    tab_run, tab_export, tab_refs = st.tabs(["Chạy thử (Agent / Chatbot)", "Báo cáo & xuất CSV", "Nguồn & rubric"])

    presets = load_preset_questions()
    default_fallback = (
        "I want to fly from Hanoi (HAN) to Da Nang (DAD) on 2026-04-15. "
        "Budget 8000000 VND total for 2 nights, hotel 900000 VND per night. "
        "Check weather in Da Nang and flight prices, then say if the budget works."
    )

    with tab_run:
        st.title("Lab 3: Chatbot vs ReAct Agent")
        st.caption("Chủ đề du lịch — chọn câu hỏi mẫu hoặc tự nhập; mỗi bước trace kèm **trích dẫn nguồn**.")

        if "main_question_text" not in st.session_state:
            st.session_state.main_question_text = (
                presets[0]["question"] if presets else default_fallback
            )

        with st.sidebar:
            st.subheader("Cấu hình")
            mode = st.radio(
                "Chế độ",
                options=["agent", "chatbot"],
                format_func=lambda x: "ReAct Agent (có tools)" if x == "agent" else "Chatbot baseline (không tools)",
                index=0,
            )
            max_steps = st.number_input(
                "Agent: so buoc toi da",
                min_value=1,
                max_value=24,
                value=int(os.getenv("AGENT_MAX_STEPS", "8")),
            )
            auto_csv = st.checkbox("Tu dong cap nhat CSV sau khi chay xong", value=True)
            st.divider()
            if st.button("Xoa cache LLM & tai lai"):
                st.cache_resource.clear()
                st.rerun()
            st.caption(f"Python: `{sys.executable}`")
            st.caption(f"Model trong .env: `{os.getenv('DEFAULT_MODEL', '')}`")

        st.subheader("Bộ câu hỏi mẫu")
        selected_preset = None
        if not presets:
                st.warning("Thiếu `data/preset_questions.json`. Hãy pull repo đầy đủ.")
        else:
            preset_titles = [p["title"] for p in presets]
            sel_title = st.selectbox("Chon kich ban", preset_titles, key="preset_title_pick")
            selected_preset = next(p for p in presets if p["title"] == sel_title)
            if st.session_state.get("_last_preset_title") != sel_title:
                st.session_state.main_question_text = selected_preset["question"]
                st.session_state._last_preset_title = sel_title
            st.info(selected_preset.get("notes_vi", ""))
            refs_md = "\n".join(
                f"- [{r['label']}]({r['url']})" for r in selected_preset.get("references", [])
            )
            if refs_md:
                st.markdown("**Tài liệu kiểm chứng (ngoài repo):** " + refs_md)

        st.subheader("Nội dung sẽ gửi cho LLM")
        question = st.text_area(
            "Sửa tại đây nếu cần (tiếng Anh hoặc Việt đều được)",
            height=150,
            key="main_question_text",
        )

        log_today = ROOT / "logs" / f"{datetime.now():%Y-%m-%d}.log"
        st.markdown(
            f"**Log JSON hôm nay (để đối chiếu trace):** `{log_today.resolve()}`  \n"
            "*Mọi sự kiện AGENT_*, LLM_METRIC ghi trong file này — mở bằng VS Code / Notepad.*"
        )

        if st.button("Chay", type="primary"):
            q = question.strip()
            if not q:
                st.warning("Nhập câu hỏi.")
            else:
                try:
                    llm = _cached_llm(_llm_resource_cache_key())
                except RuntimeError as e:
                    st.markdown(str(e))
                except Exception as e:
                    st.error(f"LLM: {e}")
                else:
                    if mode == "chatbot":
                        with st.spinner("Đang xử lý (chatbot)..."):
                            bot = TravelChatbotBaseline(llm)
                            answer = bot.reply(q)
                        st.subheader("Trả lời (chatbot)")
                        st.markdown(answer)
                        _render_answer_feedback(q, answer, "chatbot")
                    else:
                        agent = ReActAgent(llm, get_tool_specs(), max_steps=int(max_steps))
                        answer = ""
                        status_ctx = getattr(st, "status", None)
                        if status_ctx is not None:
                            with st.status("Agent ReAct đang chạy (streaming từng bước)...", expanded=True) as status:
                                for ev in agent.iter_run(q):
                                    _render_agent_step(ev)
                                    if ev.get("kind") == "final":
                                        answer = ev.get("text") or ""
                                        status.update(label="Hoàn thành", state="complete")
                                    elif ev.get("kind") == "max_steps":
                                        answer = ev.get("text") or ""
                                        status.update(label="Dừng sau số bước tối đa", state="error")
                        else:
                            trace_ph = st.empty()
                            chunk: list = []
                            for ev in agent.iter_run(q):
                                chunk.append(ev)
                                with trace_ph.container():
                                    for e in chunk:
                                        _render_agent_step(e)
                                if ev.get("kind") == "final":
                                    answer = ev.get("text") or ""
                                elif ev.get("kind") == "max_steps":
                                    answer = ev.get("text") or ""

                        st.subheader("Kết quả (agent)")
                        st.markdown(answer)
                        _render_answer_feedback(q, answer, "agent")

                        if agent.history:
                            with st.expander("Trace ReAct + trích dẫn nguồn (tóm tắt)", expanded=False):
                                for h in agent.history:
                                    st.markdown(f"##### Buoc {h['step']}")
                                    st.markdown("**LLM (raw)**")
                                    st.code(h.get("llm", "") or "", language="markdown")
                                    if h.get("final"):
                                        st.success("Có Final Answer trong khối trên.")
                                    if h.get("tool"):
                                        st.markdown(f"**Tool:** `{h['tool']}`")
                                        st.markdown(
                                            observation_citation_markdown(h["tool"], h.get("observation") or "")
                                        )
                                        obs = h.get("observation") or ""
                                        try:
                                            st.json(json.loads(obs))
                                        except (json.JSONDecodeError, TypeError):
                                            st.text(obs)

                    if auto_csv:
                        exp = run_export_summaries()
                        st.session_state["last_export"] = exp
                        if exp["ok"]:
                            st.success("Đã cập nhật CSV trong `report/exports/` (xem tab Báo cáo).")
                        else:
                            st.warning(exp["messages"][0] if exp["messages"] else "Chưa xuất được CSV.")

    with tab_export:
        st.header("Báo cáo & xuất file")
        st.markdown(
            "Thư mục output: `report/exports/` (gitignore — bạn copy CSV vào báo cáo nhóm nếu cần).  \n"
            "Script CLI tương đương: `python scripts/summarize_logs.py`"
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Làm mới CSV từ logs hiện tại"):
                exp = run_export_summaries()
                st.session_state["last_export"] = exp
                for m in exp["messages"]:
                    st.write(m)
        with c2:
            st.markdown("Sau khi chạy agent/chatbot (hoặc nút bên trái), kiểm tra file:")

        out_dir = ROOT / "report" / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, fname in [
            ("LLM metrics", "llm_metrics.csv"),
            ("Sessions", "sessions_summary.csv"),
            ("Event counts", "event_counts.csv"),
        ]:
            fp = out_dir / fname
            if fp.is_file():
                st.download_button(
                    label=f"Tai ve {fname}",
                    data=fp.read_bytes(),
                    file_name=fname,
                    mime="text/csv",
                    key=f"dl_{fname}",
                )
                st.caption(f"Cập nhật: {datetime.fromtimestamp(fp.stat().st_mtime).isoformat(sep=' ', timespec='seconds')}")
            else:
                st.caption(f"{fname}: (chưa có — chạy agent hoặc nút Làm mới)")

        st.divider()
        st.subheader("Feedback cho nhóm / GV")
        st.markdown("Ghi ý kiến hoặc lỗi phát hiện; lưu vào `report/ui_feedback.md` trong repo (có thể commit).")
        fb = st.text_area("Nội dung feedback", height=120, key="fb_text")
        fb_name = st.text_input("Tên / vai trò (tùy chọn)", key="fb_name")
        if st.button("Ghi feedback vao report/ui_feedback.md"):
            if fb.strip():
                path = append_feedback(ROOT, fb, context=fb_name.strip() or "Streamlit UI")
                st.success(f"Đã ghi: `{path.relative_to(ROOT)}` — vui lòng commit / gửi PR.")
            else:
                st.warning("Feedback trống.")

    with tab_refs:
        st.markdown(
            """
### Rubric & tài liệu lab (kiểm chứng)

- [SCORING.md — diem nhom + ca nhan](https://github.com/VinUni-AI20k/Day-3-Lab-Chatbot-vs-react-agent/blob/main/SCORING.md)
- [EVALUATION.md — metrics](https://github.com/VinUni-AI20k/Day-3-Lab-Chatbot-vs-react-agent/blob/main/EVALUATION.md)
- [INSTRUCTOR_GUIDE.md](https://github.com/VinUni-AI20k/Day-3-Lab-Chatbot-vs-react-agent/blob/main/INSTRUCTOR_GUIDE.md)

### API ngoài (dữ liệu thực, không phải demo)

- [Gemini API / Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [Duffel API](https://duffel.com/docs/api/overview)

### Trong repo (mã nguồn)

- Preset câu hỏi: `data/preset_questions.json`
- Tools: `src/tools/` — `weather.py`, `flights.py`, `budget.py`, `demo_fallback.py`
- Agent ReAct: `src/agent/agent.py`
- Tổng hợp log: `src/reporting/log_summary.py`, `scripts/summarize_logs.py`
- Checklist việc: `report/VIEC_CAN_LAM.md`
"""
        )


if __name__ == "__main__":
    main()
