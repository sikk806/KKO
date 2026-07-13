from __future__ import annotations

import json
from pathlib import Path

from mypet_life_mcp.core.schemas import SourceResult


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    with (FIXTURE_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


class FakeSourceClient:
    def __init__(self, items, ok=True, error_ko=None):
        self.items = items
        self.ok = ok
        self.error_ko = error_ko

    def search(self, *args, **kwargs):
        return SourceResult(items=self.items, source="테스트 공공데이터", ok=self.ok, error_ko=self.error_ko)


class FakeHoliday:
    def __init__(self, value):
        self.value = value

    def is_holiday(self, day):
        return self.value

    def check(self, day):
        return SourceResult(items=[{"date": day.isoformat(), "is_holiday": self.value}], source="테스트 휴일")


class FakeWeather:
    def __init__(self, item):
        self.item = item

    def forecast(self, *args, **kwargs):
        return SourceResult(items=[self.item], source="테스트 날씨")
