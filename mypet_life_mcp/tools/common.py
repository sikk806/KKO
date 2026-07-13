from __future__ import annotations

from datetime import datetime
from typing import Any

from mypet_life_mcp.core.schemas import Candidate, GeoPoint, KST, SourceResult, ValidationError

from .region_data import PROVINCE_ALIASES, REGION_CENTROIDS, SIGUNGU_BY_PROVINCE, SIGUNGU_SUFFIXES
from .station_locations import station_centroid

DEFAULT_LOCATION_CHOICES = (
    "서울특별시",
    "부산광역시 해운대구",
    "인천광역시 부평구",
    "제주특별자치도 제주시",
    "대전광역시",
)
EMPTY_LOCATION_HINTS = {"", "어디든", "아무데나", "랜덤", "상관없어", "장소없음", "지역없음"}
STATION_QUERY_SUFFIXES = ("근처", "주변", "인근", "부근", "앞", "쪽", "에서", "으로", "까지")


def resolve_location_text(location: Any) -> tuple[str, bool]:
    if location is None:
        return _default_location(), True
    if not isinstance(location, str):
        raise ValidationError("location 값이 필요합니다.")
    text = " ".join(location.strip().split())
    compact = text.replace(" ", "").lower()
    if compact in EMPTY_LOCATION_HINTS:
        return _default_location(), True
    if _looks_like_unknown_station(text):
        raise ValidationError(f"'{text}' 역명을 찾을 수 없습니다. 역명을 다시 확인해 주세요.")
    return normalize_region_name(text), False


def default_location_warning(location: str, action_ko: str) -> str:
    return f"장소가 지정되지 않아 자동 추천 지역 '{location}' 기준으로 {action_ko}"


def _default_location() -> str:
    index = datetime.now(KST).timetuple().tm_yday % len(DEFAULT_LOCATION_CHOICES)
    return DEFAULT_LOCATION_CHOICES[index]


def _looks_like_unknown_station(location: str) -> bool:
    compact = location.replace(" ", "")
    for suffix in STATION_QUERY_SUFFIXES:
        if compact.endswith(suffix):
            compact = compact[: -len(suffix)]
            break
    return compact.endswith("역") and station_centroid(location) is None


def normalize_region_name(location: str) -> str:
    text = " ".join(location.strip().split())
    compact = text.replace(" ", "")
    if compact in PROVINCE_ALIASES:
        return PROVINCE_ALIASES[compact]

    for alias, province in PROVINCE_ALIASES.items():
        if compact.startswith(alias) and compact != alias:
            tail = compact[len(alias) :]
            matched = _match_sigungu(province, tail)
            if matched:
                return f"{province} {matched}"

    unique = _unique_sigungu(compact)
    if unique:
        province, sigungu = unique
        return f"{province} {sigungu}"

    return text


def _match_sigungu(province: str, value: str) -> str | None:
    candidates = SIGUNGU_BY_PROVINCE.get(province, [])
    for sigungu in candidates:
        stripped = _strip_sigungu_suffix(sigungu)
        if value == sigungu or value == stripped or value.startswith(sigungu) or value.startswith(stripped):
            return sigungu
    return None


def _unique_sigungu(value: str) -> tuple[str, str] | None:
    matches = []
    for province, candidates in SIGUNGU_BY_PROVINCE.items():
        for sigungu in candidates:
            if value == sigungu or value == _strip_sigungu_suffix(sigungu):
                matches.append((province, sigungu))
    return matches[0] if len(matches) == 1 else None


def _strip_sigungu_suffix(value: str) -> str:
    if value.endswith(SIGUNGU_SUFFIXES):
        return value[:-1]
    return value


def region_centroid(location: str) -> GeoPoint | None:
    normalized = normalize_region_name(location)
    coordinates = REGION_CENTROIDS.get(normalized)
    if coordinates is None:
        province = normalized.split(" ", 1)[0]
        coordinates = REGION_CENTROIDS.get(province)
    if coordinates is None:
        return station_centroid(location)
    latitude, longitude = coordinates
    return GeoPoint(label=normalized, latitude=latitude, longitude=longitude, address=normalized)


def location_basis_warning(location: str, origin: GeoPoint | None, action_ko: str) -> str:
    if origin and origin.label.endswith("역"):
        return f"'{location}' 입력을 {origin.label} 위치 좌표 기준으로 {action_ko}"
    if origin:
        return f"정확한 주소 좌표가 없어 '{location}' 지역 중심 기준으로 {action_ko}"
    return f"좌표가 없어 지역명 '{location}' 기준으로 {action_ko} 거리순 정렬은 제한됩니다."


def search_region_for_origin(origin: GeoPoint | None, fallback: str) -> str:
    if not origin or not origin.address:
        return fallback
    parts = origin.address.split()
    if len(parts) >= 2 and parts[1].endswith(SIGUNGU_SUFFIXES):
        return " ".join(parts[:2])
    return origin.address


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
