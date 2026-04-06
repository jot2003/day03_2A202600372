"""Dữ liệu giả lập khi bật DEMO_TRAVEL_APIS=1 và chưa có API key (chỉ để demo / học lab)."""
import json
import os
from typing import Any, Dict
from urllib.parse import quote_plus


def demo_travel_apis_enabled() -> bool:
    v = os.getenv("DEMO_TRAVEL_APIS", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def mock_weather(city: str) -> str:
    city = city.strip() or "Da Nang"
    # Trang web OWM theo city id (cung id khi goi API that) — de demo bam link ra dung noi
    _KNOWN_OWM_CITY_ID: Dict[str, int] = {
        "da nang": 1583992,
        "đà nẵng": 1583992,
        "hanoi": 1581130,
        "hà nội": 1581130,
        "ho chi minh": 1580578,
        "hồ chí minh": 1580578,
        "saigon": 1580578,
        "hue": 1580246,
        "huế": 1580246,
    }
    key = city.lower().split(",")[0].strip()
    owm_id = _KNOWN_OWM_CITY_ID.get(key)
    if owm_id is None:
        for k, cid in _KNOWN_OWM_CITY_ID.items():
            if k in key or key in k:
                owm_id = cid
                break
    public_url = (
        f"https://openweathermap.org/city/{owm_id}"
        if owm_id is not None
        else f"https://openweathermap.org/find?q={quote_plus(city)}"
    )
    out: Dict[str, Any] = {
        "_demo": True,
        "city": city,
        "country": "VN",
        "openweather_city_id": owm_id,
        "public_weather_page_url": public_url,
        "current": {
            "description": "nắng nhẹ, ít mây (dữ liệu demo)",
            "temp_c": 29,
            "feels_like_c": 31,
            "humidity_percent": 72,
        },
        "forecast_samples_next_24h": [
            {"time_utc": "demo", "temp_c": 28, "description": "nắng", "pop": 0.1},
        ],
    }
    return json.dumps(out, ensure_ascii=False)


def mock_flights(origin: str, destination: str, departure_date: str) -> str:
    origin = (origin or "HAN").strip().upper()
    destination = (destination or "DAD").strip().upper()
    departure_date = (departure_date or "").strip()
    out = {
        "_demo": True,
        "message": "Giá vé mẫu (không phải API Duffel). Đặt OPENWEATHER + DUFFEL trong .env để dùng dữ liệu thật.",
        "offers": [
            {
                "price": "1250000",
                "currency": "VND",
                "departure_at": f"{departure_date}T06:00:00",
                "arrival_at": f"{departure_date}T07:15:00",
                "carrier_code": "VJ",
                "carrier_name": "VietJet Air (demo)",
                "flight_number": "VJ123 (demo)",
                "aircraft": {"name": "Airbus A320 (demo)", "iata_code": "320"},
                "number_of_stops": 0,
                "segments": [
                    {
                        "origin": origin,
                        "destination": destination,
                        "departing_at": f"{departure_date}T06:00:00",
                        "arriving_at": f"{departure_date}T07:15:00",
                        "duration": "PT1H15M",
                        "marketing_carrier": {"name": "VietJet Air (demo)", "iata_code": "VJ"},
                        "operating_carrier": {"name": "VietJet Air (demo)", "iata_code": "VJ"},
                        "flight_number": {"marketing": "123", "operating": "123"},
                        "aircraft": {"name": "Airbus A320 (demo)", "iata_code": "320"},
                    }
                ],
            },
            {
                "price": "1890000",
                "currency": "VND",
                "departure_at": f"{departure_date}T08:30:00",
                "arrival_at": f"{departure_date}T09:45:00",
                "carrier_code": "VN",
                "carrier_name": "Vietnam Airlines (demo)",
                "flight_number": "VN456 (demo)",
                "aircraft": {"name": "Airbus A321 (demo)", "iata_code": "321"},
                "number_of_stops": 0,
                "segments": [
                    {
                        "origin": origin,
                        "destination": destination,
                        "departing_at": f"{departure_date}T08:30:00",
                        "arriving_at": f"{departure_date}T09:45:00",
                        "duration": "PT1H15M",
                        "marketing_carrier": {"name": "Vietnam Airlines (demo)", "iata_code": "VN"},
                        "operating_carrier": {"name": "Vietnam Airlines (demo)", "iata_code": "VN"},
                        "flight_number": {"marketing": "456", "operating": "456"},
                        "aircraft": {"name": "Airbus A321 (demo)", "iata_code": "321"},
                    }
                ],
            },
        ],
        "route": f"{origin}→{destination}",
        "source": "demo_stub",
    }
    return json.dumps(out, ensure_ascii=False)
