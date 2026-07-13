from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib.resources import files
from typing import Any

from mypet_life_mcp.core.schemas import GeoPoint


CITY_ALIASES = {
    "서울특별시": ("서울", "서울시", "서울특별시"),
    "부산광역시": ("부산", "부산시", "부산광역시"),
    "대구광역시": ("대구", "대구시", "대구광역시"),
    "인천광역시": ("인천", "인천시", "인천광역시"),
    "광주광역시": ("광주", "광주시", "광주광역시"),
    "대전광역시": ("대전", "대전시", "대전광역시"),
    "울산광역시": ("울산", "울산시", "울산광역시"),
    "세종특별자치시": ("세종", "세종시", "세종특별자치시"),
}

LOCATION_SUFFIXES = ("근처", "주변", "인근", "부근", "앞", "쪽", "에서", "으로", "까지")
QUERY_ALIASES = {
    "부평시청역": "부평구청역",
    "부평시청": "부평구청역",
}


def station_centroid(location: str) -> GeoPoint | None:
    query = _compact(location)
    query = QUERY_ALIASES.get(query, query)
    if not query:
        return None

    matches = [_score_station(query, item) for item in _stations()]
    matches = [item for item in matches if item[0] > 0]
    if not matches:
        return None

    _, station = max(matches, key=lambda item: item[0])
    label = station["name"] if str(station["name"]).endswith("역") else f"{station['name']}역"
    return GeoPoint(
        label=label,
        latitude=float(station["latitude"]),
        longitude=float(station["longitude"]),
        address=str(station.get("address") or label),
    )


@lru_cache(maxsize=1)
def _stations() -> tuple[dict[str, Any], ...]:
    path = files("mypet_life_mcp.data").joinpath("station_locations.json")
    return tuple(json.loads(path.read_text(encoding="utf-8")))


def _score_station(query: str, station: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    aliases = sorted((str(alias) for alias in station.get("aliases", [])), key=len, reverse=True)
    score = 0
    for alias in aliases:
        alias_key = _compact(alias)
        if not alias_key:
            continue
        if query == alias_key or _strip_location_suffix(query) == alias_key:
            score = max(score, 100 + len(alias_key))
        elif "역" in query and alias_key.endswith("역") and alias_key in query:
            score = max(score, 70 + len(alias_key))
        elif "역" not in query and query.endswith(alias_key):
            score = max(score, 45 + len(alias_key))

    if score <= 0:
        return 0, station

    score += _context_score(query, station)
    return score, station


def _context_score(query: str, station: dict[str, Any]) -> int:
    score = 0
    province = str(station.get("province") or "")
    for alias in CITY_ALIASES.get(province, (province,)):
        if alias and _compact(alias) in query:
            score += 30

    address = _compact(str(station.get("address") or ""))
    for token in _compact(query).split():
        if token and token in address:
            score += 5

    line_name = _compact(str(station.get("line_name") or ""))
    if line_name and line_name in query:
        score += 20
    return score


def _strip_location_suffix(value: str) -> str:
    text = value
    changed = True
    while changed:
        changed = False
        for suffix in LOCATION_SUFFIXES:
            key = _compact(suffix)
            if text.endswith(key):
                text = text[: -len(key)]
                changed = True
    return text


def _compact(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", value).lower()
