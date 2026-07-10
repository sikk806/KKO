from __future__ import annotations

from mypet_life_mcp.clients import (
    AnimalHospitalClient,
    AnimalPharmacyClient,
    KakaoLocalClient,
    PetFriendlyPlaceClient,
    WeatherClient,
)
from mypet_life_mcp.core.korean import confirmation_note_ko, safety_note_ko
from mypet_life_mcp.core.schemas import GeoPoint, ValidationError, optional_coordinate, parse_when, positive_radius, require_text
from mypet_life_mcp.core.scoring import enrich_distance, outing_score, rank_candidates

from .common import candidates_from_source, map_place, setup_response, source_warnings


def make_pet_outing_plan(
    location: str,
    pet_type: str | None = "dog",
    outing_type: str | None = None,
    radius_km: float | None = 5.0,
    when: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    kakao_client: KakaoLocalClient | None = None,
    place_client: PetFriendlyPlaceClient | None = None,
    weather_client: WeatherClient | None = None,
    hospital_client: AnimalHospitalClient | None = None,
    pharmacy_client: AnimalPharmacyClient | None = None,
) -> dict:
    try:
        location_text = require_text(location, "location")
        radius = positive_radius(radius_km)
        moment = parse_when(when)
        lat = optional_coordinate(latitude, "latitude", -90, 90)
        lon = optional_coordinate(longitude, "longitude", -180, 180)
    except ValidationError as exc:
        return {"status": "invalid_request", "summary_ko": str(exc), "safety_note_ko": safety_note_ko()}

    geocode_warning = None
    if lat is not None and lon is not None:
        origin = GeoPoint(label=location_text, latitude=lat, longitude=lon, address=location_text)
    else:
        try:
            origin = (kakao_client or KakaoLocalClient()).geocode(location_text)
        except Exception as exc:
            origin = None
            geocode_warning = (
                f"좌표가 제공되지 않았고 카카오 위치 변환을 사용할 수 없어 지역명 '{location_text}' 기준으로 제한된 외출 계획을 만듭니다. "
                f"거리순 장소 추천은 제한됩니다. 확인 내용: {str(exc)}"
            )

    if origin:
        place_result = (place_client or PetFriendlyPlaceClient()).search(origin.latitude, origin.longitude, radius, outing_type)
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
        "source_warnings_ko": ([geocode_warning] if geocode_warning else [])
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
