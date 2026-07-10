from __future__ import annotations

from mypet_life_mcp.clients import KakaoLocalClient, PetBusinessLicenseClient
from mypet_life_mcp.core.korean import safety_note_ko
from mypet_life_mcp.core.normalizer import normalize_address, normalize_text, similarity
from mypet_life_mcp.core.schemas import ValidationError, require_text
from mypet_life_mcp.core.scoring import is_active_status

from .common import item_to_candidate, source_warnings


def verify_pet_business(
    business_name: str,
    region: str | None = None,
    business_type: str | None = "unknown",
    license_client: PetBusinessLicenseClient | None = None,
    kakao_client: KakaoLocalClient | None = None,
) -> dict:
    try:
        name = require_text(business_name, "business_name")
    except ValidationError as exc:
        return {"status": "invalid_request", "summary_ko": str(exc), "safety_note_ko": safety_note_ko()}

    license_result = (license_client or PetBusinessLicenseClient()).search(name, region, business_type)
    license_matches = [item_to_candidate(item, license_result.source) for item in license_result.items]
    map_candidates = []
    map_error = None
    if kakao_client:
        try:
            geo = kakao_client.geocode(region or name)
            map_candidates = kakao_client.keyword_search(name, geo.latitude, geo.longitude)
        except Exception as exc:
            map_error = str(exc)

    status, confidence, matched = _verification_status(name, license_matches, map_candidates)
    notes = _notes(status)
    result = {
        "business_name": name,
        "status": status,
        "confidence": confidence,
        "matched_license": matched.to_dict() if matched else None,
        "map_candidates": map_candidates[:5],
        "source_warnings_ko": source_warnings(license_result) + ([map_error] if map_error else []),
        "verification_notes_ko": notes,
        "questions_to_ask_ko": [
            "인허가 등록명과 실제 운영명이 같은가요?",
            "예약한 서비스가 해당 인허가 범위에 포함되나요?",
            "상주 인력과 응급 시 연계 동물병원이 있나요?",
            "추가 비용, 취소 규정, 분리 공간 운영 방식을 확인할 수 있나요?",
        ],
        "summary_ko": _summary(name, status),
        "safety_note_ko": "인허가 정보 기준 확인 결과이며, 서비스 품질이나 안전을 보장하지 않습니다. 예약 전 직접 확인을 권장합니다.",
    }
    return result


def _verification_status(name: str, licenses: list, map_candidates: list[dict]) -> tuple[str, float, object | None]:
    active = [candidate for candidate in licenses if is_active_status(candidate.business_status)]
    if not active:
        return ("not_found", 0.0, None)
    exact = [candidate for candidate in active if normalize_text(name) in normalize_text(candidate.name)]
    if len(exact) == 1:
        confidence = 0.85
        if map_candidates:
            best_map = max(map_candidates, key=lambda item: similarity(exact[0].address, item.get("address_name") or item.get("road_address_name") or ""))
            if similarity(exact[0].address, best_map.get("address_name") or best_map.get("road_address_name") or "") >= 0.45:
                confidence = 0.95
        return ("verified", confidence, exact[0])
    if len(exact) > 1:
        return ("ambiguous", 0.55, exact[0])
    scored = sorted(active, key=lambda item: similarity(name, item.name) + similarity(normalize_address(item.address), name), reverse=True)
    if scored and similarity(name, scored[0].name) >= 0.35:
        return ("possible_match", 0.6, scored[0])
    return ("not_found", 0.0, None)


def _notes(status: str) -> list[str]:
    notes = {
        "verified": ["공식 인허가 후보에서 이름과 영업 상태가 확인되었습니다.", "실제 서비스 제공 조건은 방문 전 확인이 필요합니다."],
        "possible_match": ["유사한 인허가 후보가 있으나 이름이나 주소가 완전히 일치하지 않습니다.", "업체에 등록명과 인허가 종류를 직접 확인해 주세요."],
        "ambiguous": ["비슷한 후보가 여러 개 있어 하나로 확정하기 어렵습니다.", "주소와 대표 운영명을 추가로 확인해 주세요."],
        "not_found": ["공식 인허가 후보에서 일치 항목을 찾지 못했습니다.", "다른 지역명이나 사업장 등록명으로 다시 확인해 보세요."],
    }
    return notes[status]


def _summary(name: str, status: str) -> str:
    label = {
        "verified": "인허가 정보 기준 확인된 후보입니다.",
        "possible_match": "유사 후보가 있어 추가 확인이 필요합니다.",
        "ambiguous": "후보가 여러 개라 주소 확인이 필요합니다.",
        "not_found": "공식 인허가 후보를 찾지 못했습니다.",
    }[status]
    return f"{name} 업체 확인 결과: {label}"
