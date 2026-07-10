from __future__ import annotations

from datetime import datetime
from typing import Iterable

from .geo import haversine_km
from .normalizer import normalize_address, normalize_text
from .schemas import Candidate, GeoPoint

HOSPITAL_HINT_KEYWORDS = ("24", "응급", "야간", "동물의료센터", "메디컬센터", "센터")
ACTIVE_STATUS_KEYWORDS = ("정상", "영업", "운영", "open", "active")
INACTIVE_STATUS_KEYWORDS = ("폐업", "말소", "취소", "휴업", "closed", "inactive", "종료")
MEDICINE_KEYWORDS = ("약", "medicine", "pharmacy", "처방", "구충", "심장사상충")


def is_active_status(status: str | None) -> bool:
    normalized = normalize_text(status)
    if not normalized:
        return True
    if any(keyword in normalized for keyword in map(normalize_text, INACTIVE_STATUS_KEYWORDS)):
        return False
    return True


def has_active_hint(status: str | None) -> bool:
    normalized = normalize_text(status)
    return any(keyword in normalized for keyword in map(normalize_text, ACTIVE_STATUS_KEYWORDS))


def dedupe_candidates(candidates: Iterable[Candidate]) -> list[Candidate]:
    seen: set[tuple[str, str]] = set()
    deduped: list[Candidate] = []
    for candidate in candidates:
        key = (normalize_text(candidate.name), normalize_address(candidate.address))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def enrich_distance(candidates: list[Candidate], origin: GeoPoint) -> list[Candidate]:
    for candidate in candidates:
        if candidate.latitude is not None and candidate.longitude is not None:
            candidate.distance_km = haversine_km(origin.latitude, origin.longitude, candidate.latitude, candidate.longitude)
    return candidates


def candidate_score(candidate: Candidate, kind: str, situation: str | None = None) -> float:
    score = 0.0
    if is_active_status(candidate.business_status):
        score += 30
    if has_active_hint(candidate.business_status):
        score += 5
    if candidate.distance_km is not None:
        score += max(0, 25 - candidate.distance_km * 3)
    if candidate.phone:
        score += 10
    normalized_name = normalize_text(candidate.name)
    keyword_hits = [kw for kw in HOSPITAL_HINT_KEYWORDS if normalize_text(kw) in normalized_name]
    score += min(20, len(keyword_hits) * 5)
    normalized_situation = normalize_text(situation)
    if kind == "hospital" and not any(normalize_text(kw) in normalized_situation for kw in MEDICINE_KEYWORDS):
        score += 8
    if kind == "pharmacy" and any(normalize_text(kw) in normalized_situation for kw in MEDICINE_KEYWORDS):
        score += 8
    return score


def rank_candidates(candidates: list[Candidate], kind: str, situation: str | None = None) -> list[Candidate]:
    active = [candidate for candidate in dedupe_candidates(candidates) if is_active_status(candidate.business_status)]
    ranked = sorted(active, key=lambda item: candidate_score(item, kind, situation), reverse=True)
    for index, candidate in enumerate(ranked):
        score = candidate_score(candidate, kind, situation)
        candidate.priority = "high" if index < 3 and score >= 45 else "medium"
        reasons = []
        if candidate.distance_km is not None:
            reasons.append(f"검색 위치에서 약 {candidate.distance_km}km 거리입니다.")
        if has_active_hint(candidate.business_status) or not candidate.business_status:
            reasons.append("인허가 정보 기준 영업 상태가 유효한 후보입니다.")
        if any(normalize_text(kw) in normalize_text(candidate.name) for kw in HOSPITAL_HINT_KEYWORDS):
            reasons.append("이름에 24시/응급/야간 관련 힌트가 있습니다. 단, 운영 보장은 아닙니다.")
        if candidate.phone:
            reasons.append("전화번호가 있어 방문 전 확인에 도움이 됩니다.")
        candidate.ranking_reasons = reasons or ["공공데이터 기준으로 확인된 후보입니다."]
        candidate.verification_needed = [
            "현재 접수 가능 여부",
            "접수 마감 시간",
            "해당 동물과 상황 상담 가능 여부",
        ]
    return ranked


def is_holiday_or_night(moment: datetime, holiday: bool = False) -> bool:
    hour = moment.hour
    return holiday or moment.weekday() >= 5 or hour < 9 or hour >= 18


def outing_score(weather: dict, places: list[dict], hospitals: list[Candidate]) -> tuple[int, list[str]]:
    score = 100
    cautions: list[str] = []
    rain_probability = int(weather.get("rain_probability", 0) or 0)
    precipitation = float(weather.get("precipitation_mm", 0) or 0)
    temperature = weather.get("temperature_c")
    wind = float(weather.get("wind_mps", 0) or 0)

    if rain_probability >= 60 or precipitation >= 5:
        score -= 20
        cautions.append("비 예보가 있어 실내 동선이나 짧은 산책을 권장합니다.")
    if temperature is not None and (float(temperature) >= 30 or float(temperature) <= 0):
        score -= 15
        cautions.append("기온 조건이 부담될 수 있어 이동 시간과 체온 관리가 필요합니다.")
    if wind >= 8:
        score -= 8
        cautions.append("바람이 강할 수 있어 야외 체류 시간을 줄이는 편이 좋습니다.")
    if not hospitals:
        score -= 10
        cautions.append("근처 동물병원 후보가 확인되지 않아 이동 전 별도 확인이 필요합니다.")
    if not places or any(not place.get("pet_policy") for place in places):
        score -= 10
        cautions.append("반려동물 동반 조건이 불명확한 장소가 있어 방문 전 확인을 권장합니다.")
    return max(0, min(100, score)), cautions
