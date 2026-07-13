from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo


class ValidationError(ValueError):
    """Raised when tool input is invalid."""


KST = ZoneInfo("Asia/Seoul")


@dataclass(frozen=True)
class GeoPoint:
    label: str
    latitude: float
    longitude: float
    address: str = ""


@dataclass
class Candidate:
    name: str
    address: str = ""
    phone: str = ""
    business_status: str = ""
    latitude: float | None = None
    longitude: float | None = None
    source: str = ""
    license_type: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    distance_km: float | None = None
    priority: str = "medium"
    ranking_reasons: list[str] = field(default_factory=list)
    verification_needed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "priority": self.priority,
            "distance_km": self.distance_km,
            "address": self.address,
            "phone": self.phone,
            "business_status": self.business_status,
            "source": self.source,
            "license_type": self.license_type,
            "ranking_reasons_ko": self.ranking_reasons,
            "verification_needed_ko": self.verification_needed,
        }


@dataclass
class SourceResult:
    items: list[dict[str, Any]]
    source: str
    ok: bool = True
    error_ko: str | None = None


def require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} 값이 필요합니다.")
    return value.strip()


def positive_radius(value: Any, default: float = 5.0) -> float:
    if value is None:
        return default
    try:
        radius = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("radius_km은 숫자로 입력해 주세요.") from exc
    if radius <= 0 or radius > 50:
        raise ValidationError("radius_km은 0보다 크고 50 이하로 입력해 주세요.")
    return radius


def optional_coordinate(value: Any, field_name: str, minimum: float, maximum: float) -> float | None:
    if value is None or value == "":
        return None
    try:
        coordinate = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name}은 숫자로 입력해 주세요.") from exc
    if coordinate < minimum or coordinate > maximum:
        raise ValidationError(f"{field_name} 값의 범위가 올바르지 않습니다.")
    return coordinate


def parse_when(value: str | None, now: datetime | None = None) -> datetime:
    base = _kst_now(now)
    if not value:
        return base
    natural = value.strip().lower()
    compact = natural.replace(" ", "")
    if natural in {"now", "current", "today", "지금", "현재", "오늘"}:
        return base
    if compact in {"tonight", "야간", "오늘밤"}:
        return datetime.combine(base.date(), time(hour=21), tzinfo=KST)
    if compact in {"tomorrow", "내일"}:
        return datetime.combine(base.date() + timedelta(days=1), time(hour=12), tzinfo=KST)
    if compact in {"모레"}:
        return datetime.combine(base.date() + timedelta(days=2), time(hour=12), tzinfo=KST)
    if "주말" in compact or compact in {"weekend"}:
        hour = 21 if _has_night_hint(compact) else 12
        skip_this_week = "다음" in compact or "next" in compact
        return _next_weekday(base, 5, hour=hour, include_today=not skip_this_week)
    if _has_weekday_hint(compact, "saturday", "토요일", "토욜"):
        return _next_weekday(base, 5, hour=21 if _has_night_hint(compact) else 12)
    if _has_weekday_hint(compact, "sunday", "일요일", "일욜"):
        return _next_weekday(base, 6, hour=21 if _has_night_hint(compact) else 12)
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=KST)
        return parsed
    except ValueError as exc:
        raise ValidationError("when은 ISO 날짜/시간 형식으로 입력해 주세요.") from exc


def _kst_now(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(KST)
    if now.tzinfo is None:
        return now.replace(tzinfo=KST)
    return now.astimezone(KST)


def _next_weekday(base: datetime, weekday: int, hour: int = 12, include_today: bool = True) -> datetime:
    days = (weekday - base.weekday()) % 7
    if days == 0 and not include_today:
        days = 7
    target_day = base.date() + timedelta(days=days)
    return datetime.combine(target_day, time(hour=hour), tzinfo=KST)


def _has_night_hint(text: str) -> bool:
    return any(hint in text for hint in ("밤", "야간", "저녁", "night", "evening"))


def _has_weekday_hint(text: str, *hints: str) -> bool:
    return any(hint in text for hint in hints)
