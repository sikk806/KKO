from __future__ import annotations

import os

from mypet_life_mcp.tools import (
    check_pet_food_safety,
    find_pet_emergency_candidates,
    make_pet_care_map,
    make_pet_outing_plan,
    verify_pet_business,
)


def create_app():
    try:
        from mcp.server.fastmcp import FastMCP
        from mcp.types import ToolAnnotations
    except ImportError as exc:
        raise RuntimeError("MCP 서버 실행에는 mcp 패키지가 필요합니다. `pip install -e .` 후 다시 실행해 주세요.") from exc

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    mcp = FastMCP("MyPet Life MCP", host=host, port=port, streamable_http_path="/mcp")

    def read_only_tool(title: str) -> ToolAnnotations:
        return ToolAnnotations(
            title=title,
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        )

    @mcp.tool(
        name="find_pet_emergency_candidates",
        description=(
            "MyPet Life(마이펫 라이프) finds candidate pet emergency contacts for nights, weekends, "
            "and holidays in Korea. It returns cautious Korean guidance and asks users "
            "to confirm availability by phone."
        ),
        annotations=read_only_tool("Find pet emergency contact candidates"),
    )
    def find_pet_emergency_candidates_tool(
        location: str,
        pet_type: str | None = None,
        situation: str | None = None,
        radius_km: float = 5.0,
        when: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> dict:
        return find_pet_emergency_candidates(location, pet_type, situation, radius_km, when, latitude, longitude)

    @mcp.tool(
        name="make_pet_care_map",
        description=(
            "MyPet Life(마이펫 라이프) builds a pet-care candidate map around an outing or travel "
            "location in Korea, including animal hospitals and optional animal pharmacies."
        ),
        annotations=read_only_tool("Make a pet care candidate map"),
    )
    def make_pet_care_map_tool(
        location: str,
        radius_km: float = 5.0,
        include_pharmacies: bool = True,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> dict:
        return make_pet_care_map(location, radius_km, include_pharmacies, latitude, longitude)

    @mcp.tool(
        name="make_pet_outing_plan",
        description=(
            "MyPet Life(마이펫 라이프) suggests a Korean pet outing plan by combining pet-friendly "
            "place candidates, weather context, and nearby care contacts."
        ),
        annotations=read_only_tool("Make a pet outing plan"),
    )
    def make_pet_outing_plan_tool(
        location: str,
        pet_type: str = "dog",
        outing_type: str | None = None,
        radius_km: float = 5.0,
        when: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> dict:
        return make_pet_outing_plan(location, pet_type, outing_type, radius_km, when, latitude, longitude)

    @mcp.tool(
        name="verify_pet_business",
        description=(
            "MyPet Life(마이펫 라이프) verifies pet-related business license candidates against "
            "official public-data records and returns cautious Korean guidance."
        ),
        annotations=read_only_tool("Verify pet business license candidates"),
    )
    def verify_pet_business_tool(
        business_name: str,
        region: str | None = None,
        business_type: str = "unknown",
    ) -> dict:
        return verify_pet_business(business_name, region, business_type)

    @mcp.tool(
        name="check_pet_food_safety",
        description=(
            "MyPet Life(마이펫 라이프) checks whether a dog or cat may need caution after eating a "
            "food, product, or ingredient by combining local pet-food references with "
            "food ingredient lookup when available."
        ),
        annotations=read_only_tool("Check pet food safety"),
    )
    def check_pet_food_safety_tool(
        food: str,
        pet_type: str,
        weight_kg: float | None = None,
        amount_gram: float | None = None,
    ) -> dict:
        return check_pet_food_safety(food, pet_type, weight_kg, amount_gram)

    return mcp


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport not in {"stdio", "sse", "streamable-http"}:
        raise ValueError("MCP_TRANSPORT must be one of: stdio, sse, streamable-http")
    create_app().run(transport=transport)


if __name__ == "__main__":
    main()
