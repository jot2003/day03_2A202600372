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
                "Thieu package `google-generativeai`.\n\n"
                f'Chay: `"{py}" -m pip install google-generativeai` roi `"{py}" -m streamlit run app.py`'
            ) from e
        raise


def observation_citation_markdown(tool: str, obs_raw: str) -> str:
    """Trich dan nguon de nguoi doc tu kiem chung."""
    try:
        d = json.loads(obs_raw)
    except (json.JSONDecodeError, TypeError):
        return f"**Nguon:** raw observation (khong parse JSON). Tool `{tool}`."

    if d.get("_demo") is True:
        demo_url = d.get("public_weather_page_url")
        demo_link = (
            f" [Minh hoa: trang thoi tiet cung dia diem tren OpenWeather]({demo_url})"
            if demo_url
            else ""
        )
        return (
            "**Nguon (kiem chung):** Du lieu **MO PHONG** trong tool — `DEMO_TRAVEL_APIS=1` hoac thieu key. "
            f"Khong phai snapshot API that.{demo_link} "
            "Ma: `src/tools/demo_fallback.py` — cau hinh: `.env.example`."
        )
    if d.get("error"):
        return (
            f"**Nguon / loi:** `{d.get('error')}` — "
            f"{d.get('hint', '(xem huong dan trong JSON)')}"
        )
    if tool == "get_weather":
        pub = d.get("public_weather_page_url")
        cname = d.get("city") or ""
        cc = d.get("country") or ""
        if d.get("source") == "openweathermap.org/data/2.5" and pub:
            wq = d.get("weather_query") or ""
            return (
                f"**Nguon (kiem chung nhanh):** [Thoi tiet hien tai tai {cname}, {cc} (OpenWeatherMap)]({pub}) "
                f"— trang web cung dia diem voi API (`q` da dung: `{wq}`). "
                "[Tai lieu ky thuat API](https://openweathermap.org/api) — key / loi 401: `docs/OPENWEATHER_SETUP_VI.md`."
            )
        if pub:
            return (
                f"**Nguon:** [Thoi tiet tai {cname}, {cc} (OpenWeatherMap)]({pub}) — "
                "[API docs](https://openweathermap.org/api), ma: `src/tools/weather.py`."
            )
        if d.get("source") == "openweathermap.org/data/2.5":
            return (
                "**Nguon:** [OpenWeatherMap API](https://openweathermap.org/api) — endpoint `data/2.5/weather` + `forecast`. "
                "Huong dan key / loi 401: `docs/OPENWEATHER_SETUP_VI.md`."
            )
        return (
            "**Nguon:** [OpenWeatherMap](https://openweathermap.org/api) — xem `src/tools/weather.py`."
        )
    if tool == "search_flights":
        return (
            "**Nguon:** [Amadeus Self-Service — Flight Offers Search](https://developers.amadeus.com/self-service), "
            "Test API trong `src/tools/flights.py`."
        )
    if tool == "calculate_travel_budget":
        return "**Nguon:** Tinh toan cuc bo (Python), khong goi API ngoai — `src/tools/budget.py`."

    return f"**Nguon:** Ket qua tool `{tool}`; doi chieu voi ma trong `src/tools/`."


def _render_agent_step(ev: dict) -> None:
    """Hien thi mot su kien tu iter_run (Streamlit)."""
    k = ev.get("kind")
    if k == "start":
        st.caption(f"Model: `{ev.get('model', '')}`")
    elif k == "llm_step":
        st.markdown(f"##### Buoc {ev.get('step', '')} — LLM")
        st.code(ev.get("content") or "", language="markdown")
    elif k == "parse_error":
        st.warning(
            f"Khong parse duoc Action o buoc {ev.get('step', '')} — agent se thu lai trong buoc tiep theo."
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


def main() -> None:
    load_dotenv(ROOT / ".env", override=True)

    st.set_page_config(
        page_title="Lab 3 — Travel Agent",
        page_icon="✈️",
        layout="wide",
    )

    tab_run, tab_export, tab_refs = st.tabs(["Chay thu (Agent / Chatbot)", "Bao cao & xuat CSV", "Nguon & rubric"])

    presets = load_preset_questions()
    default_fallback = (
        "I want to fly from Hanoi (HAN) to Da Nang (DAD) on 2026-04-15. "
        "Budget 8000000 VND total for 2 nights, hotel 900000 VND per night. "
        "Check weather in Da Nang and flight prices, then say if the budget works."
    )

    with tab_run:
        st.title("Lab 3: Chatbot vs ReAct Agent")
        st.caption("Chu de du lich — chon cau hoi mau hoac tu nhap; moi buoc trace kem **trich dan nguon**.")

        if "main_question_text" not in st.session_state:
            st.session_state.main_question_text = (
                presets[0]["question"] if presets else default_fallback
            )

        with st.sidebar:
            st.subheader("Cau hinh")
            mode = st.radio(
                "Che do",
                options=["agent", "chatbot"],
                format_func=lambda x: "ReAct Agent (co tools)" if x == "agent" else "Chatbot baseline (khong tools)",
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
            st.caption(f"Model .env: `{os.getenv('DEFAULT_MODEL', '')}`")

        st.subheader("Bo cau hoi mau")
        selected_preset = None
        if not presets:
            st.warning("Thieu `data/preset_questions.json`. Hay pull repo day du.")
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
                st.markdown("**Tai lieu kiem chung (ngoai repo):** " + refs_md)

        st.subheader("Noi dung se gui cho LLM")
        question = st.text_area(
            "Sua tai day neu can (tieng Anh hoac Viet deu duoc)",
            height=150,
            key="main_question_text",
        )

        log_today = ROOT / "logs" / f"{datetime.now():%Y-%m-%d}.log"
        st.markdown(
            f"**Log JSON hom nay (de doi chieu trace):** `{log_today.resolve()}`  \n"
            "*Moi su kien AGENT_*, LLM_METRIC ghi trong file nay — mo bang VS Code / Notepad.*"
        )

        if st.button("Chay", type="primary"):
            q = question.strip()
            if not q:
                st.warning("Nhap cau hoi.")
            else:
                try:
                    llm = _cached_llm(_llm_resource_cache_key())
                except RuntimeError as e:
                    st.markdown(str(e))
                except Exception as e:
                    st.error(f"LLM: {e}")
                else:
                    if mode == "chatbot":
                        with st.spinner("Dang xu ly (chatbot)..."):
                            bot = TravelChatbotBaseline(llm)
                            answer = bot.reply(q)
                        st.subheader("Tra loi (chatbot)")
                        st.markdown(answer)
                    else:
                        agent = ReActAgent(llm, get_tool_specs(), max_steps=int(max_steps))
                        answer = ""
                        status_ctx = getattr(st, "status", None)
                        if status_ctx is not None:
                            with st.status("Agent ReAct dang chay (streaming tung buoc)...", expanded=True) as status:
                                for ev in agent.iter_run(q):
                                    _render_agent_step(ev)
                                    if ev.get("kind") == "final":
                                        answer = ev.get("text") or ""
                                        status.update(label="Hoan thanh", state="complete")
                                    elif ev.get("kind") == "max_steps":
                                        answer = ev.get("text") or ""
                                        status.update(label="Dung sau so buoc toi da", state="error")
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

                        st.subheader("Ket qua (agent)")
                        st.markdown(answer)

                        if agent.history:
                            with st.expander("Trace ReAct + trich dan nguon (tom tat)", expanded=False):
                                for h in agent.history:
                                    st.markdown(f"##### Buoc {h['step']}")
                                    st.markdown("**LLM (raw)**")
                                    st.code(h.get("llm", "") or "", language="markdown")
                                    if h.get("final"):
                                        st.success("Co Final Answer trong khoi tren.")
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
                            st.success("Da cap nhat CSV trong `report/exports/` (xem tab Bao cao).")
                        else:
                            st.warning(exp["messages"][0] if exp["messages"] else "Chua xuat duoc CSV.")

    with tab_export:
        st.header("Bao cao & xuat file")
        st.markdown(
            "Thu muc output: `report/exports/` (gitignore — ban copy CSV vao bao cao nhom neu can).  \n"
            "Script CLI tuong duong: `python scripts/summarize_logs.py`"
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Lam moi CSV tu logs/ hien tai"):
                exp = run_export_summaries()
                st.session_state["last_export"] = exp
                for m in exp["messages"]:
                    st.write(m)
        with c2:
            st.markdown("Sau khi chay agent/chatbot (hoac nut ben trai), kiem tra file:")

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
                st.caption(f"Cap nhat: {datetime.fromtimestamp(fp.stat().st_mtime).isoformat(sep=' ', timespec='seconds')}")
            else:
                st.caption(f"{fname}: (chua co — chay agent hoac nut Lam moi)")

        st.divider()
        st.subheader("Feedback cho nhom / GV")
        st.markdown("Ghi y kien hoac loi phat hien; luu vao `report/ui_feedback.md` trong repo (co the commit).")
        fb = st.text_area("Noi dung feedback", height=120, key="fb_text")
        fb_name = st.text_input("Ten / vai tro (tuy chon)", key="fb_name")
        if st.button("Ghi feedback vao report/ui_feedback.md"):
            if fb.strip():
                path = append_feedback(ROOT, fb, context=fb_name.strip() or "Streamlit UI")
                st.success(f"Da ghi: `{path.relative_to(ROOT)}` — vui long commit / gui PR.")
            else:
                st.warning("Feedback trong.")

    with tab_refs:
        st.markdown(
            """
### Rubric & tai lieu lab (kiem chung)

- [SCORING.md — diem nhom + ca nhan](https://github.com/VinUni-AI20k/Day-3-Lab-Chatbot-vs-react-agent/blob/main/SCORING.md)
- [EVALUATION.md — metrics](https://github.com/VinUni-AI20k/Day-3-Lab-Chatbot-vs-react-agent/blob/main/EVALUATION.md)
- [INSTRUCTOR_GUIDE.md](https://github.com/VinUni-AI20k/Day-3-Lab-Chatbot-vs-react-agent/blob/main/INSTRUCTOR_GUIDE.md)

### API ngoai (du lieu thuc, khong phai demo)

- [Gemini API / Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [Amadeus for Developers](https://developers.amadeus.com/)

### Trong repo (ma nguon)

- Preset cau hoi: `data/preset_questions.json`
- Tools: `src/tools/` — `weather.py`, `flights.py`, `budget.py`, `demo_fallback.py`
- Agent ReAct: `src/agent/agent.py`
- Tong hop log: `src/reporting/log_summary.py`, `scripts/summarize_logs.py`
- Checklist viec: `report/VIEC_CAN_LAM.md`
"""
        )


if __name__ == "__main__":
    main()
