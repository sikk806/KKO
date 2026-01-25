import os
import requests
from fastmcp import FastMCP
from dotenv import load_dotenv

# 파싱 함수 가져오기
from parsing import parse_text_string
# intelligence는 이제 툴 내부 로직보다는 LLM의 추론을 유도하는 쪽으로 가므로 
# 분석 결과 구조체만 활용하거나, 간단한 통계용으로 씁니다.
from intelligence import analyze_chat

load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")

mcp = FastMCP("KakaoDiningConcierge")

# ---------------------------------------------------------------------
# [기능 1] 미리 정의된 프롬프트 (사용자가 불러올 수 있음)
# ---------------------------------------------------------------------
@mcp.prompt()
def dining_persona_prompt() -> str:
    """
    카카오 다이닝 컨시어지의 페르소나와 행동 지침을 불러옵니다.
    """
    return """
    당신은 '카카오 모임 설계 전문 AI'입니다.
    
    [행동 강령]
    1. 사용자가 업로드한 대화 로그를 `analyze_uploaded_chat_log` 도구로 분석하십시오.
    2. 분석 결과와 대화 내용을 바탕으로 참여자들의 '성향(Persona)', '직업', '관계'를 추론하십시오.
    3. 추론된 페르소나에 맞춰 '창의적인 검색어'를 생성하십시오.
       (예: 단순 '맛집' -> '개발팀이 회식하기 좋은 구워주는 고기집', '소개팅 2차로 좋은 조용한 칵테일바')
    4. `search_places_by_kakao` 도구로 장소를 검색하고, 추천 사유를 성향과 연결 지어 설명하십시오.
    """

# ---------------------------------------------------------------------
# [Tool 1] 텍스트 내용 분석 (설명서 강화 버전)
# ---------------------------------------------------------------------
@mcp.tool
def analyze_uploaded_chat_log(chat_content: str) -> str:
    """
    [핵심 도구] 사용자가 업로드한 카카오톡 대화 내용(Text)을 받아 기초 데이터를 분석합니다.
    
    ★★ AI 모델을 위한 지시사항 (Instruction) ★★
    이 도구를 호출한 뒤, 반환된 데이터를 바탕으로 반드시 '참여자 페르소나(Persona)'를 프로파일링 하십시오.
    - 대화 내용을 통해 참여자의 직업, 나이대, 모임의 성격(회식, 데이트, 친구)을 파악해야 합니다.
    - 파악된 페르소나를 기반으로 'search_places_by_kakao' 도구에 들어갈 '구체적인 검색어(Query)'를 생성하십시오.
    - 단순한 지역명+메뉴명 조합을 피하고, 카카오맵 검색을 위해 검색어는 반드시 '지역명 + 핵심단어' 형태로 만드십시오.
    예: '서울 유쾌한 분위기의 취업 축하 모임' (X) -> '서울 파티룸' 또는 '홍대 룸술집' (O)
    불필요한 형용사를 제거하고 구체적인 장소 카테고리를 포함하십시오.
    """
    
    if not chat_content or len(chat_content.strip()) < 10:
        return "오류: 대화 내용이 너무 짧습니다."

    try:
        # 1. 파싱
        parsed_data = parse_text_string(chat_content)
        if not parsed_data or not parsed_data['messages']:
            return "오류: 파싱 실패. 카카오톡 내보내기 형식이 아닙니다."
            
        # 2. 임시 저장 및 통계 분석
        import json
        temp_path = "temp_uploaded.json"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False)
            
        analysis_result = analyze_chat(temp_path)
        
        if not analysis_result:
            return "통계적 분석 결과 없음."

        # 3. 결과 반환 (LLM이 읽고 '아, 이런 사람들이구나' 하고 느끼게 만듦)
        return f"""
        [데이터 통계 분석 완료]
        - 최다 언급 메뉴: {analysis_result.get('preferences')}
        - 주요 활동 지역: {analysis_result.get('location')}
        - 감지된 분위기 키워드: {analysis_result.get('mood')}
        
        * 위 데이터를 참고하되, 대화 원본의 뉘앙스를 파악하여 
          참여자들이 '진짜로 원할법한' 장소를 추론하여 검색 단계로 넘어가십시오. *
        """
        
    except Exception as e:
        return f"처리 중 에러: {str(e)}"

# ---------------------------------------------------------------------
# [Tool 2] 카카오맵 검색 (그대로 유지)
# ---------------------------------------------------------------------
@mcp.tool
def search_places_by_kakao(query: str) -> str:
    """
    분석된 페르소나와 니즈를 반영한 '검색어(Query)'로 장소를 검색합니다.
    식당, 카페, 문화공간 등 카테고리 제한 없이 검색 가능합니다.
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query, "size": 5}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            places = response.json().get('documents', [])
            if not places: return f"'{query}'에 대한 검색 결과가 없습니다. 검색어를 바꿔보세요."
            
            results = []
            for p in places:
                # 결과에 카테고리 정보 포함 (카페인지 식당인지 알기 위해)
                info = (f"[{p['place_name']}] - {p['category_name']}\n"
                        f"   주소: {p['address_name']}\n"
                        f"   URL: {p['place_url']}")
                results.append(info)
            return "\n\n".join(results)
        return f"API 호출 실패: {response.status_code}"
    except Exception as e:
        return f"오류: {str(e)}"

if __name__ == "__main__":
    mcp.run()