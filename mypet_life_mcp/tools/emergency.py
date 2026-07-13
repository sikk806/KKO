from __future__ import annotations

from mypet_life_mcp.clients import AnimalHospitalClient, AnimalPharmacyClient, HolidayClient
from mypet_life_mcp.core.korean import safety_note_ko
from mypet_life_mcp.core.schemas import (
    GeoPoint,
    ValidationError,
    optional_coordinate,
    parse_when_options,
    positive_radius,
    require_text,
)
from mypet_life_mcp.core.scoring import enrich_distance, is_holiday_or_night, rank_candidates

from .common import (
    candidates_from_source,
    location_basis_warning,
    normalize_region_name,
    region_centroid,
    search_region_for_origin,
    source_warnings,
)
from .emergency_fallbacks import EMERGENCY_FALLBACK_SOURCE, emergency_hospital_fallbacks


def find_pet_emergency_candidates(
    location: str,
    pet_type: str | None = None,
    situation: str | None = None,
    radius_km: float | None = 5.0,
    when: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    hospital_client: AnimalHospitalClient | None = None,
    pharmacy_client: AnimalPharmacyClient | None = None,
    holiday_client: HolidayClient | None = None,
) -> dict:
    try:
        location_text = normalize_region_name(require_text(location, "location"))
        radius = positive_radius(radius_km)
        moments = parse_when_options(when)
        moment = moments[0]
        lat = optional_coordinate(latitude, "latitude", -90, 90)
        lon = optional_coordinate(longitude, "longitude", -180, 180)
    except ValidationError as exc:
        return {"status": "invalid_request", "summary_ko": str(exc), "safety_note_ko": safety_note_ko()}

    location_warning = None
    if lat is not None and lon is not None:
        origin = GeoPoint(label=location_text, latitude=lat, longitude=lon, address=location_text)
    else:
        origin = region_centroid(location_text)
        location_warning = location_basis_warning(location_text, origin, "후보를 정리합니다.")

    holiday_api = holiday_client or HolidayClient()
    holiday_results = [holiday_api.check(item.date()) for item in moments]
    holiday_result = holiday_results[0]
    holiday_flags = [bool(result.items and result.items[0].get("is_holiday")) for result in holiday_results]
    search_region = search_region_for_origin(origin, location_text)
    hospital_result = (hospital_client or AnimalHospitalClient()).search(search_region, radius)
    pharmacy_result = (pharmacy_client or AnimalPharmacyClient()).search(search_region, radius)
    original_hospital_result = hospital_result
    fallback_warning = None
    if not hospital_result.ok or not hospital_result.items:
        fallback_items = emergency_hospital_fallbacks(location_text, origin)
        if fallback_items:
            hospital_result = type(hospital_result)(items=fallback_items, source=EMERGENCY_FALLBACK_SOURCE)
            fallback_warning = "공공데이터 병원 조회가 실패했거나 후보가 부족해 내장 응급 연락 후보를 함께 제시합니다. 현재 진료 가능 여부는 전화 확인이 필요합니다."
    hospital_candidates = candidates_from_source(hospital_result, "동물병원")
    pharmacy_candidates = candidates_from_source(pharmacy_result, "동물약국")
    if origin:
        hospital_candidates = enrich_distance(hospital_candidates, origin)
        pharmacy_candidates = enrich_distance(pharmacy_candidates, origin)
    hospitals = rank_candidates(hospital_candidates, "hospital", situation)[:10]
    pharmacies = rank_candidates(pharmacy_candidates, "pharmacy", situation)[:10]
    night_mode = any(is_holiday_or_night(item, holiday) for item, holiday in zip(moments, holiday_flags))
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
        "resolved_when": moment.isoformat(),
        "resolved_when_options": [item.isoformat() for item in moments],
        "location_precision": "provided_coordinate" if lat is not None and lon is not None else ("coordinate" if origin else "region_text_only"),
        "is_holiday_or_night": night_mode,
        "animal_hospitals": [candidate.to_dict() for candidate in hospitals],
        "animal_pharmacies": [candidate.to_dict() for candidate in pharmacies],
        "source_warnings_ko": ([location_warning] if location_warning else [])
        + ([fallback_warning] if fallback_warning else [])
        + source_warnings(*holiday_results, original_hospital_result, pharmacy_result),
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
