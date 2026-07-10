from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Any


class ValidationError(ValueError):
    """Raised when tool input is invalid."""


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


def parse_when(value: str | None) -> datetime:
    if not value:
        return datetime.now().astimezone()
    natural = value.strip().lower()
    if natural in {"now", "current", "today", "지금", "현재", "오늘"}:
        return datetime.now().astimezone()
    if natural in {"tonight", "야간", "오늘 밤", "오늘밤"}:
        today = datetime.now().astimezone().date()
        return datetime.combine(today, time(hour=21)).astimezone()
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValidationError("when은 ISO 날짜/시간 형식으로 입력해 주세요.") from exc
