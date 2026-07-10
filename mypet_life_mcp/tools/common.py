from __future__ import annotations

from typing import Any

from mypet_life_mcp.core.schemas import Candidate, GeoPoint, SourceResult


def item_to_candidate(item: dict[str, Any], source: str, default_license_type: str = "") -> Candidate:
    name = first_present(item, "name", "사업장명", "업소명", "bplcNm", "title", "place_name")
    name = name or first_present(item, "BPLC_NM")
    address = first_present(item, "address", "소재지전체주소", "도로명전체주소", "addr1", "road_address_name", "address_name")
    address = address or first_present(item, "ROAD_NM_ADDR", "LOTNO_ADDR")
    phone = first_present(item, "phone", "전화번호", "소재지전화", "tel", "phonenum")
    phone = phone or first_present(item, "TELNO")
    status = first_present(item, "business_status", "영업상태명", "상세영업상태명", "trdStateNm", "status")
    status = status or first_present(item, "SALS_STTS_NM", "DTL_SALS_STTS_NM")
    lat = first_present(item, "latitude", "위도", "mapY", "y")
    lon = first_present(item, "longitude", "경도", "mapX", "x")
    license_type = first_present(item, "license_type", "업태구분명", "업종명", "DTL_TASK_SE_NM") or default_license_type
    return Candidate(
        name=str(name or "이름 미확인 후보"),
        address=str(address or ""),
        phone=str(phone or ""),
        business_status=str(status or ""),
        latitude=to_float(lat),
        longitude=to_float(lon),
        source=source,
        license_type=str(license_type or default_license_type),
        raw=item,
    )


def candidates_from_source(result: SourceResult, default_license_type: str = "") -> list[Candidate]:
    return [item_to_candidate(item, result.source, default_license_type) for item in result.items]


def first_present(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return ""


def to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def setup_response(tool: str, location_or_name: str, error_ko: str) -> dict[str, Any]:
    return {
        "tool": tool,
        "status": "setup_required",
        "query": location_or_name,
        "summary_ko": error_ko,
        "safety_note_ko": "환경 변수를 설정한 뒤 다시 조회해 주세요. 임의 정보로 현재 영업 여부를 단정하지 않습니다.",
    }


def source_warnings(*results: SourceResult) -> list[str]:
    return [result.error_ko for result in results if not result.ok and result.error_ko]


def map_place(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": first_present(item, "name", "title", "place_name", "사업장명") or "이름 미확인 장소",
        "address": first_present(item, "address", "addr1", "road_address_name", "address_name", "소재지전체주소"),
        "phone": first_present(item, "phone", "tel", "phonenum", "전화번호"),
        "pet_policy": first_present(item, "pet_policy", "relaAcdntRiskMtr", "acmpyTypeCd", "동반정보"),
        "source": first_present(item, "source") or "공공데이터",
    }
