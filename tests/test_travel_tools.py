import json
import os
from datetime import date, timedelta
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.tools.registry import execute_tool, get_tool_specs


def test_get_tool_specs_has_three_tools():
    specs = get_tool_specs()
    names = {s["name"] for s in specs}
    assert names == {
        "get_weather",
        "search_flights",
        "search_roundtrip_flights",
        "search_itinerary_flights",
        "calculate_travel_budget",
    }


def test_calculate_travel_budget_execute():
    raw = execute_tool(
        "calculate_travel_budget",
        "8000000, 2400000, 900000, 2",
    )
    data = json.loads(raw)
    assert data["remaining_vnd"] == 8000000 - 2400000 - 1800000
    assert data["feasible"] is True


def test_calculate_travel_budget_keyword_style():
    """LLM (Gemini) hay in Action: calculate_travel_budget(a=1, b=2, ...)."""
    raw = execute_tool(
        "calculate_travel_budget",
        "total_budget_vnd=8000000, flight_cost_vnd=1250000, hotel_per_night_vnd=900000, num_nights=2",
    )
    data = json.loads(raw)
    assert "error" not in data
    assert data["remaining_vnd"] == 8000000 - 1250000 - 1800000


def test_search_flights_keyword_style():
    raw = execute_tool(
        "search_flights",
        "origin=HAN, destination=DAD, departure_date=2026-04-20",
    )
    data = json.loads(raw)
    assert "error" not in data or "Duffel" in data.get("error", "")


def test_search_flights_single_quoted_keyword_style():
    raw = execute_tool(
        "search_flights",
        "origin='HAN', destination='DAD', departure_date='2026-04-20'",
    )
    data = json.loads(raw)
    # Quan trong: parser phai bo dau nhay don, khong duoc loi expected args.
    assert "expected 3 args" not in data.get("error", "")


def test_search_flights_accepts_natural_date_with_demo():
    old = os.environ.get("DEMO_TRAVEL_APIS")
    os.environ["DEMO_TRAVEL_APIS"] = "1"
    try:
        raw = execute_tool(
            "search_flights",
            "origin=HAN, destination=DAD, departure_date=tomorrow",
        )
        data = json.loads(raw)
        assert "offers" in data
    finally:
        if old is None:
            os.environ.pop("DEMO_TRAVEL_APIS", None)
        else:
            os.environ["DEMO_TRAVEL_APIS"] = old


def test_search_flights_invalid_date_returns_hint():
    raw = execute_tool(
        "search_flights",
        "origin=HAN, destination=DAD, departure_date=next someday",
    )
    data = json.loads(raw)
    assert data.get("error") == "Invalid departure_date format"


def test_search_flights_understands_next_week_phrase_with_demo():
    old = os.environ.get("DEMO_TRAVEL_APIS")
    os.environ["DEMO_TRAVEL_APIS"] = "1"
    try:
        raw = execute_tool(
            "search_flights",
            "origin=HAN, destination=DAD, departure_date=ngay nay tuan sau",
        )
        data = json.loads(raw)
        assert "offers" in data
        expected = (date.today() + timedelta(days=7)).isoformat()
        assert data["offers"][0]["departure_at"].startswith(expected)
    finally:
        if old is None:
            os.environ.pop("DEMO_TRAVEL_APIS", None)
        else:
            os.environ["DEMO_TRAVEL_APIS"] = old


def test_search_flights_understands_weekday_phrase_with_demo():
    old = os.environ.get("DEMO_TRAVEL_APIS")
    os.environ["DEMO_TRAVEL_APIS"] = "1"
    try:
        raw = execute_tool(
            "search_flights",
            "origin=HAN, destination=DAD, departure_date=next monday",
        )
        data = json.loads(raw)
        assert "offers" in data
        assert "T" in data["offers"][0]["departure_at"]
    finally:
        if old is None:
            os.environ.pop("DEMO_TRAVEL_APIS", None)
        else:
            os.environ["DEMO_TRAVEL_APIS"] = old


def test_search_flights_marks_ambiguous_weekend_phrase():
    old = os.environ.get("DEMO_TRAVEL_APIS")
    os.environ["DEMO_TRAVEL_APIS"] = "1"
    try:
        raw = execute_tool(
            "search_flights",
            "origin=HAN, destination=DAD, departure_date=cuoi tuan sau",
        )
        data = json.loads(raw)
        assert "offers" in data
        assert data.get("departure_date_ambiguous") is True
        assert len(data.get("departure_date_candidates") or []) == 2
    finally:
        if old is None:
            os.environ.pop("DEMO_TRAVEL_APIS", None)
        else:
            os.environ["DEMO_TRAVEL_APIS"] = old


def test_search_flights_marks_ambiguous_or_phrase():
    old = os.environ.get("DEMO_TRAVEL_APIS")
    os.environ["DEMO_TRAVEL_APIS"] = "1"
    try:
        raw = execute_tool(
            "search_flights",
            "origin=HAN, destination=DAD, departure_date=next friday or saturday",
        )
        data = json.loads(raw)
        assert "offers" in data
        assert data.get("departure_date_ambiguous") is True
        assert len(data.get("departure_date_candidates") or []) >= 2
    finally:
        if old is None:
            os.environ.pop("DEMO_TRAVEL_APIS", None)
        else:
            os.environ["DEMO_TRAVEL_APIS"] = old


def test_search_roundtrip_flights_with_demo():
    old = os.environ.get("DEMO_TRAVEL_APIS")
    os.environ["DEMO_TRAVEL_APIS"] = "1"
    try:
        raw = execute_tool(
            "search_roundtrip_flights",
            "origin=HAN, destination=DAD, departure_date=tomorrow, return_date=in 3 days",
        )
        data = json.loads(raw)
        assert data.get("type") == "roundtrip"
        assert "outbound" in data and "inbound" in data
    finally:
        if old is None:
            os.environ.pop("DEMO_TRAVEL_APIS", None)
        else:
            os.environ["DEMO_TRAVEL_APIS"] = old


def test_search_itinerary_flights_with_demo():
    old = os.environ.get("DEMO_TRAVEL_APIS")
    os.environ["DEMO_TRAVEL_APIS"] = "1"
    try:
        raw = execute_tool(
            "search_itinerary_flights",
            "segments_text=\"HAN-DAD:tomorrow; DAD-SGN:next monday; SGN-HAN:2026-05-20\"",
        )
        data = json.loads(raw)
        assert data.get("type") == "itinerary"
        assert data.get("num_legs") == 3
        assert len(data.get("legs") or []) == 3
    finally:
        if old is None:
            os.environ.pop("DEMO_TRAVEL_APIS", None)
        else:
            os.environ["DEMO_TRAVEL_APIS"] = old


def test_unknown_tool():
    raw = execute_tool("fake_tool", "")
    data = json.loads(raw)
    assert "error" in data


def test_get_weather_city_with_comma_is_single_argument():
    raw = execute_tool("get_weather", "Da Nang, VN")
    data = json.loads(raw)
    # Tool parser khong duoc tach city thanh 2 args.
    assert "expected 1 args, got 2" not in data.get("error", "")
