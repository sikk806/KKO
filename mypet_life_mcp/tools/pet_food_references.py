from __future__ import annotations

from typing import Any

from mypet_life_mcp.tools.food_safety_helpers import compact


ASPCA_FOODS_URL = "https://www.aspca.org/pet-care/aspca-poison-control/people-foods-avoid-feeding-your-pets"
FDA_XYLITOL_URL = "https://www.fda.gov/animal-veterinary/animal-health-literacy/paws-xylitol-its-dangerous-dogs"
MERCK_GRAPE_URL = "https://www.merckvetmanual.com/toxicology/food-hazards/grape-raisin-and-tamarind-vitis-spp-tamarindus-spp-toxicosis-in-dogs"
LOCAL_GUIDE = "Curated Korean pet food guide"


def _ref(
    rid: str,
    label: str,
    aliases: list[str],
    species: list[str],
    severity: str,
    concern: str,
    signs: list[str],
    source: str = LOCAL_GUIDE,
    url: str = "",
    recommendation: str | None = None,
) -> dict[str, Any]:
    return {
        "id": rid,
        "label_ko": label,
        "aliases": aliases,
        "species": species,
        "severity": severity,
        "concern_ko": concern,
        "signs_ko": signs,
        "source_name": source,
        "source_url": url,
        "recommendation": recommendation or _default_recommendation(severity),
    }


def _default_recommendation(severity: str) -> str:
    if severity == "danger":
        return "avoid"
    if severity == "caution":
        return "limited"
    return "ok"


PET_FOOD_REFERENCES: list[dict[str, Any]] = [
    _ref("chocolate_caffeine", "초콜릿/카페인", ["초콜릿", "초코", "코코아", "카카오", "커피", "카페인", "chocolate", "cocoa", "coffee", "caffeine"], ["dog", "cat"], "danger", "메틸잔틴 성분으로 인한 중독 가능성이 알려져 있습니다.", ["구토", "설사", "헐떡임", "갈증/소변 증가", "과흥분", "심박 이상", "떨림", "발작"], "ASPCA People Foods to Avoid Feeding Your Pets", ASPCA_FOODS_URL),
    _ref("xylitol", "자일리톨", ["자일리톨", "무설탕껌", "무설탕 사탕", "xylitol", "sugar free gum"], ["dog"], "danger", "강아지에게 저혈당 및 간 손상 가능성이 알려져 있습니다.", ["구토", "무기력", "비틀거림", "발작", "저혈당", "간 이상"], "FDA Paws Off Xylitol", FDA_XYLITOL_URL),
    _ref("grape_raisin", "포도/건포도", ["포도", "건포도", "포도주스", "grape", "raisin", "currant", "tamarind"], ["dog"], "danger", "강아지에게 위장 증상 및 신장 손상 가능성이 알려져 있습니다.", ["구토", "설사", "무기력", "식욕 저하", "복통", "탈수", "떨림", "신장 이상"], "Merck Veterinary Manual", MERCK_GRAPE_URL),
    _ref("allium", "양파/마늘/파류", ["양파", "마늘", "대파", "쪽파", "부추", "양파분말", "마늘분말", "onion", "garlic", "chive", "leek"], ["dog", "cat"], "danger", "위장 자극과 적혈구 손상, 빈혈 가능성이 알려져 있습니다. 고양이가 더 민감할 수 있습니다.", ["구토", "설사", "위장 자극", "무기력", "빈혈", "잇몸 창백"], "ASPCA People Foods to Avoid Feeding Your Pets", ASPCA_FOODS_URL),
    _ref("fruit_pits_seeds", "과일 씨/씨앗/핵", ["사과씨", "사과 씨", "체리씨", "체리 씨", "복숭아씨", "복숭아 씨", "자두씨", "자두 씨", "살구씨", "살구 씨", "매실씨", "매실 씨", "과일씨", "과일 씨", "fruit pit", "fruit seed", "cherry pit", "peach pit", "plum pit", "apricot pit"], ["dog", "cat"], "danger", "일부 과일의 씨나 핵은 청색증 유발 성분, 목 막힘, 장 폐색 위험이 있어 과육과 분리해서 봐야 합니다.", ["구토", "설사", "침 흘림", "호흡 이상", "무기력", "목 막힘", "복부 불편", "폐색 가능성"], "Curated from ASPCA fruit/vegetable guidance", ASPCA_FOODS_URL),
    _ref("nightshade_green_parts", "덜 익은 토마토/감자 싹", ["덜익은토마토", "덜 익은 토마토", "초록토마토", "초록 토마토", "토마토잎", "토마토 잎", "토마토줄기", "토마토 줄기", "감자싹", "감자 싹", "초록감자", "초록 감자", "싹난감자", "싹난 감자", "green tomato", "tomato leaf", "tomato stem", "potato sprout", "green potato"], ["dog", "cat"], "danger", "가지과 식물의 덜 익은 열매, 잎, 줄기, 싹에는 위장 및 신경계 자극 가능 성분이 있어 먹이지 않는 편이 안전합니다.", ["구토", "설사", "침 흘림", "무기력", "복부 불편", "비틀거림", "떨림"], "Curated veterinary toxic plant guidance", LOCAL_GUIDE),
    _ref("rhubarb_leaf", "루바브 잎", ["루바브잎", "루바브 잎", "대황잎", "대황 잎", "rhubarb leaf", "rhubarb leaves"], ["dog", "cat"], "danger", "루바브 잎은 옥살산염 등으로 위장 자극과 신장 부담 가능성이 있어 먹이지 않는 편이 안전합니다.", ["구토", "설사", "침 흘림", "무기력", "떨림", "신장 이상"], "Curated veterinary toxic plant guidance", LOCAL_GUIDE),
    _ref("alcohol_yeast_dough", "알코올/효모 반죽", ["알코올", "술", "맥주", "와인", "효모반죽", "날반죽", "yeast dough", "raw dough", "alcohol"], ["dog", "cat"], "danger", "알코올 중독 또는 반죽 팽창으로 인한 위장 응급 가능성이 알려져 있습니다.", ["구토", "설사", "비틀거림", "호흡 이상", "떨림", "혼수", "복부 팽만"], "ASPCA People Foods to Avoid Feeding Your Pets", ASPCA_FOODS_URL),
    _ref("macadamia", "마카다미아", ["마카다미아", "macadamia"], ["dog"], "danger", "강아지에게 무기력, 비틀거림 등 이상 증상 가능성이 알려져 있습니다.", ["구토", "설사", "무기력", "비틀거림", "떨림", "고열"], "ASPCA People Foods to Avoid Feeding Your Pets", ASPCA_FOODS_URL),
    _ref("avocado", "아보카도", ["아보카도", "avocado"], ["dog", "cat"], "caution", "기름기가 많고 껍질/씨는 막힘 위험도 있어 급여하지 않는 편이 안전합니다.", ["구토", "설사", "복부 불편", "폐색 가능성"], recommendation="avoid"),
    _ref("nuts", "견과류", ["견과류", "아몬드", "호두", "피칸", "땅콩", "almond", "walnut", "pecan", "peanut"], ["dog", "cat"], "caution", "고지방 견과는 소화 불편이나 췌장 부담 가능성이 있어 주의가 필요합니다.", ["구토", "설사", "소화기 불편", "복부 불편", "무기력", "췌장 부담"]),
    _ref("dairy", "우유/유제품", ["우유", "치즈", "크림", "요거트", "아이스크림", "유제품", "milk", "cheese", "cream", "yogurt"], ["dog", "cat"], "caution", "유당 분해가 어려워 소화기 불편이 생길 수 있습니다.", ["설사", "소화 불편", "복부 불편"]),
    _ref("raw_bone", "생고기/날달걀/뼈", ["생고기", "날고기", "날달걀", "생달걀", "익힌뼈", "닭뼈", "돼지뼈", "소뼈", "raw meat", "raw egg", "bone"], ["dog", "cat"], "caution", "세균 노출, 소화관 손상, 폐색 가능성이 알려져 있어 먹이지 않는 편이 안전합니다.", ["구토", "설사", "복통", "소화관 손상", "폐색 가능성"], recommendation="avoid"),
    _ref("spicy_salty", "맵고 짠 음식", ["김치", "떡볶이", "라면", "짬뽕", "마라탕", "김치찌개", "부대찌개", "된장찌개", "고추", "고춧가루", "청양고추", "매운고추"], ["dog", "cat"], "caution", "맵고 짠 양념은 위장 자극과 염분 부담을 줄 수 있어 먹이지 않는 편이 안전합니다.", ["구토", "설사", "침 흘림", "복부 불편", "위장 자극", "갈증/소변 증가"], recommendation="avoid"),
    _ref("citrus_parts", "감귤류 껍질/씨/신 과일", ["귤껍질", "귤 껍질", "오렌지껍질", "오렌지 껍질", "레몬", "라임", "자몽", "유자", "레몬껍질", "레몬 껍질", "라임껍질", "라임 껍질", "자몽껍질", "자몽 껍질", "citrus peel", "lemon", "lime", "grapefruit"], ["dog", "cat"], "caution", "감귤류의 껍질, 씨, 잎, 강한 산미는 위장 자극을 줄 수 있어 먹이지 않는 편이 안전합니다.", ["구토", "설사", "침 흘림", "복부 불편", "무기력"], recommendation="avoid"),
    _ref("ripe_tomato", "익은 토마토", ["토마토", "방울토마토", "익은토마토", "익은 토마토", "tomato", "cherry tomato"], ["dog", "cat"], "caution", "익은 과육만 소량이면 큰 문제가 적은 편이지만, 잎/줄기/덜 익은 부분과 많은 양은 피하는 편이 좋습니다.", ["구토", "설사", "침 흘림", "복부 불편"]),
    _ref("leafy_oxalate_veg", "옥살산 많은 잎채소", ["시금치", "케일", "근대", "비트잎", "비트 잎", "청경채", "spinach", "kale", "chard", "beet greens", "bok choy"], ["dog", "cat"], "caution", "일부 잎채소는 옥살산염이나 섬유질 부담이 있어 익혀도 많이 주지 않는 편이 좋습니다.", ["구토", "설사", "복부 불편", "소변 이상"]),
    _ref("corn_cob", "옥수수 심/속대", ["옥수수심", "옥수수 심", "옥수수대", "옥수수 대", "옥수수속대", "옥수수 속대", "corn cob"], ["dog", "cat"], "caution", "옥수수 알갱이보다 심이나 속대가 문제이며, 삼키면 목 막힘이나 장 폐색 위험이 있어 먹이면 안 됩니다.", ["구토", "기침", "목 막힘", "복부 불편", "폐색 가능성"], recommendation="avoid"),
    _ref("mushroom_unknown", "야생버섯/종류 불명 버섯", ["야생버섯", "독버섯", "산버섯", "모르는버섯", "모르는 버섯", "종류 모르는 버섯", "wild mushroom", "unknown mushroom"], ["dog", "cat"], "caution", "버섯은 종류에 따라 위험도가 크게 달라서, 야생버섯이나 종류를 모르는 버섯은 먹이지 않는 편이 안전합니다.", ["구토", "설사", "침 흘림", "무기력", "떨림", "비틀거림"], recommendation="avoid"),
    _ref("edible_mushroom", "일반 식용 버섯", ["버섯", "표고버섯", "양송이버섯", "새송이버섯", "느타리버섯", "팽이버섯", "mushroom", "shiitake", "button mushroom", "oyster mushroom"], ["dog", "cat"], "ok", "일반 식용 버섯은 양념 없이 충분히 익힌 경우 소량이면 괜찮은 편입니다.", ["구토", "설사", "복부 불편"], recommendation="ok"),
    _ref("salty_processed", "가공육/짠 반찬", ["햄", "소시지", "베이컨", "스팸", "어묵", "젓갈", "멸치볶음", "장조림", "processed meat", "sausage", "bacon"], ["dog", "cat"], "caution", "염분과 지방, 양념이 많아 소화기 불편과 췌장 부담이 생길 수 있어 먹이지 않는 편이 안전합니다.", ["구토", "설사", "갈증/소변 증가", "복부 불편", "췌장 부담"], recommendation="avoid"),
    _ref("fried_fatty", "튀김/기름진 음식", ["치킨", "후라이드치킨", "양념치킨", "튀김", "돈까스", "삼겹살", "족발", "보쌈", "곱창", "막창"], ["dog", "cat"], "caution", "기름기와 양념이 많아 소화기 불편이나 췌장 부담이 생길 수 있어 먹이지 않는 편이 안전합니다.", ["구토", "설사", "복부 불편", "무기력", "췌장 부담"], recommendation="avoid"),
    _ref("mixed_korean_meal", "양념된 한식/분식", ["김밥", "비빔밥", "불고기", "갈비", "제육볶음", "카레", "짜장면", "잡채", "볶음밥", "만두", "순대"], ["dog", "cat"], "caution", "사람용 양념, 소금, 마늘/양파가 들어갈 수 있어 성분 확인 없이 급여하지 않는 편이 안전합니다.", ["구토", "설사", "위장 자극", "갈증/소변 증가", "무기력"], recommendation="avoid"),
    _ref("rice_cake", "떡/찹쌀 음식", ["떡", "인절미", "가래떡", "송편", "찹쌀떡", "rice cake"], ["dog", "cat"], "caution", "끈적한 식감 때문에 목 막힘이나 소화 불편이 생길 수 있습니다.", ["구토", "기침", "목 막힘", "복부 불편"]),
    _ref("seafood_raw_salty", "회/해산물/건어물", ["회", "초밥", "참치회", "연어회", "오징어", "문어", "새우", "게", "조개", "황태", "북어", "멸치"], ["dog", "cat"], "caution", "날것, 뼈/가시, 염분, 알레르기 가능성 때문에 소량이라도 상태 확인이 필요합니다.", ["구토", "설사", "가려움", "복부 불편", "목 걸림"]),
    _ref("sweets", "단 음식", ["사탕", "젤리", "케이크", "쿠키", "과자", "빵", "도넛", "초코파이", "마카롱", "탕후루"], ["dog", "cat"], "caution", "당분과 지방이 많고 일부 제품은 초콜릿/자일리톨이 들어갈 수 있어 성분 확인이 필요합니다.", ["구토", "설사", "복부 불편", "무기력"]),
    _ref("great_veg", "좋은 간식 채소", ["오이", "당근", "애호박", "cucumber", "carrot", "zucchini"], ["dog", "cat"], "ok", "수분이나 식이섬유가 있고 양념 없이 작게 잘라 주면 좋은 간식으로 볼 수 있습니다.", ["설사", "복부 불편"], recommendation="great"),
    _ref("safe_veg", "괜찮은 채소", ["브로콜리", "양배추", "양상추", "그린빈", "껍질콩", "green bean", "broccoli", "cabbage", "lettuce"], ["dog", "cat"], "ok", "양념 없이 작게 잘라 소량 급여하는 정도는 대체로 가능하지만, 많이 먹으면 소화 불편이 생길 수 있습니다.", ["설사", "복부 불편"], recommendation="ok"),
    _ref("great_fruit", "좋은 간식 과일", ["블루베리", "수박", "딸기", "blueberry", "watermelon", "strawberry"], ["dog", "cat"], "ok", "씨와 껍질을 정리하고 과육만 조금 주면 좋은 간식으로 볼 수 있습니다.", ["구토", "설사", "복부 불편"], recommendation="great"),
    _ref("safe_fruit", "괜찮은 과일", ["사과", "배", "바나나", "귤", "감귤", "orange", "apple", "banana", "pear"], ["dog", "cat"], "ok", "씨, 껍질, 심지, 과량의 당분은 주의하고 과육만 소량 급여하는 편이 좋습니다.", ["구토", "설사", "복부 불편"], recommendation="ok"),
    _ref("great_starch", "좋은 담백 간식", ["고구마", "단호박", "호박", "sweet potato", "pumpkin"], ["dog", "cat"], "ok", "양념 없이 익힌 뒤 조금 주면 포만감 있는 좋은 간식으로 볼 수 있습니다.", ["설사", "복부 불편"], recommendation="great"),
    _ref("safe_starch", "괜찮은 탄수화물", ["밥", "흰쌀밥", "쌀밥", "감자", "rice", "potato"], ["dog", "cat"], "ok", "양념 없이 익힌 상태라면 소량은 대체로 가능하지만 주식처럼 많이 주지는 않는 편이 좋습니다.", ["설사", "복부 불편"], recommendation="ok"),
    _ref("safe_protein", "괜찮은 단백질", ["닭가슴살", "닭고기", "소고기", "돼지고기", "연어", "계란", "삶은계란", "두부", "chicken", "beef", "pork", "salmon", "egg", "tofu"], ["dog", "cat"], "ok", "양념 없이 충분히 익힌 살코기나 단백질은 소량 급여 가능하지만, 뼈/가시/기름/간은 제거해야 합니다.", ["구토", "설사", "복부 불편"], recommendation="ok"),
]


def match_pet_food_references(values: list[str], species: str) -> list[dict[str, Any]]:
    haystacks = [compact(value) for value in values if value]
    matches: list[dict[str, Any]] = []
    seen: set[str] = set()
    for reference in PET_FOOD_REFERENCES:
        if reference["id"] in seen or not _matches_any_alias(reference["aliases"], haystacks):
            continue
        seen.add(reference["id"])
        match_species = species if species in reference["species"] else None
        matches.append(_evidence(reference, match_species))
    return matches


def _evidence(reference: dict[str, Any], match_species: str | None) -> dict[str, Any]:
    return {
        "source": reference["source_name"],
        "source_url": reference["source_url"],
        "reference_id": reference["id"],
        "title": reference["label_ko"],
        "summary": reference["concern_ko"],
        "severity": reference["severity"],
        "species": match_species,
        "matched_species": reference["species"],
        "signs_ko": reference["signs_ko"],
        "recommendation": reference["recommendation"],
    }


def _matches_any_alias(aliases: list[str], haystacks: list[str]) -> bool:
    return any(_matches_alias(compact(alias), haystack) for alias in aliases for haystack in haystacks)


def _matches_alias(needle: str, haystack: str) -> bool:
    if len(needle) <= 1:
        if needle in {"귤", "배", "떡"}:
            return needle in haystack
        return needle == haystack
    return needle in haystack
