from __future__ import annotations

from datetime import date

from mypet_life_mcp.core.schemas import SourceResult

from .base import BaseApiClient


class HolidayClient(BaseApiClient):
    service_name = "공휴일 정보 공공데이터"
    SEARCH_URL = "https://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo"

    def is_holiday(self, day: date) -> bool:
        result = self.check(day)
        if not result.ok or not result.items:
            return False
        return bool(result.items[0].get("is_holiday"))

    def check(self, day: date) -> SourceResult:
        try:
            key = self.get_key("KASI_SERVICE_KEY", "DATA_GO_KR_SERVICE_KEY")
            data = self.get_json(
                self.SEARCH_URL,
                {"serviceKey": key, "solYear": day.year, "solMonth": f"{day.month:02d}", "_type": "json"},
            )
            body = data.get("response", {}).get("body", {})
            items = body.get("items", {}).get("item", [])
            if isinstance(items, dict):
                items = [items]
            target = day.strftime("%Y%m%d")
            return SourceResult(
                items=[{"date": day.isoformat(), "is_holiday": any(str(item.get("locdate")) == target for item in items)}],
                source=self.service_name,
            )
        except Exception as exc:
            return self.source_error(exc)
