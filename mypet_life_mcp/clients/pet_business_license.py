from __future__ import annotations

from mypet_life_mcp.core.schemas import SourceResult

from .base import BaseApiClient, contains_region, data_go_items

LICENSE_TYPE_KO = {
    "hotel": "동물위탁관리업",
    "daycare": "동물위탁관리업",
    "boarding": "동물위탁관리업",
    "grooming": "동물미용업",
    "transport": "동물운송업",
    "funeral": "동물장묘업",
    "unknown": "반려동물 관련 영업",
}


class PetBusinessLicenseClient(BaseApiClient):
    service_name = "반려동물 영업 인허가 공공데이터"
    SEARCH_URLS = {
        "hotel": "http://apis.data.go.kr/1741000/animal_boarding/info",
        "daycare": "http://apis.data.go.kr/1741000/animal_boarding/info",
        "boarding": "http://apis.data.go.kr/1741000/animal_boarding/info",
        "grooming": "http://apis.data.go.kr/1741000/pet_grooming/info",
        "transport": "http://apis.data.go.kr/1741000/animal_transport/info",
        "funeral": "http://apis.data.go.kr/1741000/animal_cremation/info",
        "unknown": "http://apis.data.go.kr/1741000/animal_boarding/info",
    }

    def search(self, business_name: str, region: str | None = None, business_type: str | None = None) -> SourceResult:
        try:
            key = self.get_key("DATA_GO_KR_SERVICE_KEY")
            url = self.SEARCH_URLS.get(business_type or "unknown", self.SEARCH_URLS["unknown"])
            items = []
            for page_no in range(1, 20):
                data = self.get_json(url, {"serviceKey": key, "pageNo": page_no, "numOfRows": 1000, "type": "json"})
                page_items = data_go_items(data)
                for item in page_items:
                    if contains_region(item, region) and contains_region(item, business_name):
                        items.append(item)
                if len(page_items) < 1000:
                    break
            expected_type = LICENSE_TYPE_KO.get(business_type or "unknown")
            for item in items:
                item.setdefault("license_type", expected_type)
            return SourceResult(items=items, source=self.service_name)
        except Exception as exc:
            return self.source_error(exc)
