from __future__ import annotations

import re
from typing import Any

from mypet_life_mcp.tools.food_safety_helpers import dedupe


def summary(
    food: str,
    species: str,
    ingredients: list[dict[str, Any]],
) -> str:
    species_label = "강아지" if species == "dog" else "고양이"
    display_food = _display_food_name(food, species)
    food_topic = _topic(display_food)
    matched = _summary_matches(ingredients, species)
    species_matched = [item for item in matched if item.get("species_evidence_found")]

    if species_matched:
        effects = _effect_summary(species_matched)
        recommendation = _strongest_recommendation(species_matched)
        if recommendation == "great":
            return (
                f"{food_topic} {species_label}에게 좋은 간식으로 볼 수 있는 음식입니다. "
                f"양념 없이 작게 잘라 조금만 주세요. "
                f"좋은 음식이어도 너무 많이 먹으면 {effects} 같은 증상이 생길 수 있으니 간식 정도로만 주는 게 좋습니다."
            )
        if recommendation == "ok":
            return (
                f"{food_topic} {species_label}에게 소량이면 괜찮은 음식입니다. "
                f"다만 양념, 씨, 껍질, 뼈, 가시, 기름기는 피하고 조금만 주세요. "
                f"많이 먹었거나 {effects} 같은 증상이 있으면 동물병원에 문의해 주세요."
            )
        if recommendation == "limited":
            return (
                f"{food_topic} {species_label}에게 소량만 조심해서 봐야 하는 음식입니다. "
                f"소량을 먹었고 이상 증상이 없다면 상태를 지켜봐 주세요. "
                f"많이 먹었거나 {effects} 같은 증상이 있으면 동물병원에 문의해 주세요."
            )
        return (
            f"{food_topic} {species_label}에게 먹이면 안 되거나 위험할 수 있는 음식입니다. "
            f"이미 먹었다면 먹은 양, 먹은 시간, 체중을 확인하고 동물병원에 문의해 주세요. "
            f"나타날 수 있는 증상은 {effects} 등입니다."
        )

    if matched:
        effects = _effect_summary(matched)
        return (
            f"{food_topic} 반려동물에게 주의가 필요한 음식으로 알려진 근거가 있습니다. "
            f"다만 {species_label}에게 그대로 적용되는지는 추가 확인이 필요해요. "
            f"이미 먹었다면 상태를 관찰하고, {effects} 같은 증상이 있으면 동물병원에 문의해 주세요."
        )

    return (
        f"{food_topic} 현재 보유한 음식 데이터에는 없는 항목입니다. "
        f"정확한 급여 가능 여부는 인터넷으로 추가 확인하거나 동물병원에 문의해 주세요. "
        f"이미 먹었다면 구토, 설사, 무기력, 떨림, 호흡 이상처럼 평소와 다른 모습이 있는지 지켜봐 주세요."
    )


def _summary_matches(ingredients: list[dict[str, Any]], species: str) -> list[dict[str, Any]]:
    primary = [item for item in ingredients if item.get("role") == "primary"]
    primary_matches = [item for item in primary if item.get("evidence")]
    ingredient_matches = [item for item in ingredients if item.get("role") != "primary" and item.get("evidence")]
    ingredient_danger = [
        item
        for item in ingredient_matches
        if any(evidence.get("species") == species and evidence.get("severity") == "danger" for evidence in item["evidence"])
    ]
    if _has_species_severity(primary_matches, species, "danger"):
        return primary_matches
    if ingredient_danger:
        return ingredient_danger
    if primary_matches:
        return primary_matches
    return []


def _has_species_severity(items: list[dict[str, Any]], species: str, severity: str) -> bool:
    return any(
        evidence.get("species") == species and evidence.get("severity") == severity
        for item in items
        for evidence in item.get("evidence") or []
    )


def _topic(text: str) -> str:
    value = text.strip()
    if not value:
        return text
    code = ord(value[-1])
    if 0xAC00 <= code <= 0xD7A3 and (code - 0xAC00) % 28:
        return f"{value}은"
    return f"{value}는"


def _display_food_name(food: str, species: str) -> str:
    value = food.strip()
    value = _strip_pet_subject(value, species)
    value = _strip_question_phrases(value)
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) > 2:
        value = re.sub(r"(을|를|은|는|이|가|에게|한테)$", "", value).strip()
    return value or food.strip()


def _strip_pet_subject(value: str, species: str) -> str:
    common = ["반려동물", "반려견", "반려묘"]
    species_words = ["강아지", "개"] if species == "dog" else ["고양이"]
    for word in common + species_words:
        value = re.sub(rf"^{word}(에게|한테|는|은|이|가)?\s*", "", value)
    return value


def _strip_question_phrases(value: str) -> str:
    phrases = [
        "줘도 돼?",
        "줘도 돼",
        "줘도 됨?",
        "줘도 됨",
        "먹어도 되나?",
        "먹어도 되나",
        "먹어도 돼?",
        "먹어도 돼",
        "먹었는데 괜찮아?",
        "먹었는데 괜찮아",
        "먹었어",
        "먹은 것 같아",
        "마셔도 돼?",
        "마셔도 돼",
        "마셨는데 괜찮아?",
        "마셨는데 괜찮아",
        "마셨어",
        "괜찮아?",
        "괜찮아",
    ]
    for phrase in phrases:
        value = value.replace(phrase, " ")
    return value


def _effect_summary(ingredients: list[dict[str, Any]]) -> str:
    effects: list[str] = []
    for ingredient in ingredients:
        for evidence in ingredient.get("evidence") or []:
            effects.extend(evidence.get("signs_ko") or [])
    if effects:
        return ", ".join(dedupe(effects)[:8])
    names = [item.get("canonical_name") or item.get("input_name") for item in ingredients[:3]]
    names = [name for name in names if name]
    return f"{', '.join(names)} 관련 이상 증상"


def _strongest_recommendation(ingredients: list[dict[str, Any]]) -> str:
    recommendations = [
        evidence.get("recommendation") or _recommendation_from_severity(evidence.get("severity"))
        for ingredient in ingredients
        for evidence in ingredient.get("evidence") or []
    ]
    for value in ("avoid", "limited", "ok", "great"):
        if value in recommendations:
            return value
    return "ok"


def _recommendation_from_severity(severity: str | None) -> str:
    if severity == "danger":
        return "avoid"
    if severity == "caution":
        return "limited"
    return "ok"
