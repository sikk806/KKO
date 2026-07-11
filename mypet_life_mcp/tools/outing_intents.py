from __future__ import annotations

OUTING_TYPE_CONTENT_TYPE = {
    "숙소": "32",
    "펜션": "32",
    "호텔": "32",
    "캠핑": "32",
    "글램핑": "32",
    "식사": "39",
    "점심": "39",
    "저녁": "39",
    "밥": "39",
    "맛집": "39",
    "카페": "39",
    "놀이": "12",
    "놀거리": "12",
    "놀이터": "12",
    "산책": "12",
    "공원": "12",
    "등산": "12",
    "관광": "12",
    "여행": "12",
    "물놀이": "12",
    "해변": "12",
    "계곡": "12",
    "호수": "12",
    "walk": "12",
    "play": "12",
    "meal": "39",
    "stay": "32",
}

OUTING_INTENT_KEYWORDS = {
    "water": ["물놀이", "해변", "계곡", "바다", "호수", "강변", "반려견 놀이터"],
    "indoor": ["박물관", "쇼핑", "문화", "카페"],
    "cool": ["호수", "강변", "해변", "계곡", "숲", "카페"],
    "warm": ["카페", "실내", "문화", "박물관", "쇼핑"],
    "relax": ["카페", "호수공원", "휴양림", "공원", "한옥", "산책"],
    "photo": ["한옥", "전망", "해변", "공원", "카페", "문화"],
    "social": ["반려견 놀이터", "공원", "운동장", "카페"],
    "energetic": ["반려견 놀이터", "공원", "운동장", "레포츠", "산책"],
    "easy": ["공원", "산책", "카페", "반려견 놀이터"],
    "stay": ["애견펜션", "펜션", "글램핑", "캠핑", "호텔", "숙소"],
    "food": ["카페", "식당", "브런치", "베이커리", "맛집"],
    "play": ["반려견 놀이터", "공원", "산책", "휴양림", "등산", "관광"],
    "drive": ["관광", "시장", "한옥", "유람선", "해변"],
}

OUTING_INTENT_ALIASES = {
    "water": ["물놀이", "수영", "수영장", "해변", "바다", "계곡", "호수", "강가", "강변"],
    "indoor": ["실내", "비오는", "비 오는", "비올", "비 올", "비가", "눈오는", "눈 오는", "미세먼지"],
    "cool": ["시원", "더워", "더운", "여름", "그늘", "바람", "물가"],
    "warm": ["따뜻", "추워", "추운", "겨울", "포근"],
    "relax": ["휴식", "쉬고", "쉬는", "쉬러", "쉰다", "힐링", "조용", "한적", "여유", "느긋", "편하게", "피곤", "멍때", "쉬엄"],
    "photo": ["사진", "예쁜", "이쁜", "인생샷", "감성", "분위기", "데이트", "노을", "야경", "뷰좋", "전망"],
    "social": ["친구", "사회화", "다른강아지", "다른 강아지", "만나", "어울", "함께놀"],
    "energetic": ["신나", "활동적", "운동", "에너지", "스트레스", "뛰어", "뛰놀", "뛰고", "실컷"],
    "easy": ["안전", "무난", "가까운", "초보", "처음", "겁많", "겁 많은", "사람적", "사람 적"],
    "stay": ["숙소", "펜션", "호텔", "캠핑", "글램핑", "카라반", "1박", "여행"],
    "food": ["식사", "점심", "저녁", "밥", "맛집", "카페", "브런치", "베이커리"],
    "play": ["놀이", "놀이터", "운동장", "산책", "공원", "등산", "산에", "뛰어", "뛰놀", "휴양림"],
    "drive": ["드라이브", "차로", "바람쐬", "관광"],
}

OUTING_INTENT_CONTENT_TYPES = {
    "water": {"12", "25", "28"},
    "indoor": {"14", "38", "39"},
    "cool": {"12", "14", "39"},
    "warm": {"14", "38", "39"},
    "relax": {"12", "14", "32", "39"},
    "photo": {"12", "14", "39"},
    "social": {"12", "39"},
    "energetic": {"12", "25", "28"},
    "easy": {"12", "39"},
    "stay": {"32"},
    "food": {"39"},
    "play": {"12", "25", "28"},
    "drive": {"12", "25"},
}

SEMANTIC_FALLBACK_INTENTS = set(OUTING_INTENT_KEYWORDS)


def _content_type_for_outing(outing_type: str | None) -> str | None:
    if not outing_type:
        return None
    compact = outing_type.strip().lower().replace(" ", "")
    for keyword, content_type in OUTING_TYPE_CONTENT_TYPE.items():
        if keyword in compact:
            return content_type
    return None


def _outing_intent(outing_type: str | None) -> str | None:
    if not outing_type:
        return None
    compact = outing_type.strip().lower().replace(" ", "")
    if any(word in compact for word in ("펜션", "호텔", "캠핑", "글램핑", "카라반", "숙소", "1박")):
        return "stay"
    for intent, aliases in OUTING_INTENT_ALIASES.items():
        if any(alias.replace(" ", "") in compact for alias in aliases):
            return intent
    return None


def _keywords_for_outing(outing_type: str | None, intent: str) -> list[str]:
    compact = (outing_type or "").strip().lower().replace(" ", "")
    if any(word in compact for word in ("등산", "산에", "산책로")):
        return ["등산", "휴양림", "산책"]
    if any(word in compact for word in ("물놀이", "수영", "해변", "바다", "계곡", "호수", "강변", "강가")):
        return ["물놀이", "해변", "계곡", "호수", "바다"]
    if any(word in compact for word in ("공원", "놀이터", "운동장")):
        return ["반려견 놀이터", "공원", "호수공원", "산책"]
    if any(word in compact for word in ("실내", "비오는", "비오는날", "비오는 날", "미세먼지")):
        return ["박물관", "문화", "카페", "쇼핑"]
    if any(word in compact for word in ("휴식", "쉬고", "쉬는", "쉰다", "힐링", "조용", "한적", "여유", "느긋")):
        return ["카페", "호수공원", "휴양림", "공원", "한옥"]
    if any(word in compact for word in ("사진", "예쁜", "이쁜", "인생샷", "감성", "분위기", "노을", "야경", "전망")):
        return ["한옥", "전망", "공원", "해변", "카페"]
    if any(word in compact for word in ("시원", "더워", "더운", "여름", "그늘", "물가")):
        return ["호수", "강변", "해변", "계곡", "숲"]
    if any(word in compact for word in ("따뜻", "추워", "추운", "겨울", "포근")):
        return ["카페", "실내", "박물관", "문화", "쇼핑"]
    if any(word in compact for word in ("친구", "사회화", "다른강아지", "만나", "어울")):
        return ["반려견 놀이터", "공원", "운동장", "카페"]
    if any(word in compact for word in ("안전", "무난", "초보", "처음", "겁많", "사람적")):
        return ["공원", "산책", "카페", "반려견 놀이터"]
    return OUTING_INTENT_KEYWORDS[intent]
