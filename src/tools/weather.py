import json
import os
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

import requests

from src.tools.demo_fallback import demo_travel_apis_enabled, mock_weather

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def _normalize_city(city: str) -> str:
    """Bo prefix city= neu LLM gui kieu keyword trong chuoi."""
    s = city.strip()
    if s.lower().startswith("city="):
        s = s.split("=", 1)[1].strip()
    return s


def _ascii_fold(s: str) -> str:
    """Lowercase + strip accents for matching Vietnamese names."""
    s = s.replace("Đ", "D").replace("đ", "d")
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn").lower()


# Ten thanh pho Viet thuong gap -> query ASCII (OpenWeather on dinh hon)
_VI_TO_EN: Dict[str, str] = {
    "da nang": "Da Nang",
    "ha noi": "Hanoi",
    "ho chi minh": "Ho Chi Minh City",
    "tp hcm": "Ho Chi Minh City",
    "tp. hcm": "Ho Chi Minh City",
    "hue": "Hue",
    "nha trang": "Nha Trang",
    "hai phong": "Hai Phong",
    "can tho": "Can Tho",
    "da lat": "Da Lat",
    "vinh": "Vinh",
    "quy nhon": "Quy Nhon",
    "phan thiet": "Phan Thiet",
    "vung tau": "Vung Tau",
}


def _city_query_variants(raw: str) -> List[str]:
    """
    Thu nhieu dang q= de tranh 404 khi LLM gui Unicode hoac format la.
    OpenWeather chap nhan 'Da Nang, VN' — khong phai loi 'dau phay'.
    """
    base = _normalize_city(raw)
    seen: set = set()
    out: List[str] = []

    def add(x: str) -> None:
        x = x.strip()
        if not x or x in seen:
            return
        seen.add(x)
        out.append(x)

    add(base)
    if len(base) >= 2 and base[0] in "'\"" and base[-1] == base[0]:
        add(base[1:-1].strip())

    if "," in base:
        left = base.split(",")[0].strip()
        right = base.rsplit(",", 1)[-1].strip()
        add(left)
        if len(right) == 2 and right.isalpha():
            add(f"{left}, {right.upper()}")

    # Map theo doan truoc dau phay hoac ca chuoi (fold tieng Viet -> ASCII)
    for segment in (base.split(",")[0].strip(), base):
        key = _ascii_fold(segment)
        if key in _VI_TO_EN:
            en = _VI_TO_EN[key]
            add(f"{en}, VN")
            add(en)
        else:
            for vn_key, en in _VI_TO_EN.items():
                if vn_key in key:
                    add(f"{en}, VN")
                    add(en)
                    break

    return out


def _parse_owm_error(status_code: int, body: Any) -> str:
    if isinstance(body, dict):
        msg = body.get("message") or str(body)
        cod = body.get("cod")
        if status_code == 401 or cod == 401:
            return (
                "401 Invalid API key. Nguyen nhan thuong gap: (1) Key vua tao — cho 10 phut–2 gio de OpenWeather kich hoat. "
                "(2) Copy thieu ky tu / co dau cach trong .env. (3) Chua xac nhan email. "
                "Xem: docs/OPENWEATHER_SETUP_VI.md va https://openweathermap.org/faq#error401"
            )
        if status_code == 404 or cod == "404":
            return (
                f"404 Khong tim thay dia diem: {msg}. "
                "Thu lai voi ten ASCII, vi du: 'Da Nang, VN' hoac 'Hanoi, VN'."
            )
        if status_code == 429:
            return "429 Qua nhieu request (rate limit). Doi vai phut hoac giam tan suat goi API."
        return f"HTTP {status_code}: {msg}"
    return f"HTTP {status_code}: {str(body)[:400]}"


def _fetch_json(url: str, params: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[str]]:
    try:
        r = requests.get(url, params=params, timeout=20)
    except requests.RequestException as e:
        return None, f"Loi mang / timeout: {e}"

    try:
        body = r.json()
    except ValueError:
        return None, f"Phan hoi khong phai JSON: {r.text[:400]}"

    if r.status_code != 200:
        return None, _parse_owm_error(r.status_code, body)

    if isinstance(body, dict) and str(body.get("cod")) == "404":
        return None, _parse_owm_error(404, body)

    return body, None


def get_weather(city: str) -> str:
    """
    Current conditions + next few slots from 5-day forecast (OpenWeatherMap).
    """
    key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    # Loai bo ngoac kep thua khi user paste trong .env
    if len(key) >= 2 and key[0] in "'\"" and key[-1] == key[0]:
        key = key[1:-1].strip()

    if not key:
        if demo_travel_apis_enabled():
            return mock_weather(city)
        return json.dumps(
            {
                "error": "Missing OPENWEATHER_API_KEY in .env",
                "hint": "Xem huong dan: docs/OPENWEATHER_SETUP_VI.md — hoac DEMO_TRAVEL_APIS=1 de demo.",
            },
            ensure_ascii=False,
        )

    if len(key) < 20:
        return json.dumps(
            {
                "error": "OPENWEATHER_API_KEY co ve qua ngan.",
                "hint": "Lay key tai https://home.openweathermap.org/api_keys — xem docs/OPENWEATHER_SETUP_VI.md",
                "key_length": len(key),
            },
            ensure_ascii=False,
        )

    city = _normalize_city(city)
    base_params: Dict[str, Any] = {"appid": key, "units": "metric", "lang": "vi"}

    variants = _city_query_variants(city)
    cur: Optional[Dict] = None
    err_last: Optional[str] = None
    q_used: str = city

    for q in variants:
        params_try = {**base_params, "q": q}
        cur, err_last = _fetch_json(OPENWEATHER_URL, params_try)
        if not err_last:
            q_used = q
            break

    if cur is None or err_last:
        return json.dumps(
            {
                "error": "OpenWeather: current weather failed",
                "detail": err_last,
                "city_query": city,
                "variants_tried": variants[:12],
                "doc": "docs/OPENWEATHER_SETUP_VI.md",
            },
            ensure_ascii=False,
        )

    params_fc = {**base_params, "q": q_used}
    fc, fc_err = _fetch_json(FORECAST_URL, params_fc)
    if fc_err:
        fc = {"list": []}

    main = cur.get("weather", [{}])[0].get("description", "")
    temp = cur.get("main", {}).get("temp")
    feels = cur.get("main", {}).get("feels_like")
    humidity = cur.get("main", {}).get("humidity")

    samples = []
    for item in (fc.get("list") or [])[:8]:
        samples.append(
            {
                "time_utc": item.get("dt_txt"),
                "temp_c": item.get("main", {}).get("temp"),
                "description": (item.get("weather") or [{}])[0].get("description"),
                "pop": item.get("pop"),
            }
        )

    owm_city_id = cur.get("id")
    public_page = (
        f"https://openweathermap.org/city/{owm_city_id}"
        if isinstance(owm_city_id, int)
        else None
    )

    out = {
        "source": "openweathermap.org/data/2.5",
        "weather_query": q_used,
        "openweather_city_id": owm_city_id,
        "public_weather_page_url": public_page,
        "city": cur.get("name"),
        "country": (cur.get("sys") or {}).get("country"),
        "current": {
            "description": main,
            "temp_c": temp,
            "feels_like_c": feels,
            "humidity_percent": humidity,
        },
        "forecast_samples_next_24h": samples,
        "forecast_note": None if not fc_err else f"Forecast skipped: {fc_err}",
    }
    return json.dumps(out, ensure_ascii=False)
