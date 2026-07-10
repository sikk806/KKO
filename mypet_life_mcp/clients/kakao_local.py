from __future__ import annotations

from typing import Any

from mypet_life_mcp.core.schemas import GeoPoint

from .base import BaseApiClient, first_value


class KakaoLocalClient(BaseApiClient):
    service_name = "카카오 로컬 API"
    required_env = "KAKAO_REST_API_KEY"
    ADDRESS_URL = "https://dapi.kakao.com/v2/local/search/address.json"
    KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

    def geocode(self, location: str) -> GeoPoint:
        key = self.get_key("KAKAO_REST_API_KEY")
        data = self.get_json(
            self.ADDRESS_URL,
            {"query": location, "size": 1},
            {"Authorization": f"KakaoAK {key}"},
        )
        documents = data.get("documents", [])
        if not documents:
            raise RuntimeError("입력한 위치를 찾지 못했습니다. 시/군/구 또는 도로명 주소를 조금 더 구체적으로 입력해 주세요.")
        first = documents[0]
        return self._document_to_point(location, first)

    def keyword_search(self, query: str, latitude: float, longitude: float, radius_m: int = 5000) -> list[dict[str, Any]]:
        key = self.get_key("KAKAO_REST_API_KEY")
        data = self.get_json(
            self.KEYWORD_URL,
            {"query": query, "x": longitude, "y": latitude, "radius": radius_m, "size": 15},
            {"Authorization": f"KakaoAK {key}"},
        )
        return data.get("documents", [])

    @staticmethod
    def _document_to_point(label: str, document: dict[str, Any]) -> GeoPoint:
        address = first_value(document, "road_address_name", "address_name")
        return GeoPoint(
            label=label,
            latitude=float(document["y"]),
            longitude=float(document["x"]),
            address=address,
        )
