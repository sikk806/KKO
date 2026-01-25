import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")

app = FastAPI()

# 데이터 받을 그릇(Schema) 정의
class SearchQuery(BaseModel):
    keyword: str

@app.get("/")
def read_root():
    return {"status": "Server is running"}

@app.post("/search_kakao")
def search_places(data: SearchQuery):
    """
    ChatGPT가 이 주소로 검색어를 보내면, 카카오 API 결과를 돌려줍니다.
    """
    print(f"🔎 ChatGPT가 검색 요청함: {data.keyword}")
    
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": data.keyword, "size": 5}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            places = response.json().get('documents', [])
            results = []
            for p in places:
                results.append({
                    "name": p['place_name'],
                    "category": p['category_name'],
                    "url": p['place_url'],
                    "address": p['address_name']
                })
            return {"results": results}
        return {"error": "Kakao API Error"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    # 8000번 포트에서 서버 실행
    uvicorn.run(app, host="0.0.0.0", port=8000)