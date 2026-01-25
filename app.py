import os
import requests
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")

if not KAKAO_API_KEY:
    raise ValueError("❌ .env 파일에서 KAKAO_API_KEY를 찾을 수 없습니다.")

def search_keyword(query):
    """
    카카오 로컬 API: 장소 검색 및 URL 반환 (정상 작동 확인됨)
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query, "size": 1} 
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        documents = response.json().get('documents')
        if documents:
            place = documents[0]
            print(f"✅ API 검색 성공: {place['place_name']}")
            print(f"🔗 카카오맵 URL: {place['place_url']}")
            return place
        else:
            print("❌ 검색 결과가 없습니다.")
            return None
    else:
        print(f"❌ API 호출 실패: {response.status_code}")
        return None

def get_reviews_dummy(place_url):
    """
    [임시 조치]
    실제 스크래핑 대신 임시(Dummy) 평점과 리뷰 데이터를 반환합니다.
    추후 스크래핑 로직이나 다른 API로 교체될 예정입니다.
    """
    print(f"⚠️ [임시] {place_url}에서 리뷰 데이터를 가져오는 척(Mocking) 합니다.")
    
    # 임시 데이터 구조
    dummy_data = {
        "rating": "4.5",
        "reviews": [
            "분위기가 너무 좋고 음식이 맛있어요.",
            "주말에는 웨이팅이 좀 있지만 기다릴 만합니다.",
            "가격 대비 양이 푸짐해요."
        ]
    }
    
    print(f"⭐ 평점(임시): {dummy_data['rating']}")
    print(f"📝 리뷰(임시): {dummy_data['reviews']}")
    
    return dummy_data

if __name__ == "__main__":
    # 1. API 테스트
    keyword = "강남역 파스타"
    place_info = search_keyword(keyword)
    
    # 2. 리뷰 데이터 확보 (지금은 임시 데이터 사용)
    if place_info:
        reviews = get_reviews_dummy(place_info['place_url'])
        
        # 3. (나중을 위한) 통합 데이터 출력 예시
        final_result = {
            "name": place_info['place_name'],
            "address": place_info['address_name'],
            "rating": reviews['rating'],
            "recent_reviews": reviews['reviews']
        }
        print("\n--- 최종 결과 데이터 (Next Step으로 넘길 데이터) ---")
        print(final_result)