from __future__ import annotations

from typing import Any

from mypet_life_mcp.clients import FoodSafetyKoreaClient
from mypet_life_mcp.core.korean import safety_note_ko
from mypet_life_mcp.core.schemas import ValidationError, require_text
from mypet_life_mcp.tools.food_safety_helpers import (
    evidence_status,
    food_safety_fallback_notices,
    ingredient_candidates,
    normalize_species,
    positive_optional,
    source_rows,
    warnings,
)
from mypet_life_mcp.tools.food_safety_summary import summary
from mypet_life_mcp.tools.pet_food_references import match_pet_food_references


def check_pet_food_safety(
    food: str,
    pet_type: str,
    weight_kg: float | None = None,
    amount_gram: float | None = None,
    food_client: FoodSafetyKoreaClient | None = None,
) -> dict:
    try:
        food_text = require_text(food, "food")
        species = normalize_species(require_text(pet_type, "pet_type"))
        weight = positive_optional(weight_kg, "weight_kg")
        amount = positive_optional(amount_gram, "amount_gram")
    except ValidationError as exc:
        return {"status": "invalid_request", "summary_ko": str(exc), "safety_note_ko": safety_note_ko()}

    food_api = food_client or FoodSafetyKoreaClient()
    product_result = food_api.search_product(food_text)
    candidates = ingredient_candidates(food_text, product_result)
    ingredients = [_resolve_ingredient(item["name"], item["role"], species, food_api) for item in candidates[:8]]
    sources = source_rows(product_result, ingredients)
    source_warnings = warnings(sources)
    fallback_notices = food_safety_fallback_notices(product_result)
    status = "evidence_collected" if any(item["evidence"] for item in ingredients) else "source_limited"
    return {
        "tool": "check_pet_food_safety",
        "status": status,
        "food": food_text,
        "pet_type": species,
        "weight_kg": weight,
        "amount_gram": amount,
        "ingredient_resolution": {
            "status": "resolved" if product_result.ok and product_result.items else "fallback_to_input",
            "source": product_result.source,
        },
        "ingredients": ingredients,
        "sources": sources,
        "source_warnings_ko": source_warnings,
        "fallback_notices_ko": fallback_notices,
        "limitations_ko": [
            "식품안전나라 원재료와 공개 레퍼런스 기준의 후보 안내입니다.",
            "개별 동물의 체중, 기저질환, 섭취량, 섭취 후 경과 시간에 따라 위험도는 달라질 수 있습니다.",
            "조회 결과가 없다는 뜻은 안전하다는 보장이 아닙니다.",
        ],
        "summary_ko": summary(food_text, species, ingredients),
        "safety_note_ko": safety_note_ko(),
    }


def _resolve_ingredient(name: str, role: str, species: str, food_api: FoodSafetyKoreaClient) -> dict[str, Any]:
    normalized = _normalize_ingredient(name, food_api)
    values = [
        name,
        normalized.get("canonical_name"),
        normalized.get("english_name"),
        normalized.get("scientific_name"),
        *(normalized.get("aliases") or []),
    ]
    evidence = match_pet_food_references([str(value) for value in values if value], species)
    return {
        **normalized,
        "role": role,
        "identifiers": {},
        "evidence_status": evidence_status(evidence, species),
        "species_evidence_found": any(item.get("species") == species for item in evidence),
        "evidence": evidence,
        "_source": normalized["_source"],
    }


def _normalize_ingredient(name: str, food_api: FoodSafetyKoreaClient) -> dict[str, Any]:
    result = food_api.normalize_ingredient(name)
    item = result.items[0] if result.ok and result.items else {}
    canonical = item.get("RPRSNT_RAWMTRL_NM") or name
    aliases = [part.strip() for part in str(item.get("RAWMTRL_NCKNM") or "").split(",") if part.strip()]
    return {
        "input_name": name,
        "canonical_name": canonical,
        "english_name": item.get("ENG_NM"),
        "scientific_name": item.get("SCNM"),
        "aliases": aliases,
        "normalization_status": "resolved" if item else "unresolved",
        "_source": result,
    }
