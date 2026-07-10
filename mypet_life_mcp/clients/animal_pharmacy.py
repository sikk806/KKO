from __future__ import annotations

from mypet_life_mcp.core.schemas import SourceResult

from .base import BaseApiClient, contains_region, data_go_items


class AnimalPharmacyClient(BaseApiClient):
    service_name = "동물약국 인허가 공공데이터"
    SEARCH_URL = "http://apis.data.go.kr/1741000/animal_pharmacies/info"

    def search(self, region: str, radius_km: float = 5.0) -> SourceResult:
        try:
            key = self.get_key("DATA_GO_KR_SERVICE_KEY")
            items = []
            for page_no in range(1, 20):
                data = self.get_json(self.SEARCH_URL, {"serviceKey": key, "pageNo": page_no, "numOfRows": 1000, "type": "json"})
                page_items = data_go_items(data)
                items.extend(item for item in page_items if contains_region(item, region))
                if len(page_items) < 1000:
                    break
            return SourceResult(items=items, source=self.service_name)
        except Exception as exc:
            return self.source_error(exc)
