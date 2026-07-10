from __future__ import annotations

import os

from mypet_life_mcp.tools import (
    find_pet_emergency_candidates,
    make_pet_care_map,
    make_pet_outing_plan,
    verify_pet_business,
)


def create_app():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("MCP 서버 실행에는 mcp 패키지가 필요합니다. `pip install -e .` 후 다시 실행해 주세요.") from exc

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    mcp = FastMCP("MyPet Life MCP", host=host, port=port, streamable_http_path="/mcp")

    @mcp.tool(name="find_pet_emergency_candidates", description="휴일/야간/주말 반려동물 응급 연락 후보를 한국어로 정리합니다.")
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

    @mcp.tool(name="make_pet_care_map", description="외출/여행 위치 주변 동물병원과 동물약국 후보 지도를 한국어로 만듭니다.")
    def make_pet_care_map_tool(
        location: str,
        radius_km: float = 5.0,
        include_pharmacies: bool = True,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> dict:
        return make_pet_care_map(location, radius_km, include_pharmacies, latitude, longitude)

    @mcp.tool(name="make_pet_outing_plan", description="반려동물 동반 장소, 날씨, 돌봄 연락처를 묶어 외출 계획을 한국어로 제안합니다.")
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

    @mcp.tool(name="verify_pet_business", description="반려동물 관련 업체의 공식 인허가 후보를 한국어로 확인합니다.")
    def verify_pet_business_tool(
        business_name: str,
        region: str | None = None,
        business_type: str = "unknown",
    ) -> dict:
        return verify_pet_business(business_name, region, business_type)

    return mcp


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport not in {"stdio", "sse", "streamable-http"}:
        raise ValueError("MCP_TRANSPORT must be one of: stdio, sse, streamable-http")
    create_app().run(transport=transport)


if __name__ == "__main__":
    main()
