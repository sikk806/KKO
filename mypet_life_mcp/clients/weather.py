from __future__ import annotations

import math
from datetime import datetime, timedelta

from mypet_life_mcp.core.schemas import SourceResult

from .base import BaseApiClient


class WeatherClient(BaseApiClient):
    service_name = "기상청 단기예보"
    SEARCH_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"

    def forecast(self, latitude: float, longitude: float, when: datetime) -> SourceResult:
        try:
            key = self.get_key("KMA_SERVICE_KEY", "DATA_GO_KR_SERVICE_KEY")
            base_date, base_time = _forecast_base_time(when)
            nx, ny = _to_kma_grid(latitude, longitude)
            data = self.get_json(
                self.SEARCH_URL,
                {
                    "serviceKey": key,
                    "pageNo": 1,
                    "numOfRows": 1000,
                    "dataType": "JSON",
                    "base_date": base_date,
                    "base_time": base_time,
                    "nx": nx,
                    "ny": ny,
                },
            )
            return SourceResult(items=[_compact_vilage_forecast(data)], source=self.service_name)
        except Exception as exc:
            return self.source_error(exc)


def _forecast_base_time(moment: datetime) -> tuple[str, str]:
    issue_hours = [2, 5, 8, 11, 14, 17, 20, 23]
    local = moment
    if local.hour < 2:
        local = local - timedelta(days=1)
        return local.strftime("%Y%m%d"), "2300"
    base_hour = max(hour for hour in issue_hours if hour <= local.hour)
    return local.strftime("%Y%m%d"), f"{base_hour:02d}00"


def _to_kma_grid(latitude: float, longitude: float) -> tuple[int, int]:
    re = 6371.00877
    grid = 5.0
    slat1 = 30.0
    slat2 = 60.0
    olon = 126.0
    olat = 38.0
    xo = 43
    yo = 136

    degrad = math.pi / 180.0
    re_grid = re / grid
    slat1_rad = slat1 * degrad
    slat2_rad = slat2 * degrad
    olon_rad = olon * degrad
    olat_rad = olat * degrad

    sn = math.tan(math.pi * 0.25 + slat2_rad * 0.5) / math.tan(math.pi * 0.25 + slat1_rad * 0.5)
    sn = math.log(math.cos(slat1_rad) / math.cos(slat2_rad)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1_rad * 0.5)
    sf = (sf**sn) * math.cos(slat1_rad) / sn
    ro = math.tan(math.pi * 0.25 + olat_rad * 0.5)
    ro = re_grid * sf / (ro**sn)

    ra = math.tan(math.pi * 0.25 + latitude * degrad * 0.5)
    ra = re_grid * sf / (ra**sn)
    theta = longitude * degrad - olon_rad
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    x = math.floor(ra * math.sin(theta) + xo + 0.5)
    y = math.floor(ro - ra * math.cos(theta) + yo + 0.5)
    return x, y


def _compact_vilage_forecast(data: dict) -> dict:
    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    if isinstance(items, dict):
        items = [items]
    compact = {"rain_probability": 0, "precipitation_mm": 0}
    for item in items:
        category = item.get("category")
        value = item.get("fcstValue")
        if category == "POP":
            compact["rain_probability"] = _to_number(value, 0)
        elif category == "PCP":
            compact["precipitation_mm"] = _precipitation_to_mm(value)
        elif category == "TMP":
            compact["temperature_c"] = _to_number(value, None)
        elif category == "WSD":
            compact["wind_mps"] = _to_number(value, 0)
    return compact


def _to_number(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _precipitation_to_mm(value) -> float:
    if value in (None, "", "강수없음"):
        return 0.0
    text = str(value).replace("mm", "").strip()
    if text.startswith("1mm 미만"):
        return 0.5
    if "~" in text:
        text = text.split("~", 1)[-1]
    return float(text) if text.replace(".", "", 1).isdigit() else 0.0
