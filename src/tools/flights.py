import json
import os
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Tuple
import unicodedata

import requests

from src.tools.demo_fallback import demo_travel_apis_enabled, mock_flights

DUFFEL_OFFER_REQUEST_URL = "https://api.duffel.com/air/offer_requests"
DUFFEL_VERSION = os.getenv("DUFFEL_API_VERSION", "v2")


def _duffel_token() -> str:
    return os.getenv("DUFFEL_ACCESS_TOKEN", "").strip()


def _extract_duffel_offers(body: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = body.get("data") or {}
    offers = data.get("offers")
    if isinstance(offers, list):
        return offers

    included = body.get("included") or []
    if isinstance(included, list):
        return [x for x in included if isinstance(x, dict) and x.get("type") == "offer"]
    return []


def _safe_iata(obj: Any) -> str:
    if isinstance(obj, dict):
        return (obj.get("iata_code") or "").strip()
    return ""


def _segment_summary(seg: Any) -> Dict[str, Any]:
    if not isinstance(seg, dict):
        return {}
    marketing_carrier = seg.get("marketing_carrier") or {}
    operating_carrier = seg.get("operating_carrier") or {}
    aircraft = seg.get("aircraft") or {}
    origin = seg.get("origin") or {}
    destination = seg.get("destination") or {}

    return {
        "origin": _safe_iata(origin),
        "destination": _safe_iata(destination),
        "departing_at": seg.get("departing_at"),
        "arriving_at": seg.get("arriving_at"),
        "duration": seg.get("duration"),
        "marketing_carrier": {
            "name": (marketing_carrier.get("name") if isinstance(marketing_carrier, dict) else None),
            "iata_code": (marketing_carrier.get("iata_code") if isinstance(marketing_carrier, dict) else None),
        },
        "operating_carrier": {
            "name": (operating_carrier.get("name") if isinstance(operating_carrier, dict) else None),
            "iata_code": (operating_carrier.get("iata_code") if isinstance(operating_carrier, dict) else None),
        },
        "flight_number": {
            "marketing": seg.get("marketing_carrier_flight_number"),
            "operating": seg.get("operating_carrier_flight_number"),
        },
        "aircraft": {
            "name": (aircraft.get("name") if isinstance(aircraft, dict) else None),
            "iata_code": (aircraft.get("iata_code") if isinstance(aircraft, dict) else None),
        },
    }


def _offer_request_resource_url(offer_request_id: Any) -> str:
    if isinstance(offer_request_id, str) and offer_request_id.strip():
        return f"{DUFFEL_OFFER_REQUEST_URL}/{offer_request_id.strip()}"
    return ""


def _norm_text(text: str) -> str:
    s = (text or "").strip().lower()
    s = s.replace("đ", "d")
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"\s+", " ", s)
    return s


def _weekday_from_token(tok: str) -> int:
    tok = _norm_text(tok)
    mapping = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
        "thu 2": 0,
        "thu 3": 1,
        "thu 4": 2,
        "thu 5": 3,
        "thu 6": 4,
        "thu 7": 5,
        "thu bay": 5,
        "cn": 6,
        "chu nhat": 6,
    }
    return mapping.get(tok, -1)


def _weekday_date(today: date, weekday: int, week_shift: int = 0) -> date:
    delta = (weekday - today.weekday()) % 7
    if week_shift > 0:
        delta += 7 * week_shift
    return today + timedelta(days=delta)


def _parse_relative_date(text: str, today: date) -> Dict[str, Any]:
    s = _norm_text(text)
    out: Dict[str, Any] = {"normalized": "", "candidates": [], "ambiguous": False, "note": ""}

    if s in {"today", "hom nay"}:
        out["normalized"] = today.isoformat()
        out["note"] = "Interpreted as today."
        return out
    if s in {"tomorrow", "ngay mai"}:
        out["normalized"] = (today + timedelta(days=1)).isoformat()
        out["note"] = "Interpreted as tomorrow."
        return out
    if s in {"day after tomorrow", "ngay kia"}:
        out["normalized"] = (today + timedelta(days=2)).isoformat()
        out["note"] = "Interpreted as day after tomorrow."
        return out
    if s in {"next week", "tuan sau", "ngay nay tuan sau"}:
        out["normalized"] = (today + timedelta(days=7)).isoformat()
        out["note"] = "Interpreted as same weekday next week."
        return out
    if s in {"dau tuan sau", "early next week", "start of next week"}:
        next_monday = _weekday_date(today, 0, 1)
        out["normalized"] = next_monday.isoformat()
        out["note"] = "Interpreted as start of next week (Monday)."
        return out
    if s in {"this weekend", "cuoi tuan nay", "next weekend", "cuoi tuan sau"}:
        week_shift = 0 if s in {"this weekend", "cuoi tuan nay"} else 1
        sat = _weekday_date(today, 5, week_shift)
        sun = _weekday_date(today, 6, week_shift)
        out["normalized"] = sat.isoformat()
        out["candidates"] = [sat.isoformat(), sun.isoformat()]
        out["ambiguous"] = True
        out["note"] = "Weekend is ambiguous; defaulted to Saturday."
        return out
    if s in {"cuoi thang nay", "end of this month"}:
        first_next = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        last_day = first_next - timedelta(days=1)
        cands = [max(today, last_day - timedelta(days=2)), max(today, last_day - timedelta(days=1)), last_day]
        out["normalized"] = cands[-1].isoformat()
        out["candidates"] = [d.isoformat() for d in cands]
        out["ambiguous"] = True
        out["note"] = "End of month is ambiguous; defaulted to last day of month."
        return out

    m = re.fullmatch(r"(?:in\s+)?(\d{1,2})\s*(?:day|days|ngay)", s)
    if m:
        out["normalized"] = (today + timedelta(days=int(m.group(1)))).isoformat()
        out["note"] = f"Interpreted as +{m.group(1)} days."
        return out

    # "next monday", "this friday", "thu 6 tuan sau"
    m = re.fullmatch(
        r"(next|this)?\s*(monday|tuesday|wednesday|thursday|friday|saturday|sunday|thu\s*[2-7]|thu bay|cn|chu nhat)(?:\s+(tuan sau|tuan nay))?",
        s,
    )
    if m:
        eng_mode, wd_tok, vi_mode = m.groups()
        wd = _weekday_from_token(wd_tok)
        if wd >= 0:
            week_shift = 0
            if eng_mode == "next" or vi_mode == "tuan sau":
                week_shift = 1
            out["normalized"] = _weekday_date(today, wd, week_shift).isoformat()
            out["note"] = "Interpreted as specific weekday."
            return out

    # "next friday or saturday", "thu 6 hoac thu 7 tuan sau"
    m = re.fullmatch(
        r"(?:next\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday|thu\s*[2-7]|thu bay|cn|chu nhat)\s*(?:or|hoac)\s*(monday|tuesday|wednesday|thursday|friday|saturday|sunday|thu\s*[2-7]|thu bay|cn|chu nhat)(?:\s+(tuan sau|next week))?",
        s,
    )
    if m:
        a, b, period = m.groups()
        da = _weekday_from_token(a)
        db = _weekday_from_token(b)
        if da >= 0 and db >= 0:
            shift = 1 if period in {"tuan sau", "next week"} else 0
            cand_a = _weekday_date(today, da, shift)
            cand_b = _weekday_date(today, db, shift)
            cands = sorted({cand_a.isoformat(), cand_b.isoformat()})
            out["normalized"] = cands[0]
            out["candidates"] = cands
            out["ambiguous"] = True
            out["note"] = "Multiple weekdays found; defaulted to earliest candidate."
            return out

    return out


def _normalize_departure_date(raw: str) -> Dict[str, Any]:
    """
    Accept natural date text and normalize to YYYY-MM-DD.
    Examples: today, tomorrow, in 3 days, 10/05/2026, 2026/05/10, May 10 2026.
    """
    s = (raw or "").strip()
    out: Dict[str, Any] = {"normalized": "", "candidates": [], "ambiguous": False, "note": ""}
    if not s:
        return out

    today = date.today()
    rel = _parse_relative_date(s, today)
    if rel.get("normalized"):
        return rel

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        out["normalized"] = s
        out["note"] = "Used ISO date directly."
        return out

    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y.%m.%d", "%d.%m.%Y", "%b %d %Y", "%B %d %Y", "%d %b %Y", "%d %B %Y"):
        try:
            out["normalized"] = datetime.strptime(s, fmt).date().isoformat()
            out["note"] = f"Parsed with format {fmt}."
            return out
        except ValueError:
            continue

    # Fallback: try common month/day comma format
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            out["normalized"] = datetime.strptime(s, fmt).date().isoformat()
            out["note"] = f"Parsed with format {fmt}."
            return out
        except ValueError:
            continue
    return out


def search_flights(origin: str, destination: str, departure_date: str) -> str:
    """
    Duffel Air API: IATA codes (e.g. HAN, DAD, SGN), departure_date YYYY-MM-DD.
    """
    origin = origin.strip().upper()
    destination = destination.strip().upper()
    departure_date_raw = departure_date.strip()
    date_parse = _normalize_departure_date(departure_date_raw)
    departure_date = date_parse.get("normalized") or ""
    if not departure_date:
        return json.dumps(
            {
                "error": "Invalid departure_date format",
                "input": departure_date_raw,
                "hint": (
                    "Dùng YYYY-MM-DD hoặc cụm tự nhiên như: today, tomorrow, ngay nay tuan sau, "
                    "next monday, cuoi tuan sau, 10/05/2026."
                ),
            },
            ensure_ascii=False,
        )

    token = _duffel_token()
    if not token:
        if demo_travel_apis_enabled():
            raw_demo = mock_flights(origin, destination, departure_date)
            try:
                d = json.loads(raw_demo)
                if isinstance(d, dict):
                    d["departure_date_input"] = departure_date_raw
                    d["departure_date_normalized"] = departure_date
                    d["departure_date_candidates"] = date_parse.get("candidates") or []
                    d["departure_date_ambiguous"] = bool(date_parse.get("ambiguous"))
                    d["departure_date_note"] = date_parse.get("note")
                    return json.dumps(d, ensure_ascii=False)
            except Exception:
                pass
            return raw_demo
        return json.dumps(
            {
                "error": "Missing DUFFEL_ACCESS_TOKEN",
                "hint": "https://duffel.com/docs/api/overview — hoặc DEMO_TRAVEL_APIS=1 trong .env để demo không cần Duffel.",
            },
            ensure_ascii=False,
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Duffel-Version": DUFFEL_VERSION,
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "data": {
            "slices": [
                {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                }
            ],
            "passengers": [{"type": "adult"}],
            "cabin_class": "economy",
            "max_connections": 1,
        }
    }

    try:
        r = requests.post(DUFFEL_OFFER_REQUEST_URL, headers=headers, json=payload, timeout=30)
        if r.status_code >= 400:
            return json.dumps(
                {
                    "error": "Duffel flight search failed",
                    "status": r.status_code,
                    "body": r.text[:3000],
                },
                ensure_ascii=False,
            )
        body = r.json()
    except requests.RequestException as e:
        return json.dumps({"error": "Duffel request failed", "detail": str(e)}, ensure_ascii=False)
    except ValueError:
        return json.dumps({"error": "Duffel response is not valid JSON", "body": r.text[:1000]}, ensure_ascii=False)

    raw_offers = _extract_duffel_offers(body)
    offers = []
    for item in raw_offers[:5]:
        slices = item.get("slices") or []
        first_slice = slices[0] if slices else {}
        segs = first_slice.get("segments") or []
        first_seg = segs[0] if segs else {}
        last_seg = segs[-1] if segs else {}
        seg_summaries = [_segment_summary(s) for s in segs if isinstance(s, dict)]
        marketing = first_seg.get("marketing_carrier") if isinstance(first_seg, dict) else {}
        operating = first_seg.get("operating_carrier") if isinstance(first_seg, dict) else {}
        aircraft = first_seg.get("aircraft") if isinstance(first_seg, dict) else {}
        offers.append(
            {
                "price": item.get("total_amount"),
                "currency": item.get("total_currency", "VND"),
                "departure_at": (first_seg.get("departing_at") if isinstance(first_seg, dict) else None),
                "arrival_at": (last_seg.get("arriving_at") if isinstance(last_seg, dict) else None),
                "carrier_code": (
                    (first_seg.get("marketing_carrier") or {}).get("iata_code")
                    if isinstance(first_seg, dict)
                    else ""
                ),
                "carrier_name": (
                    (marketing.get("name") if isinstance(marketing, dict) else None)
                ),
                "flight_number": (
                    first_seg.get("marketing_carrier_flight_number") if isinstance(first_seg, dict) else None
                ),
                "aircraft": {
                    "name": (aircraft.get("name") if isinstance(aircraft, dict) else None),
                    "iata_code": (aircraft.get("iata_code") if isinstance(aircraft, dict) else None),
                },
                "operating_carrier": {
                    "name": (operating.get("name") if isinstance(operating, dict) else None),
                    "iata_code": (operating.get("iata_code") if isinstance(operating, dict) else None),
                },
                "number_of_stops": max(0, len(segs) - 1),
                "segments": seg_summaries,
            }
        )

    offer_request_id = (body.get("data") or {}).get("id")
    resource_url = _offer_request_resource_url(offer_request_id)

    if not offers:
        return json.dumps(
            {
                "message": "No offers returned for this route/date.",
                "departure_date_input": departure_date_raw,
                "departure_date_normalized": departure_date,
                "departure_date_candidates": date_parse.get("candidates") or [],
                "departure_date_ambiguous": bool(date_parse.get("ambiguous")),
                "departure_date_note": date_parse.get("note"),
                "duffel_offer_request_id": offer_request_id,
                "duffel_offer_request_url": resource_url or None,
                "source": "duffel",
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "offers": offers,
            "departure_date_input": departure_date_raw,
            "departure_date_normalized": departure_date,
            "departure_date_candidates": date_parse.get("candidates") or [],
            "departure_date_ambiguous": bool(date_parse.get("ambiguous")),
            "departure_date_note": date_parse.get("note"),
            "duffel_offer_request_id": offer_request_id,
            "duffel_offer_request_url": resource_url or None,
            "source": "duffel",
        },
        ensure_ascii=False,
    )


def search_roundtrip_flights(origin: str, destination: str, departure_date: str, return_date: str) -> str:
    """
    Tim ve khu hoi bang 2 luot tim 1 chieu (di + ve), gom ket qua vao 1 JSON.
    """
    out_raw = search_flights(origin, destination, departure_date)
    in_raw = search_flights(destination, origin, return_date)
    try:
        outbound = json.loads(out_raw)
    except Exception:
        outbound = {"error": "Failed to parse outbound result", "raw": out_raw[:1500]}
    try:
        inbound = json.loads(in_raw)
    except Exception:
        inbound = {"error": "Failed to parse inbound result", "raw": in_raw[:1500]}

    return json.dumps(
        {
            "type": "roundtrip",
            "route": f"{origin.strip().upper()}<->{destination.strip().upper()}",
            "outbound": outbound,
            "inbound": inbound,
            "source": "duffel",
        },
        ensure_ascii=False,
    )


def _parse_itinerary_segments(segments_text: str) -> Tuple[List[Dict[str, str]], str]:
    """
    Parse multi-city input:
    - JSON list: [{"origin":"HAN","destination":"DAD","departure_date":"tomorrow"}, ...]
    - Hoac chuoi: "HAN-DAD:tomorrow; DAD-SGN:next monday; SGN-HAN:2026-05-20"
    """
    text = (segments_text or "").strip()
    if not text:
        return [], "segments_text is empty"

    if text.startswith("["):
        try:
            arr = json.loads(text)
        except Exception as e:
            return [], f"invalid JSON segments_text: {e}"
        if not isinstance(arr, list):
            return [], "segments_text JSON must be a list"
        out: List[Dict[str, str]] = []
        for i, item in enumerate(arr, 1):
            if not isinstance(item, dict):
                return [], f"segment {i} must be an object"
            o = str(item.get("origin", "")).strip().upper()
            d = str(item.get("destination", "")).strip().upper()
            dt = str(item.get("departure_date", "")).strip()
            if not o or not d or not dt:
                return [], f"segment {i} missing origin/destination/departure_date"
            out.append({"origin": o, "destination": d, "departure_date": dt})
        return out, ""

    parts = [p.strip() for p in text.split(";") if p.strip()]
    out2: List[Dict[str, str]] = []
    for i, part in enumerate(parts, 1):
        m = re.fullmatch(r"([A-Za-z]{3})\s*-\s*([A-Za-z]{3})\s*:\s*(.+)", part)
        if not m:
            return [], (
                f"segment {i} invalid format: '{part}'. "
                "Use 'HAN-DAD:tomorrow; DAD-SGN:2026-05-12'."
            )
        o, d, dt = m.groups()
        out2.append({"origin": o.upper(), "destination": d.upper(), "departure_date": dt.strip()})
    if not out2:
        return [], "no valid segments found"
    return out2, ""


def search_itinerary_flights(segments_text: str) -> str:
    """
    Tim ve cho tour nhieu chang.
    """
    segments, err = _parse_itinerary_segments(segments_text)
    if err:
        return json.dumps(
            {
                "error": "Invalid itinerary input",
                "detail": err,
                "hint": (
                    "Dung JSON list hoac chuoi 'HAN-DAD:tomorrow; DAD-SGN:next monday; SGN-HAN:2026-05-20'."
                ),
            },
            ensure_ascii=False,
        )

    leg_results: List[Dict[str, Any]] = []
    for seg in segments:
        raw = search_flights(seg["origin"], seg["destination"], seg["departure_date"])
        try:
            leg_data = json.loads(raw)
        except Exception:
            leg_data = {"error": "Failed to parse leg result", "raw": raw[:1500]}
        leg_results.append(
            {
                "origin": seg["origin"],
                "destination": seg["destination"],
                "departure_date_input": seg["departure_date"],
                "result": leg_data,
            }
        )

    total_min = 0.0
    priced_legs = 0
    for leg in leg_results:
        offers = (leg.get("result") or {}).get("offers") or []
        prices: List[float] = []
        for off in offers:
            try:
                prices.append(float(str(off.get("price"))))
            except Exception:
                continue
        if prices:
            total_min += min(prices)
            priced_legs += 1

    return json.dumps(
        {
            "type": "itinerary",
            "num_legs": len(segments),
            "priced_legs": priced_legs,
            "estimated_min_total_price": round(total_min, 2) if priced_legs else None,
            "legs": leg_results,
            "source": "duffel",
        },
        ensure_ascii=False,
    )
