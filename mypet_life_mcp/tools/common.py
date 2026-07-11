from __future__ import annotations

from typing import Any

from mypet_life_mcp.core.schemas import Candidate, GeoPoint, SourceResult


PROVINCE_ALIASES = {
    "서울시": "서울특별시",
    "서울": "서울특별시",
    "서울특별시": "서울특별시",
    "부산시": "부산광역시",
    "부산": "부산광역시",
    "부산광역시": "부산광역시",
    "대구시": "대구광역시",
    "대구": "대구광역시",
    "대구광역시": "대구광역시",
    "인천시": "인천광역시",
    "인천": "인천광역시",
    "인천광역시": "인천광역시",
    "광주시": "광주광역시",
    "광주": "광주광역시",
    "광주광역시": "광주광역시",
    "대전시": "대전광역시",
    "대전": "대전광역시",
    "대전광역시": "대전광역시",
    "울산시": "울산광역시",
    "울산": "울산광역시",
    "울산광역시": "울산광역시",
    "세종시": "세종특별자치시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "경기도": "경기도",
    "강원": "강원특별자치도",
    "강원도": "강원특별자치도",
    "강원특별자치도": "강원특별자치도",
    "충북": "충청북도",
    "충북도": "충청북도",
    "충청북도": "충청북도",
    "충남": "충청남도",
    "충남도": "충청남도",
    "충청남도": "충청남도",
    "전북": "전북특별자치도",
    "전북도": "전북특별자치도",
    "전라북도": "전북특별자치도",
    "전북특별자치도": "전북특별자치도",
    "전남": "전라남도",
    "전남도": "전라남도",
    "전라남도": "전라남도",
    "경북": "경상북도",
    "경북도": "경상북도",
    "경상북도": "경상북도",
    "경남": "경상남도",
    "경남도": "경상남도",
    "경상남도": "경상남도",
    "제주": "제주특별자치도",
    "제주도": "제주특별자치도",
    "제주특별자치도": "제주특별자치도",
    "제주시": "제주특별자치도 제주시",
}

SIGUNGU_BY_PROVINCE = {
    "서울특별시": [
        "강남구",
        "강동구",
        "강북구",
        "강서구",
        "관악구",
        "광진구",
        "구로구",
        "금천구",
        "노원구",
        "도봉구",
        "동대문구",
        "동작구",
        "마포구",
        "서대문구",
        "서초구",
        "성동구",
        "성북구",
        "송파구",
        "양천구",
        "영등포구",
        "용산구",
        "은평구",
        "종로구",
        "중구",
        "중랑구",
    ],
    "부산광역시": [
        "강서구",
        "금정구",
        "기장군",
        "남구",
        "동구",
        "동래구",
        "부산진구",
        "북구",
        "사상구",
        "사하구",
        "서구",
        "수영구",
        "연제구",
        "영도구",
        "중구",
        "해운대구",
    ],
    "대구광역시": ["군위군", "남구", "달서구", "달성군", "동구", "북구", "서구", "수성구", "중구"],
    "인천광역시": ["강화군", "계양구", "남동구", "동구", "미추홀구", "부평구", "서구", "연수구", "옹진군", "중구"],
    "광주광역시": ["광산구", "남구", "동구", "북구", "서구"],
    "대전광역시": ["대덕구", "동구", "서구", "유성구", "중구"],
    "울산광역시": ["남구", "동구", "북구", "울주군", "중구"],
    "경기도": [
        "가평군",
        "고양시",
        "과천시",
        "광명시",
        "광주시",
        "구리시",
        "군포시",
        "김포시",
        "남양주시",
        "동두천시",
        "부천시",
        "성남시",
        "수원시",
        "시흥시",
        "안산시",
        "안성시",
        "안양시",
        "양주시",
        "양평군",
        "여주시",
        "연천군",
        "오산시",
        "용인시",
        "의왕시",
        "의정부시",
        "이천시",
        "파주시",
        "평택시",
        "포천시",
        "하남시",
        "화성시",
    ],
    "강원특별자치도": [
        "강릉시",
        "고성군",
        "동해시",
        "삼척시",
        "속초시",
        "양구군",
        "양양군",
        "영월군",
        "원주시",
        "인제군",
        "정선군",
        "철원군",
        "춘천시",
        "태백시",
        "평창군",
        "홍천군",
        "화천군",
        "횡성군",
    ],
    "충청북도": [
        "괴산군",
        "단양군",
        "보은군",
        "영동군",
        "옥천군",
        "음성군",
        "제천시",
        "증평군",
        "진천군",
        "청주시",
        "충주시",
    ],
    "충청남도": [
        "계룡시",
        "공주시",
        "금산군",
        "논산시",
        "당진시",
        "보령시",
        "부여군",
        "서산시",
        "서천군",
        "아산시",
        "예산군",
        "천안시",
        "청양군",
        "태안군",
        "홍성군",
    ],
    "전북특별자치도": [
        "고창군",
        "군산시",
        "김제시",
        "남원시",
        "무주군",
        "부안군",
        "순창군",
        "완주군",
        "익산시",
        "임실군",
        "장수군",
        "전주시",
        "정읍시",
        "진안군",
    ],
    "전라남도": [
        "강진군",
        "고흥군",
        "곡성군",
        "광양시",
        "구례군",
        "나주시",
        "담양군",
        "목포시",
        "무안군",
        "보성군",
        "순천시",
        "신안군",
        "여수시",
        "영광군",
        "영암군",
        "완도군",
        "장성군",
        "장흥군",
        "진도군",
        "함평군",
        "해남군",
        "화순군",
    ],
    "경상북도": [
        "경산시",
        "경주시",
        "고령군",
        "구미시",
        "김천시",
        "문경시",
        "봉화군",
        "상주시",
        "성주군",
        "안동시",
        "영덕군",
        "영양군",
        "영주시",
        "영천시",
        "예천군",
        "울릉군",
        "울진군",
        "의성군",
        "청도군",
        "청송군",
        "칠곡군",
        "포항시",
    ],
    "경상남도": [
        "거제시",
        "거창군",
        "고성군",
        "김해시",
        "남해군",
        "밀양시",
        "사천시",
        "산청군",
        "양산시",
        "의령군",
        "진주시",
        "창녕군",
        "창원시",
        "통영시",
        "하동군",
        "함안군",
        "함양군",
        "합천군",
    ],
    "제주특별자치도": ["제주시", "서귀포시"],
}

SIGUNGU_SUFFIXES = ("시", "군", "구")

REGION_CENTROIDS = {
    "서울특별시": (37.5665, 126.9780),
    "서울특별시 강남구": (37.5172, 127.0473),
    "서울특별시 강동구": (37.5301, 127.1238),
    "서울특별시 강북구": (37.6396, 127.0257),
    "서울특별시 강서구": (37.5509, 126.8495),
    "서울특별시 관악구": (37.4784, 126.9516),
    "서울특별시 광진구": (37.5384, 127.0823),
    "서울특별시 구로구": (37.4955, 126.8877),
    "서울특별시 금천구": (37.4569, 126.8955),
    "서울특별시 노원구": (37.6542, 127.0568),
    "서울특별시 도봉구": (37.6688, 127.0471),
    "서울특별시 동대문구": (37.5744, 127.0396),
    "서울특별시 동작구": (37.5124, 126.9393),
    "서울특별시 마포구": (37.5663, 126.9018),
    "서울특별시 서대문구": (37.5791, 126.9368),
    "서울특별시 서초구": (37.4837, 127.0324),
    "서울특별시 성동구": (37.5633, 127.0371),
    "서울특별시 성북구": (37.5894, 127.0167),
    "서울특별시 송파구": (37.5145, 127.1059),
    "서울특별시 양천구": (37.5169, 126.8664),
    "서울특별시 영등포구": (37.5264, 126.8963),
    "서울특별시 용산구": (37.5326, 126.9900),
    "서울특별시 은평구": (37.6027, 126.9291),
    "서울특별시 종로구": (37.5735, 126.9788),
    "서울특별시 중구": (37.5638, 126.9976),
    "서울특별시 중랑구": (37.6063, 127.0927),
    "부산광역시": (35.1796, 129.0756),
    "부산광역시 해운대구": (35.1631, 129.1636),
    "대구광역시": (35.8714, 128.6014),
    "인천광역시": (37.4563, 126.7052),
    "광주광역시": (35.1595, 126.8526),
    "대전광역시": (36.3504, 127.3845),
    "울산광역시": (35.5384, 129.3114),
    "세종특별자치시": (36.4800, 127.2890),
    "경기도": (37.4138, 127.5183),
    "강원특별자치도": (37.8228, 128.1555),
    "충청북도": (36.8000, 127.7000),
    "충청남도": (36.5184, 126.8000),
    "전북특별자치도": (35.7175, 127.1530),
    "전라남도": (34.8161, 126.4629),
    "경상북도": (36.4919, 128.8889),
    "경상남도": (35.4606, 128.2132),
    "제주특별자치도": (33.4996, 126.5312),
}


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
        return None
    latitude, longitude = coordinates
    return GeoPoint(label=normalized, latitude=latitude, longitude=longitude, address=normalized)


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
