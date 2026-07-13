from __future__ import annotations

from mypet_life_mcp.core.schemas import GeoPoint
from mypet_life_mcp.tools.data_files import load_data_json


_DATA = load_data_json("emergency_fallbacks.json")
EMERGENCY_FALLBACK_SOURCE = _DATA["source"]
FALLBACK_GROUPS = tuple(_DATA["groups"])


def emergency_hospital_fallbacks(location: str, origin: GeoPoint | None = None) -> list[dict]:
    group = _matching_group(location, origin)
    if not group:
        return []
    return [{**item, "source": EMERGENCY_FALLBACK_SOURCE} for item in group["hospitals"]]


def _matching_group(location: str, origin: GeoPoint | None) -> dict | None:
    text = location.replace(" ", "")
    address = (origin.address if origin else "").replace(" ", "")
    for group in FALLBACK_GROUPS:
        if any(keyword in text or keyword in address for keyword in group["keywords"]):
            return group
    return None
