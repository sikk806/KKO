from __future__ import annotations

from mypet_life_mcp.core.schemas import SourceResult

from .base import BaseApiClient


class PetFriendlyPlaceClient(BaseApiClient):
    service_name = "한국관광공사 반려동물 동반 여행 정보"
    SEARCH_URL = "https://apis.data.go.kr/B551011/KorPetTourService2/locationBasedList2"

    def search(self, latitude: float, longitude: float, radius_km: float = 5.0, content_type: str | None = None) -> SourceResult:
        try:
            key = self.get_key("KTO_SERVICE_KEY", "DATA_GO_KR_SERVICE_KEY")
            params = {
                "serviceKey": key,
                "MobileOS": "ETC",
                "MobileApp": "MyPetLife",
                "mapX": longitude,
                "mapY": latitude,
                "radius": int(radius_km * 1000),
                "_type": "json",
            }
            if content_type:
                params["contentTypeId"] = content_type
            data = self.get_json(self.SEARCH_URL, params)
            items = _items(data)
            if not items and content_type:
                params.pop("contentTypeId", None)
                data = self.get_json(self.SEARCH_URL, params)
                items = _items(data)
            return SourceResult(items=items, source=self.service_name)
        except Exception as exc:
            return self.source_error(exc)

    def search_keyword(self, keyword: str, content_type: str | None = None, rows: int = 10) -> SourceResult:
        try:
            key = self.get_key("KTO_SERVICE_KEY", "DATA_GO_KR_SERVICE_KEY")
            params = {
                "serviceKey": key,
                "MobileOS": "ETC",
                "MobileApp": "MyPetLife",
                "keyword": keyword,
                "numOfRows": rows,
                "pageNo": 1,
                "_type": "json",
            }
            if content_type:
                params["contentTypeId"] = content_type
            data = self.get_json("https://apis.data.go.kr/B551011/KorPetTourService2/searchKeyword2", params)
            return SourceResult(items=_items(data), source=self.service_name)
        except Exception as exc:
            return self.source_error(exc)


def _items(data: dict) -> list[dict]:
    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    if isinstance(items, dict):
        items = [items]
    return items if isinstance(items, list) else []
