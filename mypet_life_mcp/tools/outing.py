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


from .outing_intents import (
    SEMANTIC_FALLBACK_INTENTS,
    _content_type_for_outing,
    _keywords_for_outing,
    _outing_intent,
    OUTING_INTENT_CONTENT_TYPES,
)
from .outing_helpers import compact_weather, dedupe_items, filter_items_by_intent, filter_items_by_region

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
    weather = compact_weather(weather_result.items)
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
            keyword_result = place_client.search_keyword(keyword, content_type=content_type, rows=20)
            if keyword_result.ok:
                keyword_items.extend(keyword_result.items)
            deduped_so_far = filter_items_by_intent(dedupe_items(keyword_items), intent, OUTING_INTENT_CONTENT_TYPES)
            if len(filter_items_by_region(deduped_so_far, location_text)) >= 5:
                break
            if len(deduped_so_far) >= 10:
                break
    keyword_items = filter_items_by_intent(dedupe_items(keyword_items), intent, OUTING_INTENT_CONTENT_TYPES)
    local_keyword_items = filter_items_by_region(keyword_items, location_text)
    if local_keyword_items:
        from mypet_life_mcp.core.schemas import SourceResult

        return SourceResult(items=local_keyword_items, source=place_client.service_name)

    location_result = place_client.search(latitude, longitude, radius, content_type)
    if location_result.items:
        return location_result
    if keyword_items and intent in SEMANTIC_FALLBACK_INTENTS:
        from mypet_life_mcp.core.schemas import SourceResult

        return SourceResult(
            items=dedupe_items(keyword_items)[:10],
            source=place_client.service_name,
            ok=True,
            error_ko=f"'{outing_type}'에 정확히 맞는 지역 내 후보가 부족해 활동 키워드 기준 후보를 함께 제시합니다.",
        )
    return location_result


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
