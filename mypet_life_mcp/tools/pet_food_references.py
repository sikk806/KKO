from __future__ import annotations

from typing import Any

from mypet_life_mcp.tools.data_files import load_data_json
from mypet_life_mcp.tools.food_safety_helpers import compact


PET_FOOD_REFERENCES: list[dict[str, Any]] = load_data_json("pet_food_references.json")


def match_pet_food_references(values: list[str], species: str) -> list[dict[str, Any]]:
    haystacks = [compact(value) for value in values if value]
    matches: list[dict[str, Any]] = []
    seen: set[str] = set()
    for reference in PET_FOOD_REFERENCES:
        if reference["id"] in seen or not _matches_any_alias(reference["aliases"], haystacks):
            continue
        seen.add(reference["id"])
        match_species = species if species in reference["species"] else None
        matches.append(_evidence(reference, match_species))
    return matches


def _evidence(reference: dict[str, Any], match_species: str | None) -> dict[str, Any]:
    return {
        "source": reference["source_name"],
        "source_url": reference["source_url"],
        "reference_id": reference["id"],
        "title": reference["label_ko"],
        "summary": reference["concern_ko"],
        "severity": reference["severity"],
        "species": match_species,
        "matched_species": reference["species"],
        "signs_ko": reference["signs_ko"],
        "recommendation": reference["recommendation"],
    }


def _matches_any_alias(aliases: list[str], haystacks: list[str]) -> bool:
    return any(_matches_alias(compact(alias), haystack) for alias in aliases for haystack in haystacks)


def _matches_alias(needle: str, haystack: str) -> bool:
    if len(needle) <= 1:
        if needle in {"귤", "배", "떡"}:
            return needle in haystack
        return needle == haystack
    return needle in haystack
