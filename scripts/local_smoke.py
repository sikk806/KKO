from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mypet_life_mcp.tools import (
    find_pet_emergency_candidates,
    make_pet_care_map,
    make_pet_outing_plan,
    verify_pet_business,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local live smoke tests for MyPet Life MCP.")
    parser.add_argument("--location", default="강남구", help="Region or human-readable location label.")
    parser.add_argument("--lat", type=float, default=37.4979, help="Latitude for coordinate-based tests.")
    parser.add_argument("--lon", type=float, default=127.0276, help="Longitude for coordinate-based tests.")
    parser.add_argument("--radius-km", type=float, default=5.0, help="Search radius in kilometers.")
    parser.add_argument("--business-name", default="펫츠힐 유치원 호텔", help="Pet business name to verify.")
    parser.add_argument("--business-type", default="hotel", help="Business type for license verification.")
    args = parser.parse_args()

    cases: list[tuple[str, Any]] = [
        (
            "find_pet_emergency_candidates",
            find_pet_emergency_candidates(
                location=args.location,
                pet_type="강아지",
                situation="구토",
                radius_km=args.radius_km,
                when=datetime.now().astimezone().isoformat(),
                latitude=args.lat,
                longitude=args.lon,
            ),
        ),
        (
            "make_pet_care_map",
            make_pet_care_map(
                location=args.location,
                radius_km=args.radius_km,
                include_pharmacies=True,
                latitude=args.lat,
                longitude=args.lon,
            ),
        ),
        (
            "make_pet_outing_plan",
            make_pet_outing_plan(
                location=args.location,
                pet_type="dog",
                outing_type="walk",
                radius_km=args.radius_km,
                when=datetime.now().astimezone().isoformat(),
                latitude=args.lat,
                longitude=args.lon,
            ),
        ),
        (
            "verify_pet_business",
            verify_pet_business(
                business_name=args.business_name,
                region=None,
                business_type=args.business_type,
            ),
        ),
    ]

    for name, payload in cases:
        print(f"\n=== {name} ===")
        print(json.dumps(_summarize(payload), ensure_ascii=False, indent=2))


def _summarize(payload: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "status": payload.get("status", "ok"),
        "mode": payload.get("mode"),
        "summary_ko": payload.get("summary_ko"),
        "location_precision": payload.get("location_precision"),
        "source_warnings_ko": payload.get("source_warnings_ko", []),
    }

    count_fields = {
        "animal_hospitals": payload.get("animal_hospitals"),
        "animal_pharmacies": payload.get("animal_pharmacies"),
        "pet_friendly_places": payload.get("pet_friendly_places"),
        "matches": payload.get("matches"),
        "candidates": payload.get("candidates"),
    }
    for key, value in count_fields.items():
        if isinstance(value, list):
            summary[f"{key}_count"] = len(value)

    if "outing_score" in payload:
        summary["outing_score"] = payload.get("outing_score")
        summary["score_label_ko"] = payload.get("score_label_ko")
    if "weather" in payload:
        summary["weather"] = payload.get("weather")
    if "is_holiday_or_night" in payload:
        summary["is_holiday_or_night"] = payload.get("is_holiday_or_night")
    if "verification_status" in payload:
        summary["verification_status"] = payload.get("verification_status")

    return {key: value for key, value in summary.items() if value not in (None, [], {})}


if __name__ == "__main__":
    main()
