from __future__ import annotations

from mypet_life_mcp.core.schemas import GeoPoint


EMERGENCY_FALLBACK_SOURCE = "내장 응급 연락 후보(전화 확인 필요)"

SEOUL_EMERGENCY_HOSPITALS = [
    {
        "name": "24시여의동물의료센터",
        "address": "서울특별시 영등포구 국회대로74길 4, KCT TOWER 1층",
        "phone": "02-785-2475",
        "business_status": "전화 확인 필요",
        "latitude": 37.5286,
        "longitude": 126.9185,
        "license_type": "동물병원",
    },
    {
        "name": "포커스동물의료센터",
        "address": "서울특별시 양천구 신월로 328",
        "phone": "02-6952-4946",
        "business_status": "전화 확인 필요",
        "latitude": 37.5219,
        "longitude": 126.8546,
        "license_type": "동물병원",
    },
    {
        "name": "늘동물의료센터",
        "address": "서울특별시 양천구 목동동로 233-1",
        "phone": "02-6447-7575",
        "business_status": "전화 확인 필요",
        "latitude": 37.5262,
        "longitude": 126.8756,
        "license_type": "동물병원",
    },
]


SEOUL_KEYWORDS = (
    "서울",
    "강남",
    "강동",
    "강북",
    "강서",
    "관악",
    "광진",
    "구로",
    "금천",
    "노원",
    "도봉",
    "동대문",
    "동작",
    "마포",
    "서대문",
    "서초",
    "성동",
    "성북",
    "송파",
    "양천",
    "목동",
    "영등포",
    "여의도",
    "용산",
    "은평",
    "종로",
    "중구",
    "중랑",
)


def emergency_hospital_fallbacks(location: str, origin: GeoPoint | None = None) -> list[dict]:
    if not _is_seoul_query(location, origin):
        return []
    return [{**item, "source": EMERGENCY_FALLBACK_SOURCE} for item in SEOUL_EMERGENCY_HOSPITALS]


def _is_seoul_query(location: str, origin: GeoPoint | None) -> bool:
    text = location.replace(" ", "")
    if any(keyword in text for keyword in SEOUL_KEYWORDS):
        return True
    return bool(origin and origin.address.startswith("서울"))
