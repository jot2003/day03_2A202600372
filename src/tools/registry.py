import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.tools.budget import calculate_travel_budget
from src.tools.flights import search_flights, search_itinerary_flights, search_roundtrip_flights
from src.tools.weather import get_weather

ToolFn = Callable[..., str]

_REGISTRY: Dict[str, Tuple[ToolFn, List[str]]] = {
    "get_weather": (get_weather, ["city"]),
    "search_flights": (search_flights, ["origin", "destination", "departure_date"]),
    "search_roundtrip_flights": (
        search_roundtrip_flights,
        ["origin", "destination", "departure_date", "return_date"],
    ),
    "search_itinerary_flights": (search_itinerary_flights, ["segments_text"]),
    "calculate_travel_budget": (
        calculate_travel_budget,
        ["total_budget_vnd", "flight_cost_vnd", "hotel_per_night_vnd", "num_nights"],
    ),
}

TOOL_NAMES = list(_REGISTRY.keys())


def get_tool_specs() -> List[Dict[str, Any]]:
    """Schemas for ReAct system prompt (name + description + argument names)."""
    return [
        {
            "name": "get_weather",
            "description": (
                "Lấy thời tiết hiện tại và vài mốc dự báo (OpenWeatherMap). "
                "Tham số: city — tên thành phố tiếng Anh hoặc 'Da Nang, VN', ví dụ: Da Nang"
            ),
            "args": ["city"],
        },
        {
            "name": "search_flights",
            "description": (
                "Tìm vé máy bay (Duffel Air API). "
                "origin, destination: mã IATA 3 chữ (HAN, DAD, SGN). "
                "departure_date: ưu tiên YYYY-MM-DD, nhưng tool cũng hiểu today/tomorrow/ngay mai, "
                "next monday, ngay nay tuan sau, cuoi tuan sau, dd/mm/yyyy."
            ),
            "args": ["origin", "destination", "departure_date"],
        },
        {
            "name": "search_roundtrip_flights",
            "description": (
                "Tìm vé khứ hồi bằng 2 lượt tìm một chiều. "
                "origin, destination là IATA; departure_date là ngày đi; return_date là ngày về. "
                "Hỗ trợ ngày tự nhiên như tomorrow, next monday, ngay mai."
            ),
            "args": ["origin", "destination", "departure_date", "return_date"],
        },
        {
            "name": "search_itinerary_flights",
            "description": (
                "Tìm vé cho tour nhiều chặng. segments_text nhận JSON list hoặc chuỗi: "
                "'HAN-DAD:tomorrow; DAD-SGN:next monday; SGN-HAN:2026-05-20'."
            ),
            "args": ["segments_text"],
        },
        {
            "name": "calculate_travel_budget",
            "description": (
                "Tính tiền còn lại sau khi trừ vé và phòng khách sạn. "
                "total_budget_vnd, flight_cost_vnd, hotel_per_night_vnd là số VND; "
                "num_nights là số đêm ở lại (số nguyên)."
            ),
            "args": ["total_budget_vnd", "flight_cost_vnd", "hotel_per_night_vnd", "num_nights"],
        },
    ]


def _split_args(arg_string: str) -> List[str]:
    """Split top-level commas; respect quoted segments (' or ")."""
    parts: List[str] = []
    buf: List[str] = []
    quote_char: Optional[str] = None
    for ch in arg_string:
        if ch in ('"', "'"):
            if quote_char is None:
                quote_char = ch
            elif quote_char == ch:
                quote_char = None
            buf.append(ch)
        elif ch == "," and quote_char is None:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return [p for p in parts if p]


def _parse_value(raw: str) -> Any:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ('"', "'"):
        return raw[1:-1]
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _normalize_tool_arg_tokens(arg_string: str, param_names: List[str]) -> Tuple[List[str], Optional[str]]:
    """
    Hỗ trợ cả:
    - positional: HAN, DAD, 2026-04-15
    - keyword: origin=HAN, destination=DAD, departure_date=2026-04-15
    """
    raw = arg_string.strip()
    # Tool 1 tham số (vd: get_weather(city)) cho phép dấu phẩy trong giá trị:
    # get_weather(Da Nang, VN) -> city = "Da Nang, VN"
    if len(param_names) == 1:
        if not raw:
            return [], "empty arguments"
        key = param_names[0]
        if "=" in raw:
            left, _, right = raw.partition("=")
            if left.strip() == key:
                return [right.strip()], None
        return [raw], None

    parts = _split_args(raw) if raw else []
    if not parts and not param_names:
        return [], None
    if not parts:
        return [], "empty arguments"

    # Keyword-only: mọi mẩu đều có '=' → gom dict rồi sắp theo param_names
    if all("=" in p for p in parts):
        kv: Dict[str, str] = {}
        for p in parts:
            k, _, v = p.partition("=")
            kv[k.strip()] = v.strip()
        if all(k in kv for k in param_names):
            return [kv[k] for k in param_names], None

    # Positional: bỏ prefix tham_số= nếu LLM vẫn in kiểu keyword
    if len(parts) != len(param_names):
        return (
            [],
            f"expected {len(param_names)} args, got {len(parts)}; "
            f"use either {', '.join(param_names)} or name=value for each",
        )

    cleaned: List[str] = []
    for i, p in enumerate(parts):
        p = p.strip()
        key = param_names[i]
        lower_prefix = key.lower() + "="
        if p.lower().startswith(lower_prefix):
            p = p.split("=", 1)[1].strip()
        elif "=" in p and p.split("=", 1)[0].strip() == key:
            p = p.split("=", 1)[1].strip()
        cleaned.append(p)
    return cleaned, None


def execute_tool(name: str, arg_string: str) -> str:
    if name not in _REGISTRY:
        return json.dumps({"error": f"Unknown tool: {name}", "known": TOOL_NAMES}, ensure_ascii=False)

    fn, param_names = _REGISTRY[name]
    values, norm_err = _normalize_tool_arg_tokens(arg_string, param_names)

    if norm_err:
        return json.dumps(
            {
                "error": norm_err,
                "tool": name,
                "expected_params": param_names,
                "hint": f'Ví dụ: {name}(a, b) hoặc {name}(a=a, b=b) theo đúng tên: {", ".join(param_names)}',
            },
            ensure_ascii=False,
        )

    kwargs = {k: _parse_value(v) for k, v in zip(param_names, values)}
    try:
        return fn(**kwargs)
    except Exception as e:
        return json.dumps({"error": str(e), "tool": name}, ensure_ascii=False)
