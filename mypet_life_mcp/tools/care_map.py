from __future__ import annotations

from mypet_life_mcp.clients import AnimalHospitalClient, AnimalPharmacyClient, KakaoLocalClient
from mypet_life_mcp.core.korean import confirmation_note_ko, safety_note_ko
from mypet_life_mcp.core.schemas import GeoPoint, ValidationError, optional_coordinate, positive_radius, require_text
from mypet_life_mcp.core.scoring import enrich_distance, rank_candidates

from .common import candidates_from_source, setup_response, source_warnings


def make_pet_care_map(
    location: str,
    radius_km: float | None = 5.0,
    include_pharmacies: bool = True,
    latitude: float | None = None,
    longitude: float | None = None,
    kakao_client: KakaoLocalClient | None = None,
    hospital_client: AnimalHospitalClient | None = None,
    pharmacy_client: AnimalPharmacyClient | None = None,
) -> dict:
    try:
        location_text = require_text(location, "location")
        radius = positive_radius(radius_km)
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
                f"좌표가 제공되지 않았고 카카오 위치 변환을 사용할 수 없어 지역명 '{location_text}' 기준으로만 후보를 조회합니다. "
                f"거리순 정렬은 제한됩니다. 확인 내용: {str(exc)}"
            )

    search_region = origin.address if origin and origin.address else location_text
    hospital_result = (hospital_client or AnimalHospitalClient()).search(search_region, radius)
    hospital_candidates = candidates_from_source(hospital_result, "동물병원")
    if origin:
        hospital_candidates = enrich_distance(hospital_candidates, origin)
    hospitals = rank_candidates(hospital_candidates, "hospital")[:12]
    pharmacy_result = None
    pharmacies = []
    if include_pharmacies:
        pharmacy_result = (pharmacy_client or AnimalPharmacyClient()).search(search_region, radius)
        pharmacy_candidates = candidates_from_source(pharmacy_result, "동물약국")
        if origin:
            pharmacy_candidates = enrich_distance(pharmacy_candidates, origin)
        pharmacies = rank_candidates(pharmacy_candidates, "pharmacy")[:12]
    warnings = source_warnings(hospital_result, pharmacy_result) if pharmacy_result else source_warnings(hospital_result)
    return {
        "mode": "pet_care_map",
        "location": location_text,
        "resolved_location": origin.address if origin else None,
        "location_precision": "provided_coordinate" if lat is not None and lon is not None else ("coordinate" if origin else "region_text_only"),
        "radius_km": radius,
        "animal_hospitals": [candidate.to_dict() for candidate in hospitals],
        "animal_pharmacies": [candidate.to_dict() for candidate in pharmacies],
        "source_warnings_ko": ([geocode_warning] if geocode_warning else []) + warnings,
        "summary_ko": f"{location_text} 주변의 동물병원과 동물약국 후보를 지도/공공데이터 기준으로 정리했습니다. {confirmation_note_ko()}",
        "safety_note_ko": safety_note_ko(),
    }
