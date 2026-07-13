from __future__ import annotations

import json
import unittest

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
from mypet_life_mcp.tools.outing import _content_type_for_outing, _outing_intent
from tests.helpers import FakeHoliday, FakeSourceClient, FakeWeather, load_fixture


class CountingPlaceClient(FakeSourceClient):
    service_name = "test place"

    def __init__(self, items):
        super().__init__(items)
        self.keyword_calls = 0

    def search_keyword(self, *args, **kwargs):
        self.keyword_calls += 1
        return SourceResult(items=[], source=self.service_name)


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

    def test_emergency_fallback_when_hospital_source_fails(self):
        result = find_pet_emergency_candidates(
            "목동역",
            when="2026-07-14",
            hospital_client=FakeSourceClient([], ok=False, error_ko="동물병원 조회에 실패했습니다."),
            pharmacy_client=FakeSourceClient([]),
            holiday_client=FakeHoliday(False),
        )
        self.assertTrue(result["animal_hospitals"])
        self.assertIn("전화 확인 필요", result["animal_hospitals"][0]["business_status"])
        self.assertTrue(any("내장 응급 연락 후보" in warning for warning in result["source_warnings_ko"]))

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
        self.assertEqual(_outing_intent("강아지랑 물놀이"), "water")

    def test_station_location_lookup(self):
        mokdong = region_centroid("목동역 근처")
        self.assertIsNotNone(mokdong)
        self.assertIn("목동", mokdong.label)
        self.assertAlmostEqual(mokdong.latitude, 37.5261, places=3)

        seoul = region_centroid("서울역")
        self.assertIsNotNone(seoul)
        self.assertIn("서울", seoul.label)

        city_hall = region_centroid("서울 시청역")
        self.assertIsNotNone(city_hall)
        self.assertIn("서울특별시", city_hall.address)

        self.assertEqual(region_centroid("서울시").address, "서울특별시")
        self.assertEqual(_outing_intent("비오는날 실내"), "indoor")
        self.assertEqual(_outing_intent("드라이브"), "drive")

    def test_outing_mood_intent_mapping(self):
        self.assertEqual(_outing_intent("강아지랑 쉬고 싶은데 어디로 가야해"), "relax")
        self.assertEqual(_outing_intent("조용하고 한적한 곳에서 힐링"), "relax")
        self.assertEqual(_outing_intent("사진 찍기 좋은 감성 있는 곳"), "photo")
        self.assertEqual(_outing_intent("신나게 뛰어놀 수 있는 곳"), "energetic")
        self.assertEqual(_outing_intent("더워서 시원한 곳"), "cool")
        self.assertEqual(_outing_intent("추워서 따뜻한 실내"), "indoor")
        self.assertEqual(_outing_intent("다른 강아지 친구 만날 수 있는 곳"), "social")
        self.assertEqual(_outing_intent("겁 많은 강아지랑 무난한 곳"), "easy")
        self.assertEqual(_outing_intent("강아지랑 펜션에서 쉬고 싶어"), "stay")

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

    def test_outing_keyword_search_is_limited(self):
        place_client = CountingPlaceClient(self.places)
        result = make_pet_outing_plan(
            "강남",
            outing_type="강아지랑 물놀이",
            place_client=place_client,
            weather_client=FakeWeather(self.weather),
            hospital_client=FakeSourceClient(self.hospitals),
            pharmacy_client=FakeSourceClient(self.pharmacies),
        )
        self.assertLessEqual(place_client.keyword_calls, 2)
        self.assertIn("summary_ko", result)

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
