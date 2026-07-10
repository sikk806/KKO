from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TOOLS = {
    "find_pet_emergency_candidates",
    "make_pet_care_map",
    "make_pet_outing_plan",
    "verify_pet_business",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MCP protocol smoke tests for MyPet Life MCP.")
    parser.add_argument("--location", default="강남구", help="Region or human-readable location label.")
    parser.add_argument("--lat", type=float, default=37.4979, help="Latitude for coordinate-based tests.")
    parser.add_argument("--lon", type=float, default=127.0276, help="Longitude for coordinate-based tests.")
    parser.add_argument("--radius-km", type=float, default=5.0, help="Search radius in kilometers.")
    parser.add_argument("--business-name", default="펫츠힐 유치원 호텔", help="Pet business name to verify.")
    parser.add_argument("--business-type", default="hotel", help="Business type for license verification.")
    args = parser.parse_args()
    asyncio.run(run(args))


async def run(args: argparse.Namespace) -> None:
    env = os.environ.copy()
    pythonpath = str(PROJECT_ROOT)
    env["PYTHONPATH"] = pythonpath + os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else pythonpath

    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mypet_life_mcp.server"],
        cwd=PROJECT_ROOT,
        env=env,
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_response = await session.list_tools()
            tool_names = [tool.name for tool in tools_response.tools]
            missing = sorted(EXPECTED_TOOLS.difference(tool_names))
            print("=== tools/list ===")
            print(json.dumps({"tools": tool_names, "missing": missing}, ensure_ascii=False, indent=2))
            if missing:
                raise SystemExit(f"Missing MCP tools: {', '.join(missing)}")

            calls = [
                (
                    "find_pet_emergency_candidates",
                    {
                        "location": args.location,
                        "pet_type": "강아지",
                        "situation": "구토",
                        "radius_km": args.radius_km,
                        "when": datetime.now().astimezone().isoformat(),
                        "latitude": args.lat,
                        "longitude": args.lon,
                    },
                ),
                (
                    "make_pet_care_map",
                    {
                        "location": args.location,
                        "radius_km": args.radius_km,
                        "include_pharmacies": True,
                        "latitude": args.lat,
                        "longitude": args.lon,
                    },
                ),
                (
                    "make_pet_outing_plan",
                    {
                        "location": args.location,
                        "pet_type": "dog",
                        "outing_type": "walk",
                        "radius_km": args.radius_km,
                        "when": datetime.now().astimezone().isoformat(),
                        "latitude": args.lat,
                        "longitude": args.lon,
                    },
                ),
                (
                    "verify_pet_business",
                    {
                        "business_name": args.business_name,
                        "region": None,
                        "business_type": args.business_type,
                    },
                ),
            ]

            for name, arguments in calls:
                result = await session.call_tool(name, arguments)
                print(f"\n=== tools/call: {name} ===")
                print(json.dumps(_summarize_call_result(result), ensure_ascii=False, indent=2))


def _summarize_call_result(result: Any) -> dict[str, Any]:
    payload = _extract_payload(result)
    summary: dict[str, Any] = {
        "is_error": getattr(result, "isError", False),
        "status": payload.get("status", "ok") if isinstance(payload, dict) else None,
        "mode": payload.get("mode") if isinstance(payload, dict) else None,
        "summary_ko": payload.get("summary_ko") if isinstance(payload, dict) else None,
        "location_precision": payload.get("location_precision") if isinstance(payload, dict) else None,
    }
    if isinstance(payload, dict):
        for key in ("animal_hospitals", "animal_pharmacies", "pet_friendly_places", "matches", "candidates"):
            value = payload.get(key)
            if isinstance(value, list):
                summary[f"{key}_count"] = len(value)
        if "outing_score" in payload:
            summary["outing_score"] = payload["outing_score"]
        if "weather" in payload:
            summary["weather"] = payload["weather"]
    return {key: value for key, value in summary.items() if value not in (None, [], {})}


def _extract_payload(result: Any) -> Any:
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return structured
    content = getattr(result, "content", [])
    if content and hasattr(content[0], "text"):
        try:
            return json.loads(content[0].text)
        except json.JSONDecodeError:
            return {"text": content[0].text}
    return {}


if __name__ == "__main__":
    main()
