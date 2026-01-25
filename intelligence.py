import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_chat(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        chat_data = json.load(f)
    
    messages = chat_data.get('messages', [])
    # 최근 50개 추출
    target_messages = messages[-50:]
    chat_context = "\n".join([f"[{m['sender']}] {m['content']}" for m in target_messages])

    # [핵심 로그] 실제로 AI에게 전달되는 내용을 출력하여 확인합니다.
    print("\n" + "="*30 + " [AI 전송 데이터 확인] " + "="*30)
    print(chat_context)
    print("="*80 + "\n")

    system_instruction = """
    당신은 한국 로컬 다이닝 전문 컨시어지입니다.
    사용자의 대화 로그(json)를 분석하여 선호도와 검색 쿼리를 도출하십시오.
    
    [주의사항]
    1. 대화 내용에 명시적인 맛집 언급이 없더라도, 평소 대화 스타일이나 말투를 통해 
       사용자가 좋아할 법한 '추천 검색어(search_query)'를 최소 하나는 생성하십시오.
    2. 결과는 반드시 'json' 형식이어야 합니다.
    
    {
        "preferences": "추출된 키워드",
        "location": "언급된 지역 또는 서울",
        "mood": "대화 분위기",
        "search_query": "카카오맵 추천 검색어"
    }
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"이 데이터를 json으로 분석해줘:\n\n{chat_context}"}
            ],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ 오류: {e}")
        return None

if __name__ == "__main__":
    result = analyze_chat("mobile_parsed_filtered.json")
    if result:
        print("🎯 AI 분석 결과:", json.dumps(result, indent=2, ensure_ascii=False))