from __future__ import annotations

import unittest

from mypet_life_mcp.core.schemas import SourceResult
from mypet_life_mcp.tools.food_safety import check_pet_food_safety


class FakeFoodClient:
    def __init__(self, product=None, normalized=None, ok=True):
        self.product = product
        self.normalized = normalized or {}
        self.ok = ok

    def search_product(self, food):
        if not self.ok:
            return SourceResult([], "Food Safety Korea C002", ok=False, error_ko="missing key")
        rows = self.product if self.product is not None else [{"RAWMTRL_NM": "코코아분말, 설탕"}]
        return SourceResult(rows, "Food Safety Korea C002")

    def normalize_ingredient(self, ingredient):
        if not self.ok:
            return SourceResult([], "Food Safety Korea I2520", ok=False, error_ko="missing key")
        item = self.normalized.get(ingredient)
        if item is not None:
            return SourceResult([item], "Food Safety Korea I2520") if item else SourceResult([], "Food Safety Korea I2520")
        if "코코아" in ingredient or "초코" in ingredient or "초콜릿" in ingredient:
            return SourceResult(
                [{"RPRSNT_RAWMTRL_NM": "코코아분말", "RAWMTRL_NCKNM": "카카오분말", "ENG_NM": "cocoa powder"}],
                "Food Safety Korea I2520",
            )
        return SourceResult([{"RPRSNT_RAWMTRL_NM": ingredient, "RAWMTRL_NCKNM": "", "ENG_NM": None}], "Food Safety Korea I2520")


class CountingFoodClient(FakeFoodClient):
    def __init__(self, product=None, normalized=None, ok=True):
        super().__init__(product, normalized, ok)
        self.product_calls = 0
        self.normalize_calls = 0

    def search_product(self, food):
        self.product_calls += 1
        return super().search_product(food)

    def normalize_ingredient(self, ingredient):
        self.normalize_calls += 1
        return super().normalize_ingredient(ingredient)


class FoodSafetyToolTests(unittest.TestCase):
    def test_dog_alias_normalizes(self):
        self.assertEqual(_call(pet_type="강아지")["pet_type"], "dog")

    def test_cat_alias_normalizes(self):
        self.assertEqual(_call(pet_type="고양이")["pet_type"], "cat")

    def test_invalid_pet_type(self):
        self.assertEqual(_call(pet_type="hamster")["status"], "invalid_request")

    def test_primary_food_is_first(self):
        result = _call(food="초코 쿠키", food_client=FakeFoodClient(product=[{"RAWMTRL_NM": "코코아분말, 설탕"}]))
        self.assertEqual(result["ingredients"][0]["input_name"], "초코 쿠키")
        self.assertEqual(result["ingredients"][0]["role"], "primary")

    def test_chocolate_is_danger(self):
        result = _call(food="강아지가 초콜릿을 먹었어", food_client=FakeFoodClient(product=[]))
        self.assertIn("초콜릿은 강아지에게 먹이면 안 되거나 위험할 수 있는 음식", result["summary_ko"])
        self.assertIn("구토", result["summary_ko"])

    def test_xylitol_is_danger_for_dog(self):
        result = _call(food="강아지가 자일리톨 껌을 먹은 것 같아", food_client=FakeFoodClient(product=[]))
        self.assertEqual(result["ingredients"][0]["evidence_status"], "SPECIES_REFERENCE_FOUND")
        self.assertIn("저혈당", result["summary_ko"])

    def test_xylitol_is_general_for_cat(self):
        result = _call(food="고양이가 자일리톨을 먹었어", pet_type="cat", food_client=FakeFoodClient(product=[]))
        self.assertEqual(result["ingredients"][0]["evidence_status"], "GENERAL_REFERENCE_FOUND")

    def test_grape_is_danger(self):
        result = _call(food="강아지가 포도를 먹었어", food_client=FakeFoodClient(product=[]))
        self.assertIn("포도는 강아지에게 먹이면 안 되거나 위험할 수 있는 음식", result["summary_ko"])
        self.assertIn("신장 이상", result["summary_ko"])

    def test_allium_korean_food_is_danger_for_cat(self):
        result = _call(food="고양이가 양파 들어간 음식을 먹었어", pet_type="고양이", food_client=FakeFoodClient(product=[]))
        self.assertIn("양파 들어간 음식은 고양이에게 먹이면 안 되거나 위험할 수 있는 음식", result["summary_ko"])
        self.assertIn("빈혈", result["summary_ko"])

    def test_almond_is_caution(self):
        result = _call(food="강아지가 아몬드를 먹었는데 괜찮아?", food_client=FakeFoodClient(product=[]))
        self.assertIn("아몬드는 강아지에게 소량만 조심해서 봐야 하는 음식입니다", result["summary_ko"])
        self.assertIn("소화기 불편", result["summary_ko"])
        self.assertNotIn("매칭", result["summary_ko"])

    def test_cucumber_is_ok(self):
        result = _call(food="강아지에게 오이 줘도 돼?", food_client=FakeFoodClient(ok=False))
        self.assertIn("오이는 강아지에게 좋은 간식으로 볼 수 있는 음식입니다", result["summary_ko"])
        self.assertIn("좋은 음식이어도 너무 많이 먹으면", result["summary_ko"])
        self.assertNotIn("강아지에게 오이 줘도 돼?는", result["summary_ko"])

    def test_reference_match_skips_food_api(self):
        client = CountingFoodClient(ok=False)
        result = _call(food="강아지 오이 먹어도 돼?", food_client=client)
        self.assertEqual(result["status"], "evidence_collected")
        self.assertEqual(client.product_calls, 0)
        self.assertEqual(client.normalize_calls, 0)

    def test_salmon_is_ok_for_cat(self):
        result = _call(food="고양이는 연어 먹어도 되나?", pet_type="cat", food_client=FakeFoodClient(product=[]))
        self.assertIn("연어는 고양이에게 소량이면 괜찮은 음식입니다", result["summary_ko"])

    def test_chili_pepper_is_caution(self):
        result = _call(food="강아지 고추 줘도 됨?", food_client=FakeFoodClient(ok=False))
        self.assertIn("고추는 강아지에게 먹이면 안 되거나 위험할 수 있는 음식입니다", result["summary_ko"])
        self.assertIn("위장 자극", result["summary_ko"])

    def test_kimchi_is_caution(self):
        result = _call(food="강아지 김치 먹어도 돼?", food_client=FakeFoodClient(product=[]))
        self.assertIn("김치는 강아지에게 먹이면 안 되거나 위험할 수 있는 음식입니다", result["summary_ko"])
        self.assertIn("먹은 양, 먹은 시간, 체중을 확인", result["summary_ko"])

    def test_ramen_is_caution(self):
        result = _call(food="고양이 라면 먹어도 돼?", pet_type="cat", food_client=FakeFoodClient(product=[]))
        self.assertIn("라면은 고양이에게 먹이면 안 되거나 위험할 수 있는 음식입니다", result["summary_ko"])

    def test_chicken_bone_is_caution(self):
        result = _call(food="강아지가 닭뼈를 먹었어", food_client=FakeFoodClient(product=[]))
        self.assertIn("닭뼈는 강아지에게 먹이면 안 되거나 위험할 수 있는 음식입니다", result["summary_ko"])
        self.assertIn("폐색 가능성", result["summary_ko"])

    def test_tangerine_is_ok(self):
        result = _call(food="강아지가 귤 먹었는데 괜찮아?", food_client=FakeFoodClient(product=[]))
        self.assertIn("귤은 강아지에게 소량이면 괜찮은 음식입니다", result["summary_ko"])

    def test_fruit_seed_is_danger(self):
        result = _call(food="강아지가 복숭아 씨를 먹었어", food_client=FakeFoodClient(product=[]))
        self.assertIn("복숭아 씨는 강아지에게 먹이면 안 되거나 위험할 수 있는 음식입니다", result["summary_ko"])
        self.assertIn("폐색 가능성", result["summary_ko"])

    def test_green_tomato_is_danger(self):
        result = _call(food="강아지가 덜 익은 토마토 먹었어", food_client=FakeFoodClient(product=[]))
        self.assertIn("덜 익은 토마토는 강아지에게 먹이면 안 되거나 위험할 수 있는 음식입니다", result["summary_ko"])
        self.assertIn("비틀거림", result["summary_ko"])

    def test_ripe_tomato_is_caution(self):
        result = _call(food="강아지 토마토 먹어도 돼?", food_client=FakeFoodClient(product=[]))
        self.assertIn("토마토는 강아지에게 소량만 조심해서 봐야 하는 음식입니다", result["summary_ko"])

    def test_citrus_peel_is_caution(self):
        result = _call(food="고양이가 귤 껍질 먹었어", pet_type="cat", food_client=FakeFoodClient(product=[]))
        self.assertIn("귤 껍질은 고양이에게 먹이면 안 되거나 위험할 수 있는 음식입니다", result["summary_ko"])

    def test_leafy_veg_is_caution(self):
        result = _call(food="강아지 시금치 줘도 돼?", food_client=FakeFoodClient(product=[]))
        self.assertIn("시금치는 강아지에게 소량만 조심해서 봐야 하는 음식입니다", result["summary_ko"])

    def test_edible_mushroom_is_ok(self):
        result = _call(food="강아지 표고버섯 줘도 돼?", food_client=FakeFoodClient(product=[]))
        self.assertIn("표고버섯은 강아지에게 소량이면 괜찮은 음식입니다", result["summary_ko"])

    def test_unknown_mushroom_is_avoid(self):
        result = _call(food="강아지가 야생버섯 먹었어", food_client=FakeFoodClient(product=[]))
        self.assertIn("야생버섯은 강아지에게 먹이면 안 되거나 위험할 수 있는 음식입니다", result["summary_ko"])

    def test_unknown_food_says_not_in_data(self):
        result = _call(food="강아지 콩국수 먹어도 돼?", food_client=FakeFoodClient(product=[]))
        self.assertIn("콩국수는 현재 보유한 음식 데이터에는 없는 항목입니다", result["summary_ko"])
        self.assertIn("인터넷으로 추가 확인하거나 동물병원에 문의", result["summary_ko"])

    def test_secondary_danger_can_drive_summary(self):
        client = CountingFoodClient(product=[{"RAWMTRL_NM": "밀가루, 코코아분말, 설탕"}])
        result = _call(food="쿠키", food_client=client)
        self.assertIn("쿠키는 강아지에게 먹이면 안 되거나 위험할 수 있는 음식", result["summary_ko"])
        self.assertEqual(client.product_calls, 1)

    def test_short_alias_does_not_match_inside_unrelated_word(self):
        product = [{"RAWMTRL_NM": "아세설팜칼륨, 효모추출물"}]
        result = _call(food="테스트음식", food_client=FakeFoodClient(product=product))
        self.assertNotIn("SPECIES_REFERENCE_FOUND", [item["evidence_status"] for item in result["ingredients"]])

    def test_food_key_missing_warns_but_reference_still_works(self):
        result = _call(food="초콜릿", food_client=FakeFoodClient(ok=False))
        self.assertEqual(result["source_warnings_ko"], [])
        self.assertEqual(result["ingredients"][0]["evidence_status"], "SPECIES_REFERENCE_FOUND")

    def test_positive_weight_and_amount(self):
        result = _call(weight_kg=5, amount_gram=20)
        self.assertEqual(result["weight_kg"], 5.0)
        self.assertEqual(result["amount_gram"], 20.0)

    def test_invalid_weight(self):
        self.assertEqual(_call(weight_kg=-1)["status"], "invalid_request")


def _call(**overrides):
    kwargs = {
        "food": "초코 쿠키",
        "pet_type": "dog",
        "food_client": FakeFoodClient(),
    }
    kwargs.update(overrides)
    return check_pet_food_safety(**kwargs)


if __name__ == "__main__":
    unittest.main()
