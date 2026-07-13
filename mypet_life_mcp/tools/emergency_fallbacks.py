from __future__ import annotations

from mypet_life_mcp.core.schemas import GeoPoint
from mypet_life_mcp.tools.data_files import load_data_json


_DATA = load_data_json("emergency_fallbacks.json")
EMERGENCY_FALLBACK_SOURCE = _DATA["source"]
SEOUL_EMERGENCY_HOSPITALS = _DATA["seoul_hospitals"]
SEOUL_KEYWORDS = tuple(_DATA["seoul_keywords"])


def emergency_hospital_fallbacks(location: str, origin: GeoPoint | None = None) -> list[dict]:
    if not _is_seoul_query(location, origin):
        return []
    return [{**item, "source": EMERGENCY_FALLBACK_SOURCE} for item in SEOUL_EMERGENCY_HOSPITALS]


def _is_seoul_query(location: str, origin: GeoPoint | None) -> bool:
    text = location.replace(" ", "")
    if any(keyword in text for keyword in SEOUL_KEYWORDS):
        return True
    return bool(origin and origin.address.startswith("서울"))
