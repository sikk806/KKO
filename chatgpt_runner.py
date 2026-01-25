import os
import json
import requests  # requests가 필요하므로 import 추가
from collections import deque
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY") # 카카오 키도 여기서 로드

# ---------------------------------------------------------
# [수정됨] mcp_server에서 가져오지 않고, 여기서 직접 정의합니다.
# @mcp.tool 데코레이터를 뺐기 때문에 일반 함수처럼 잘 실행됩니다.
# ---------------------------------------------------------
def search_places_by_kakao(query: str) -> str:
    """
    카카오 로컬 API를 통해 식당을 검색합니다. (Runner 전용 함수)
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query, "size": 5}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            places = response.json().get('documents', [])
            if not places: return "검색 결과가 없습니다."
            
            results = []
            for p in places:
                # 결과 포맷팅
                results.append(f"[{p['place_name']}] {p['category_name']} / {p['place_url']}")
            return "\n".join(results)
        return f"API 호출 실패: {response.status_code}"
    except Exception as e:
        return f"오류: {str(e)}"

# ---------------------------------------------------------

# GPT가 사용할 도구 정의
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_places_by_kakao",
            "description": "사용자의 취향에 맞는 장소를 카카오맵에서 검색합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색어 (예: 강남역 파스타)"},
                },
                "required": ["query"],
            },
        },
    }
]

def read_file_content(file_path):
    """
    파일 내용을 읽어서 문자열로 반환합니다.
    (GPT 토큰 제한을 막기 위해 마지막 2000줄만 읽습니다.)
    """
    # 따옴표 제거 (경로 복사 시 생기는 "" 제거)
    file_path = file_path.replace('"', '').replace("'", "").strip()

    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return None
        
    try:
        # 파일의 끝부분 2000줄만 읽기
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = deque(f, maxlen=2000)
            return "".join(lines)
    except Exception:
        # 인코딩 에러 시 재시도
        with open(file_path, 'r', encoding='cp949', errors='replace') as f:
            lines = deque(f, maxlen=2000)
            return "".join(lines)

def run():
    print("--- 카카오 다이닝 컨시어지 (Direct Upload) ---")
    
    # 1. 파일 받기
    file_path = input("📂 분석할 txt 파일명을 입력하세요 (예: 모바일 카카오톡.txt): ").strip()
    file_content = read_file_content(file_path)
    
    if not file_content:
        return

    print(f"✅ 파일 로드 완료! (대화 내용을 읽었습니다)")

    # 2. 질문 받기
    user_query = input("💬 질문을 입력하세요 (예: 맛집 추천해줘): ")

    # 3. 메시지 구성
    messages = [
        {
            "role": "system", 
            "content": "당신은 카카오톡 대화 로그를 분석하여 맛집을 추천하는 전문가입니다. 사용자가 제공한 대화 로그(Context)를 바탕으로 취향을 분석하고, 'search_places_by_kakao' 도구를 사용하여 실제 식당을 추천해주세요."
        },
        {
            "role": "user", 
            "content": f"""
            [대화 로그 파일 내용]
            {file_content}
            
            [사용자 질문]
            {user_query}
            """
        }
    ]

    print("⏳ GPT가 분석 및 검색 중...")

    # 4. GPT 호출
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    msg = response.choices[0].message
    
    # 5. GPT가 "검색이 필요해"라고 하면 도구 실행
    if msg.tool_calls:
        messages.append(msg) # 대화 맥락 유지
        
        for tool in msg.tool_calls:
            if tool.function.name == "search_places_by_kakao":
                # 검색어 추출
                args = json.loads(tool.function.arguments)
                query = args.get("query")
                print(f"🔍 [AI 판단] '{query}' 검색 중...")
                
                # 도구 실행 (이제 바로 위에 정의된 함수를 호출하므로 에러 없음!)
                search_result = search_places_by_kakao(query)
                
                # 결과 반환
                messages.append({
                    "tool_call_id": tool.id,
                    "role": "tool",
                    "name": "search_places_by_kakao",
                    "content": str(search_result)
                })
        
        # 6. 최종 답변 생성
        final_res = client.chat.completions.create(model="gpt-4o", messages=messages)
        print(f"\n🤖 답변:\n{final_res.choices[0].message.content}")
        
    else:
        # 도구 안 쓰고 바로 대답한 경우
        print(f"\n🤖 답변:\n{msg.content}")

if __name__ == "__main__":
    run()