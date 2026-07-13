from __future__ import annotations

from typing import Any
from urllib.parse import quote

from mypet_life_mcp.clients.base import BaseApiClient
from mypet_life_mcp.core.schemas import SourceResult


class FoodSafetyKoreaClient(BaseApiClient):
    service_name = "Food Safety Korea OpenAPI"
    required_env = "FOOD_SAFETY_KOREA_API_KEY"
    base_url = "https://openapi.foodsafetykorea.go.kr/api"

    def search_product(self, food: str, rows: int = 10) -> SourceResult:
        return self._fetch("C002", rows, {"PRDLST_NM": food})

    def search_product_by_ingredient(self, ingredient: str, rows: int = 10) -> SourceResult:
        return self._fetch("C002", rows, {"RAWMTRL_NM": ingredient})

    def normalize_ingredient(self, ingredient: str, rows: int = 5) -> SourceResult:
        return self._fetch("I2520", rows, {"RPRSNT_RAWMTRL_NM": ingredient})

    def _fetch(self, service_id: str, rows: int, filters: dict[str, str]) -> SourceResult:
        try:
            key = self.get_key("FOOD_SAFETY_KOREA_API_KEY")
            url = self._url(key, service_id, rows, filters)
            payload = self.get_json(url, {})
            return SourceResult(items=_rows(payload, service_id), source=f"Food Safety Korea {service_id}")
        except Exception as exc:
            return self.source_error(exc)

    def _url(self, key: str, service_id: str, rows: int, filters: dict[str, str]) -> str:
        encoded_filters = [
            f"{quote(name, safe='')}={quote(value, safe='')}"
            for name, value in filters.items()
            if value
        ]
        suffix = "/" + "&".join(encoded_filters) if encoded_filters else ""
        return f"{self.base_url}/{quote(key, safe='')}/{service_id}/json/1/{rows}{suffix}"


def _rows(payload: dict[str, Any], service_id: str) -> list[dict[str, Any]]:
    service = payload.get(service_id, {})
    rows = service.get("row", [])
    if isinstance(rows, dict):
        return [rows]
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    return []
