from __future__ import annotations

import unittest

from mypet_life_mcp.tools.data_files import load_data_json


class DataFileTests(unittest.TestCase):
    def test_pet_food_reference_data_shape(self):
        references = load_data_json("pet_food_references.json")
        self.assertGreaterEqual(len(references), 30)
        for item in references:
            self.assertTrue(item["id"])
            self.assertTrue(item["label_ko"])
            self.assertTrue(item["aliases"])
            self.assertTrue(item["species"])
            self.assertIn(item["severity"], {"danger", "caution", "ok"})
            self.assertTrue(item["concern_ko"])
            self.assertTrue(item["signs_ko"])
            self.assertIn(item["recommendation"], {"avoid", "limited", "ok", "great"})

    def test_location_data_shape(self):
        aliases = load_data_json("region_aliases.json")
        centroids = load_data_json("region_centroids.json")
        sigungu = load_data_json("region_sigungu.json")
        stations = load_data_json("station_locations.json")

        self.assertEqual(aliases["서울"], "서울특별시")
        self.assertIn("서울특별시", centroids)
        self.assertIn("province_area", sigungu)
        self.assertGreaterEqual(len(stations), 1000)
        self.assertTrue(all("latitude" in item and "longitude" in item for item in stations))

    def test_emergency_fallback_data_shape(self):
        data = load_data_json("emergency_fallbacks.json")
        self.assertTrue(data["source"])
        self.assertIn("서울", data["seoul_keywords"])
        self.assertTrue(data["seoul_hospitals"])
        for hospital in data["seoul_hospitals"]:
            self.assertTrue(hospital["name"])
            self.assertTrue(hospital["phone"])
            self.assertEqual(hospital["business_status"], "전화 확인 필요")
