from __future__ import annotations

from mypet_life_mcp.clients import AnimalHospitalClient, AnimalPharmacyClient, HolidayClient, KakaoLocalClient
from mypet_life_mcp.core.korean import safety_note_ko
from mypet_life_mcp.core.schemas import GeoPoint, ValidationError, optional_coordinate, parse_when, positive_radius, require_text
from mypet_life_mcp.core.scoring import enrich_distance, is_holiday_or_night, rank_candidates

from .common import candidates_from_source, setup_response, source_warnings


def find_pet_emergency_candidates(
    location: str,
    pet_type: str | None = None,
    situation: str | None = None,
    radius_km: float | None = 5.0,
    when: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    kakao_client: KakaoLocalClient | None = None,
    hospital_client: AnimalHospitalClient | None = None,
    pharmacy_client: AnimalPharmacyClient | None = None,
    holiday_client: HolidayClient | None = None,
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
        kakao = kakao_client or KakaoLocalClient()
        try:
            origin = kakao.geocode(location_text)
        except Exception as exc:
            origin = None
            geocode_warning = (
                f"좌표가 제공되지 않았고 카카오 위치 변환을 사용할 수 없어 지역명 '{location_text}' 기준으로만 후보를 조회합니다. "
                f"거리순 정렬은 제한됩니다. 확인 내용: {str(exc)}"
            )

    holiday_result = (holiday_client or HolidayClient()).check(moment.date())
    holiday = bool(holiday_result.items and holiday_result.items[0].get("is_holiday"))
    search_region = origin.address if origin and origin.address else location_text
    hospital_result = (hospital_client or AnimalHospitalClient()).search(search_region, radius)
    pharmacy_result = (pharmacy_client or AnimalPharmacyClient()).search(search_region, radius)
    hospital_candidates = candidates_from_source(hospital_result, "동물병원")
    pharmacy_candidates = candidates_from_source(pharmacy_result, "동물약국")
    if origin:
        hospital_candidates = enrich_distance(hospital_candidates, origin)
        pharmacy_candidates = enrich_distance(pharmacy_candidates, origin)
    hospitals = rank_candidates(hospital_candidates, "hospital", situation)[:10]
    pharmacies = rank_candidates(pharmacy_candidates, "pharmacy", situation)[:10]
    night_mode = is_holiday_or_night(moment, holiday)
    call_script = _call_script(pet_type, situation)
    mode = "holiday_or_night_candidates" if night_mode else "regular_candidates"
    summary = (
        f"{location_text} 주변의 동물병원과 동물약국 후보를 정리했습니다. "
        "현재 진료나 조제 가능 여부는 보장하지 않으므로 먼저 전화 확인이 필요합니다."
    )
    if night_mode:
        summary = (
            f"{location_text} 기준 휴일/야간/주말 가능성이 있는 시간대로 판단되어 먼저 연락할 후보를 정리했습니다. "
            "실제 접수 가능 여부는 전화 확인이 필요합니다."
        )
    return {
        "mode": mode,
        "location": location_text,
        "resolved_location": origin.address if origin else None,
        "location_precision": "provided_coordinate" if lat is not None and lon is not None else ("coordinate" if origin else "region_text_only"),
        "is_holiday_or_night": night_mode,
        "animal_hospitals": [candidate.to_dict() for candidate in hospitals],
        "animal_pharmacies": [candidate.to_dict() for candidate in pharmacies],
        "source_warnings_ko": ([geocode_warning] if geocode_warning else [])
        + source_warnings(holiday_result, hospital_result, pharmacy_result),
        "summary_ko": summary,
        "call_script_ko": call_script,
        "safety_note_ko": safety_note_ko(),
    }


def _call_script(pet_type: str | None, situation: str | None) -> str:
    pet = pet_type or "반려동물"
    symptom = situation or "상태가 좋지 않은 상황"
    return (
        f"안녕하세요. {pet} 때문에 문의드립니다. 현재 {symptom} 상태인데 지금 진료 또는 상담 접수가 가능한가요? "
        "접수 마감 시간, 대기 시간, 준비해서 가야 할 내용을 알려주실 수 있을까요?"
    )
