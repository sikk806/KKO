from __future__ import annotations

import re
from typing import Any

from mypet_life_mcp.core.schemas import SourceResult, ValidationError


SPECIES_ALIASES = {
    "dog": {"dog", "dogs", "강아지", "개", "반려견", "댕댕이"},
    "cat": {"cat", "cats", "고양이", "반려묘", "냥이"},
}


def normalize_species(value: str) -> str:
    lowered = value.strip().lower()
    for species, aliases in SPECIES_ALIASES.items():
        if lowered in aliases:
            return species
    raise ValidationError("pet_type은 dog/강아지/개/반려견 또는 cat/고양이/반려묘만 지원합니다.")


def positive_optional(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name}은 숫자로 입력해 주세요.") from exc
    if parsed <= 0:
        raise ValidationError(f"{field_name}은 0보다 커야 합니다.")
    return parsed


def ingredient_candidates(food: str, result: SourceResult) -> list[dict[str, str]]:
    candidates = [{"name": food, "role": "primary"}]
    if result.ok:
        for item in result.items:
            raw = str(item.get("RAWMTRL_NM") or "").strip()
            for name in split_ingredient(raw):
                candidates.append({"name": name, "role": "ingredient"})
    return dedupe_candidates(candidates)


def split_ingredient(raw: str) -> list[str]:
    for token in (";", "\n", "\r", "|"):
        raw = raw.replace(token, ",")
    return [part.strip() for part in raw.split(",") if part.strip()]


def dedupe_candidates(values: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for value in values:
        key = compact(value["name"])
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = compact(value)
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def compact(value: str) -> str:
    return re.sub(r"[\s\-_()/\[\],.?!~]+", "", value).lower()


def evidence_status(evidence: list[dict[str, Any]], species: str) -> str:
    if any(item.get("species") == species for item in evidence):
        return "SPECIES_REFERENCE_FOUND"
    if evidence:
        return "GENERAL_REFERENCE_FOUND"
    return "NO_REFERENCE_FOUND"


def source_rows(product_result: SourceResult, ingredients: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [source_row(product_result)]
    for ingredient in ingredients:
        rows.append(source_row(ingredient.pop("_source")))
    unique: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row["source"]
        if key not in unique or (unique[key]["ok"] and not row["ok"]):
            unique[key] = row
    return list(unique.values())


def source_row(result: SourceResult) -> dict[str, Any]:
    return {"source": result.source, "ok": result.ok, "error_ko": result.error_ko}


def warnings(sources: list[dict[str, Any]]) -> list[str]:
    return [f"{item['source']} source를 사용할 수 없습니다: {item.get('error_ko')}" for item in sources if not item["ok"]]


def food_safety_fallback_notices(product_result: SourceResult) -> list[str]:
    has_raw_material = product_result.ok and any(
        str(item.get("RAWMTRL_NM") or "").strip() for item in product_result.items
    )
    if has_raw_material:
        return []
    if product_result.ok:
        return ["식품안전나라에서 해당 제품/음식의 원재료 결과를 찾지 못해 입력한 음식명을 기준으로 확인했습니다."]
    return ["식품안전나라 OpenAPI 조회가 실패하거나 제한되어 입력한 음식명을 기준으로 확인했습니다."]

