# 🍽️ KakaoDiningConcierge
 
카카오톡 대화 로그를 AI로 분석해 **맞춤형 맛집·장소를 추천**해주는 프로젝트입니다.
대화 내용에서 참여자들의 취향, 분위기, 지역을 파악한 뒤, 카카오 로컬 API로 실제 장소를 검색해 제안합니다.
 
---
 
## 📌 주요 기능
 
- **카카오톡 대화 파싱** — PC / 모바일 내보내기 형식(.txt) 모두 지원
- **GPT-4o 기반 취향 분석** — 대화 뉘앙스에서 선호 메뉴, 지역, 분위기 추출
- **카카오 로컬 API 장소 검색** — 분석된 페르소나에 맞는 검색어로 실제 장소 검색
- **MCP 서버** — Claude 등 MCP 호환 AI 클라이언트와 연동 가능
- **REST API 서버** — ChatGPT Actions 등 외부 AI 서비스와 HTTP로 연동 가능
 
---
 
## 🗂️ 프로젝트 구조
 
```
KKO/
├── parsing.py            # 카카오톡 .txt 파일 → 구조화 JSON 파싱
├── intelligence.py       # GPT-4o로 대화 분석 → 취향/지역/분위기/검색어 추출
├── mcp_server.py         # FastMCP 기반 MCP 서버 (Claude 등 AI와 직접 연동)
├── chatgpt_runner.py     # CLI 실행기 — 파일 입력 후 GPT-4o 함수 호출로 추천
├── api_server.py         # FastAPI REST 서버 (/search_kakao 엔드포인트)
├── app.py                # 카카오 API 단독 테스트 스크립트
├── server_playmcp.py     # PlayMCP용 HTTP ↔ stdio 브리지 서버
├── ngrok.yaml            # ngrok 터널 설정 (외부 공개용)
├── requirements.txt      # Python 의존성 목록
├── PC카카오톡.txt         # PC 카카오톡 내보내기 샘플
└── 모바일 카카오톡.txt    # 모바일 카카오톡 내보내기 샘플
```
 
---
 
## ⚙️ 설치 및 환경 설정
 
### 1. 패키지 설치
 
```bash
pip install -r requirements.txt
```
 
### 2. 환경 변수 설정 (`.env` 파일 생성)
 
```env
KAKAO_API_KEY=your_kakao_rest_api_key
OPENAI_API_KEY=your_openai_api_key
```
 
- **KAKAO_API_KEY** — [카카오 개발자 콘솔](https://developers.kakao.com)에서 REST API 키 발급
- **OPENAI_API_KEY** — [OpenAI Platform](https://platform.openai.com)에서 발급
 
---
 
## 🚀 실행 방법
 
### ① CLI로 바로 실행 (가장 간단)
 
```bash
python chatgpt_runner.py
```
 
실행 후 카카오톡 .txt 파일 경로와 질문을 입력하면 GPT-4o가 대화를 분석해 맛집을 추천합니다.
 
```
📂 분석할 txt 파일명을 입력하세요: 모바일 카카오톡.txt
💬 질문을 입력하세요: 우리 팀 회식 장소 추천해줘
```
 
### ② MCP 서버로 실행 (Claude / MCP 클라이언트 연동)
 
```bash
python mcp_server.py
```
 
MCP 호환 AI 클라이언트(Claude Desktop 등)에서 두 가지 도구를 사용할 수 있습니다.
 
| 도구 | 설명 |
|------|------|
| `analyze_uploaded_chat_log` | 카카오톡 대화 텍스트를 받아 취향·지역·분위기 분석 |
| `search_places_by_kakao` | 분석된 키워드로 카카오맵에서 장소 검색 |
 
### ③ REST API 서버로 실행 (ChatGPT Actions 등 연동)
 
```bash
python api_server.py
```
 
`POST /search_kakao` 엔드포인트에 검색어를 전달하면 카카오 로컬 API 결과를 반환합니다.
 
```json
POST http://localhost:8000/search_kakao
{ "keyword": "홍대 칵테일바" }
```
 
### ④ ngrok으로 외부 공개 (옵션)
 
```bash
ngrok start --all --config ngrok.yaml
```
 
로컬 서버를 외부 URL로 노출해 ChatGPT Actions, PlayMCP 등 클라우드 서비스와 연동할 때 사용합니다.
 
### ⑤ PlayMCP 브리지 서버
 
```bash
python server_playmcp.py
```
 
PlayMCP가 HTTP POST로 요청을 보내면 내부적으로 MCP 서버(stdio)와 통신을 중계합니다.
 
---
 
## 🔄 전체 동작 흐름
 
```
카카오톡 .txt 파일
        ↓
   parsing.py  →  메시지 구조화 (sender / content)
        ↓
  intelligence.py  →  GPT-4o 분석 → 취향·지역·무드·검색어 추출
        ↓
   카카오 로컬 API  →  실제 장소 5개 검색
        ↓
   GPT-4o 최종 정리  →  추천 사유와 함께 장소 제안
```
 
---
 
## 📝 참고 사항
 
- 카카오톡 대화 파싱은 **모바일·PC 내보내기 형식** 모두 지원하며, 토큰 절약을 위해 최근 500개 메시지만 사용합니다.
- 리뷰/평점 스크래핑 기능은 현재 더미 데이터로 대체되어 있으며 추후 구현 예정입니다.
- `ngrok.yaml`의 인증 토큰은 개인 토큰이므로 공개 저장소 업로드 시 주의하세요.
