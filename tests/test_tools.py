from __future__ import annotations

import json
import unittest
from pathlib import Path

from mypet_life_mcp.core.korean import FORBIDDEN_USER_PHRASES
from mypet_life_mcp.core.schemas import GeoPoint, SourceResult, parse_when
from mypet_life_mcp.core.scoring import candidate_score, is_holiday_or_night, outing_score, rank_candidates
from mypet_life_mcp.tools import (
    find_pet_emergency_candidates,
    make_pet_care_map,
    make_pet_outing_plan,
    verify_pet_business,
)
from mypet_life_mcp.tools.common import candidates_from_source, normalize_region_name, region_centroid
from mypet_life_mcp.tools.outing import _content_type_for_outing

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


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.hospitals = load_fixture("hospital_candidates.json")
        self.pharmacies = load_fixture("pharmacy_candidates.json")
        self.places = load_fixture("pet_friendly_places.json")
        self.weather = load_fixture("weather.json")
        self.licenses = load_fixture("pet_business_license_matches.json")

    def assert_korean_safe(self, payload):
        text = json.dumps(payload, ensure_ascii=False)
        for phrase in FORBIDDEN_USER_PHRASES:
            self.assertNotIn(phrase.lower(), text.lower())
        self.assertIn("summary_ko", payload)

    def test_geocoding_failure_is_korean(self):
        result = make_pet_care_map("없는곳", hospital_client=FakeSourceClient(self.hospitals))
        self.assertEqual(result["location_precision"], "region_text_only")
        self.assertIn("좌표가 없어", result["source_warnings_ko"][0])

    def test_distance_sorting_and_keyword_ranking(self):
        origin = GeoPoint("강남", 37.5, 127.025)
        candidates = candidates_from_source(SourceResult(self.hospitals, "테스트"), "동물병원")
        for candidate in candidates:
            if candidate.latitude and candidate.longitude:
                from mypet_life_mcp.core.geo import haversine_km

                candidate.distance_km = haversine_km(origin.latitude, origin.longitude, candidate.latitude, candidate.longitude)
        ranked = rank_candidates(candidates, "hospital")
        self.assertEqual(ranked[0].name, "튼튼24동물의료센터")
        self.assertTrue(candidate_score(ranked[0], "hospital") > candidate_score(ranked[-1], "hospital"))

    def test_inactive_business_filtering(self):
        candidates = rank_candidates(candidates_from_source(SourceResult(self.hospitals, "테스트"), "동물병원"), "hospital")
        names = [candidate.name for candidate in candidates]
        self.assertNotIn("폐업동물병원", names)

    def test_emergency_tool_with_pharmacy_and_holiday_mode(self):
        result = find_pet_emergency_candidates(
            "강남",
            pet_type="강아지",
            situation="medicine needed",
            when="2026-07-05T22:00:00+09:00",
            hospital_client=FakeSourceClient(self.hospitals),
            pharmacy_client=FakeSourceClient(self.pharmacies),
            holiday_client=FakeHoliday(True),
        )
        self.assertTrue(result["is_holiday_or_night"])
        self.assertEqual(result["animal_hospitals"][0]["name"], "튼튼24동물의료센터")
        self.assertEqual(result["animal_pharmacies"][0]["name"], "강남동물약국")
        self.assertIn("전화 확인", result["summary_ko"])
        self.assert_korean_safe(result)

    def test_missing_api_key_behavior(self):
        result = make_pet_care_map("강남", hospital_client=FakeSourceClient(self.hospitals))
        self.assertEqual(result["location_precision"], "coordinate")
        self.assertTrue(result["animal_hospitals"])

        emergency = find_pet_emergency_candidates(
            "서울시",
            when="지금",
            hospital_client=FakeSourceClient(self.hospitals),
            pharmacy_client=FakeSourceClient(self.pharmacies),
            holiday_client=FakeHoliday(False),
        )
        self.assertEqual(emergency["location_precision"], "coordinate")

    def test_partial_api_failure_behavior(self):
        result = make_pet_care_map(
            "강남",
            hospital_client=FakeSourceClient(self.hospitals),
            pharmacy_client=FakeSourceClient([], ok=False, error_ko="동물약국 조회에 실패했습니다."),
        )
        self.assertTrue(result["animal_hospitals"])
        self.assertIn("동물약국 조회에 실패했습니다.", result["source_warnings_ko"])

    def test_provided_coordinates_enable_distance(self):
        result = make_pet_care_map(
            "현재 위치",
            latitude=37.5,
            longitude=127.025,
            hospital_client=FakeSourceClient(self.hospitals),
            pharmacy_client=FakeSourceClient(self.pharmacies),
        )
        self.assertEqual(result["location_precision"], "provided_coordinate")
        self.assertIsNotNone(result["animal_hospitals"][0]["distance_km"])

    def test_holiday_night_mode_detection(self):
        from datetime import datetime

        self.assertTrue(is_holiday_or_night(datetime.fromisoformat("2026-07-04T10:00:00+09:00")))
        self.assertTrue(is_holiday_or_night(datetime.fromisoformat("2026-07-06T21:00:00+09:00")))

    def test_parse_when_accepts_natural_now(self):
        self.assertIsNotNone(parse_when("지금").tzinfo)
        self.assertIsNotNone(parse_when("현재").tzinfo)
        self.assertEqual(parse_when("오늘 밤").hour, 21)

    def test_normalize_common_region_aliases(self):
        self.assertEqual(normalize_region_name("서울"), "서울특별시")
        self.assertEqual(normalize_region_name("서울시"), "서울특별시")
        self.assertEqual(normalize_region_name("서울특별시"), "서울특별시")
        self.assertEqual(normalize_region_name("서울 양천"), "서울특별시 양천구")
        self.assertEqual(normalize_region_name("서울시 양천구"), "서울특별시 양천구")
        self.assertEqual(normalize_region_name("서울 양천구 신정동 920-31"), "서울특별시 양천구")
        self.assertEqual(normalize_region_name("서울특별시 영등포구 국회대로74길"), "서울특별시 영등포구")
        self.assertEqual(normalize_region_name("양천"), "서울특별시 양천구")
        self.assertEqual(normalize_region_name("해운대"), "부산광역시 해운대구")
        self.assertEqual(normalize_region_name("부산 해운대"), "부산광역시 해운대구")
        self.assertEqual(normalize_region_name("강원 원주"), "강원특별자치도 원주시")
        self.assertEqual(normalize_region_name("충남 천안"), "충청남도 천안시")
        self.assertEqual(normalize_region_name("전북 전주"), "전북특별자치도 전주시")
        self.assertEqual(normalize_region_name("경북 포항"), "경상북도 포항시")
        self.assertEqual(normalize_region_name("경남 창원"), "경상남도 창원시")
        self.assertEqual(normalize_region_name("중구"), "중구")

    def test_region_centroid_and_outing_type_mapping(self):
        self.assertIsNotNone(region_centroid("서울 양천"))
        self.assertIsNotNone(region_centroid("부산 해운대"))
        self.assertEqual(_content_type_for_outing("점심 식사"), "39")
        self.assertEqual(_content_type_for_outing("펜션 숙소"), "32")
        self.assertEqual(_content_type_for_outing("산책 놀이"), "12")

    def test_outing_score_calculation(self):
        score, cautions = outing_score(self.weather, self.places, candidates_from_source(SourceResult(self.hospitals, "테스트"), "동물병원"))
        self.assertLess(score, 100)
        self.assertTrue(any("비 예보" in caution for caution in cautions))

    def test_outing_tool(self):
        result = make_pet_outing_plan(
            "강남",
            place_client=FakeSourceClient(self.places),
            weather_client=FakeWeather(self.weather),
            hospital_client=FakeSourceClient(self.hospitals),
            pharmacy_client=FakeSourceClient(self.pharmacies),
        )
        self.assertIn("외출 적합도", result["summary_ko"])
        self.assertGreaterEqual(result["outing_score"], 0)
        self.assert_korean_safe(result)

    def test_business_verification_statuses(self):
        verified = verify_pet_business("해피펫호텔", "강남", "hotel", license_client=FakeSourceClient(self.licenses))
        self.assertEqual(verified["status"], "verified")
        possible = verify_pet_business("해피펫", "강남", "hotel", license_client=FakeSourceClient(self.licenses))
        self.assertIn(possible["status"], {"possible_match", "verified"})
        not_found = verify_pet_business("없는업체", "강남", "hotel", license_client=FakeSourceClient([]))
        self.assertEqual(not_found["status"], "not_found")
        ambiguous_items = self.licenses + [{**self.licenses[0], "소재지전체주소": "서울특별시 강남구 다른로 8"}]
        ambiguous = verify_pet_business("해피펫호텔", "강남", "hotel", license_client=FakeSourceClient(ambiguous_items))
        self.assertEqual(ambiguous["status"], "ambiguous")
        self.assert_korean_safe(verified)


if __name__ == "__main__":
    unittest.main()
