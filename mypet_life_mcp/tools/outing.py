from __future__ import annotations

from mypet_life_mcp.clients import (
    AnimalHospitalClient,
    AnimalPharmacyClient,
    PetFriendlyPlaceClient,
    WeatherClient,
)
from mypet_life_mcp.core.korean import confirmation_note_ko, safety_note_ko
from mypet_life_mcp.core.schemas import GeoPoint, ValidationError, optional_coordinate, parse_when, positive_radius, require_text
from mypet_life_mcp.core.scoring import enrich_distance, outing_score, rank_candidates

from .common import candidates_from_source, map_place, normalize_region_name, region_centroid, setup_response, source_warnings


OUTING_TYPE_CONTENT_TYPE = {
    "숙소": "32",
    "펜션": "32",
    "호텔": "32",
    "캠핑": "32",
    "글램핑": "32",
    "식사": "39",
    "점심": "39",
    "저녁": "39",
    "밥": "39",
    "맛집": "39",
    "카페": "39",
    "놀이": "12",
    "놀거리": "12",
    "놀이터": "12",
    "산책": "12",
    "공원": "12",
    "등산": "12",
    "관광": "12",
    "여행": "12",
    "물놀이": "12",
    "해변": "12",
    "계곡": "12",
    "호수": "12",
    "walk": "12",
    "play": "12",
    "meal": "39",
    "stay": "32",
}

OUTING_INTENT_KEYWORDS = {
    "water": ["물놀이", "해변", "계곡", "바다", "호수", "강변", "반려견 놀이터"],
    "stay": ["애견펜션", "펜션", "글램핑", "캠핑", "호텔", "숙소"],
    "food": ["카페", "식당", "브런치", "베이커리", "맛집"],
    "play": ["반려견 놀이터", "공원", "산책", "휴양림", "등산", "관광"],
    "indoor": ["박물관", "쇼핑", "문화", "카페"],
    "drive": ["관광", "시장", "한옥", "유람선", "해변"],
}

OUTING_INTENT_ALIASES = {
    "water": ["물놀이", "수영", "수영장", "해변", "바다", "계곡", "호수", "강가", "강변"],
    "stay": ["숙소", "펜션", "호텔", "캠핑", "글램핑", "카라반", "1박", "여행"],
    "food": ["식사", "점심", "저녁", "밥", "맛집", "카페", "브런치", "베이커리"],
    "play": ["놀이", "놀이터", "운동장", "산책", "공원", "등산", "산에", "뛰어", "뛰놀", "휴양림"],
    "indoor": ["실내", "비오는", "비 오는", "더운", "추운"],
    "drive": ["드라이브", "차로", "바람쐬", "관광"],
}

OUTING_INTENT_CONTENT_TYPES = {
    "water": {"12", "25", "28"},
    "stay": {"32"},
    "food": {"39"},
    "play": {"12", "25", "28"},
    "indoor": {"14", "38", "39"},
    "drive": {"12", "25"},
}


def make_pet_outing_plan(
    location: str,
    pet_type: str | None = "dog",
    outing_type: str | None = None,
    radius_km: float | None = 5.0,
    when: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    place_client: PetFriendlyPlaceClient | None = None,
    weather_client: WeatherClient | None = None,
    hospital_client: AnimalHospitalClient | None = None,
    pharmacy_client: AnimalPharmacyClient | None = None,
) -> dict:
    try:
        location_text = normalize_region_name(require_text(location, "location"))
        radius = positive_radius(radius_km)
        moment = parse_when(when)
        lat = optional_coordinate(latitude, "latitude", -90, 90)
        lon = optional_coordinate(longitude, "longitude", -180, 180)
    except ValidationError as exc:
        return {"status": "invalid_request", "summary_ko": str(exc), "safety_note_ko": safety_note_ko()}

    location_warning = None
    if lat is not None and lon is not None:
        origin = GeoPoint(label=location_text, latitude=lat, longitude=lon, address=location_text)
    else:
        origin = region_centroid(location_text)
        if origin:
            location_warning = f"정확한 주소 좌표가 없어 '{location_text}' 지역 중심 기준으로 외출 계획을 만듭니다."
        else:
            location_warning = f"좌표가 없어 지역명 '{location_text}' 기준으로 제한된 외출 계획을 만듭니다. 거리순 장소 추천은 제한됩니다."

    if origin:
        place_api = place_client or PetFriendlyPlaceClient()
        place_result = _search_places(
            place_api,
            location_text,
            origin.latitude,
            origin.longitude,
            radius,
            outing_type,
        )
        weather_result = (weather_client or WeatherClient()).forecast(origin.latitude, origin.longitude, moment)
    else:
        place_result = _empty_source("한국관광공사 반려동물 동반 여행 정보", "좌표 변환이 없어 반려동물 동반 장소 조회를 건너뛰었습니다.")
        weather_result = _empty_source("기상청 단기예보", "좌표 변환이 없어 날씨 조회를 건너뛰었습니다.")
    search_region = origin.address if origin and origin.address else location_text
    hospital_result = (hospital_client or AnimalHospitalClient()).search(search_region, radius)
    pharmacy_result = (pharmacy_client or AnimalPharmacyClient()).search(search_region, radius)

    places = [map_place(item) for item in place_result.items][:5]
    weather = _compact_weather(weather_result.items)
    hospital_candidates = candidates_from_source(hospital_result, "동물병원")
    pharmacy_candidates = candidates_from_source(pharmacy_result, "동물약국")
    if origin:
        hospital_candidates = enrich_distance(hospital_candidates, origin)
        pharmacy_candidates = enrich_distance(pharmacy_candidates, origin)
    hospitals = rank_candidates(hospital_candidates, "hospital")[:5]
    pharmacies = rank_candidates(pharmacy_candidates, "pharmacy")[:5]
    score, cautions = outing_score(weather, places, hospitals)
    return {
        "mode": "pet_outing_plan",
        "location": location_text,
        "resolved_location": origin.address if origin else None,
        "location_precision": "provided_coordinate" if lat is not None and lon is not None else ("coordinate" if origin else "region_text_only"),
        "pet_type": pet_type or "dog",
        "outing_type": outing_type,
        "outing_score": score,
        "score_label_ko": _score_label(score),
        "recommended_course_ko": _course(places, hospitals),
        "pet_friendly_places": places,
        "weather": weather,
        "care_contacts": {
            "animal_hospitals": [candidate.to_dict() for candidate in hospitals],
            "animal_pharmacies": [candidate.to_dict() for candidate in pharmacies],
        },
        "cautions_ko": cautions + [confirmation_note_ko()],
        "source_warnings_ko": ([location_warning] if location_warning else [])
        + source_warnings(place_result, weather_result, hospital_result, pharmacy_result),
        "summary_ko": f"{location_text} 주변 반려동물 동반 외출 계획을 정리했습니다. 외출 적합도는 {score}점입니다.",
        "safety_note_ko": safety_note_ko(),
    }


def _compact_weather(items: list[dict]) -> dict:
    if not items:
        return {"rain_probability": 0, "precipitation_mm": 0}
    item = items[0]
    if "rain_probability" in item:
        return item
    return {"rain_probability": item.get("pop", 0), "precipitation_mm": item.get("pcp", 0), "temperature_c": item.get("tmp")}


def _content_type_for_outing(outing_type: str | None) -> str | None:
    if not outing_type:
        return None
    compact = outing_type.strip().lower().replace(" ", "")
    for keyword, content_type in OUTING_TYPE_CONTENT_TYPE.items():
        if keyword in compact:
            return content_type
    return None


def _search_places(
    place_client: PetFriendlyPlaceClient,
    location_text: str,
    latitude: float,
    longitude: float,
    radius: float,
    outing_type: str | None,
):
    content_type = _content_type_for_outing(outing_type)
    intent = _outing_intent(outing_type)
    keyword_items = []
    if intent and hasattr(place_client, "search_keyword"):
        for keyword in _keywords_for_outing(outing_type, intent):
            keyword_result = place_client.search_keyword(keyword, content_type=content_type, rows=5)
            if keyword_result.ok:
                keyword_items.extend(keyword_result.items)
            deduped_so_far = _filter_items_by_intent(_dedupe_items(keyword_items), intent)
            if len(_filter_items_by_region(deduped_so_far, location_text)) >= 5:
                break
            if len(deduped_so_far) >= 10:
                break
    keyword_items = _filter_items_by_intent(_dedupe_items(keyword_items), intent)
    local_keyword_items = _filter_items_by_region(keyword_items, location_text)
    if local_keyword_items:
        from mypet_life_mcp.core.schemas import SourceResult

        return SourceResult(items=local_keyword_items, source=place_client.service_name)

    location_result = place_client.search(latitude, longitude, radius, content_type)
    if keyword_items and intent in {"water", "play", "indoor", "drive"}:
        from mypet_life_mcp.core.schemas import SourceResult

        return SourceResult(
            items=_dedupe_items(keyword_items)[:10],
            source=place_client.service_name,
            ok=True,
            error_ko=f"'{outing_type}'에 정확히 맞는 지역 내 후보가 부족해 활동 키워드 기준 후보를 함께 제시합니다.",
        )
    return location_result


def _outing_intent(outing_type: str | None) -> str | None:
    if not outing_type:
        return None
    compact = outing_type.strip().lower().replace(" ", "")
    for intent, aliases in OUTING_INTENT_ALIASES.items():
        if any(alias.replace(" ", "") in compact for alias in aliases):
            return intent
    return None


def _keywords_for_outing(outing_type: str | None, intent: str) -> list[str]:
    compact = (outing_type or "").strip().lower().replace(" ", "")
    if any(word in compact for word in ("등산", "산에", "산책로")):
        return ["등산", "휴양림", "산책"]
    if any(word in compact for word in ("물놀이", "수영", "해변", "바다", "계곡", "호수", "강변", "강가")):
        return ["물놀이", "해변", "계곡", "호수", "바다"]
    if any(word in compact for word in ("공원", "놀이터", "운동장")):
        return ["반려견 놀이터", "공원", "호수공원", "산책"]
    if any(word in compact for word in ("실내", "비오는", "비오는날", "비오는 날")):
        return ["박물관", "문화", "카페", "쇼핑"]
    return OUTING_INTENT_KEYWORDS[intent]


def _filter_items_by_region(items: list[dict], location_text: str) -> list[dict]:
    province = location_text.split(" ", 1)[0]
    filtered = []
    for item in items:
        address = str(item.get("addr1") or item.get("address") or "")
        if location_text in address or province in address:
            filtered.append(item)
    return filtered


def _filter_items_by_intent(items: list[dict], intent: str | None) -> list[dict]:
    allowed = OUTING_INTENT_CONTENT_TYPES.get(intent or "")
    if not allowed:
        return items
    return [item for item in items if str(item.get("contenttypeid") or "") in allowed]


def _dedupe_items(items: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for item in items:
        if not isinstance(item, dict):
            continue
        key = item.get("contentid") or item.get("title") or str(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _empty_source(source: str, error_ko: str):
    from mypet_life_mcp.core.schemas import SourceResult

    return SourceResult(items=[], source=source, ok=False, error_ko=error_ko)


def _score_label(score: int) -> str:
    if score >= 80:
        return "외출 추천"
    if score >= 60:
        return "조건부 추천"
    if score >= 40:
        return "짧은 외출만 권장"
    return "외출 비추천"


def _course(places: list[dict], hospitals: list) -> list[str]:
    course = []
    for index, place in enumerate(places[:2], start=1):
        course.append(f"{index}. {place['name']} 후보 방문 전 반려동물 동반 조건 전화 확인")
    if hospitals:
        course.append(f"{len(course) + 1}. 근처 동물병원 후보 {hospitals[0].name} 연락처를 저장")
    else:
        course.append(f"{len(course) + 1}. 출발 전 별도 동물병원 후보 확인")
    return course
