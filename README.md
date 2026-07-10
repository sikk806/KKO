# MyPet Life MCP

MyPet Life MCP는 반려동물 보호자가 외출, 여행, 휴일, 야간 상황에서 참고할 수 있는 공공데이터 기반 후보를 정리하는 PlayMCP-ready MCP 서버입니다.

이 서버는 진단, 처방, 응급 진료 가능 여부, 영업 중 여부, 반려동물 동반 가능 여부를 보장하지 않습니다. 모든 결과는 후보 정보이며 방문 전 전화 확인이 필요합니다.

## 제공 도구

- `find_pet_emergency_candidates`: 휴일, 야간, 주말 상황에서 동물병원과 동물약국 연락 후보를 정리합니다.
- `make_pet_care_map`: 외출 또는 여행 위치 주변의 동물병원/동물약국 후보를 정리합니다.
- `make_pet_outing_plan`: 반려동물 동반 장소, 날씨, 주변 돌봄 연락처를 묶어 외출 계획을 제안합니다.
- `verify_pet_business`: 반려동물 호텔, 미용, 운송, 장묘 등 업체가 공식 인허가 후보에 나타나는지 확인합니다.

## 주요 특징

- 현재 위치 좌표(`latitude`, `longitude`)를 직접 받으면 카카오 Local API 없이도 동작합니다.
- 동물병원/동물약국/인허가 정보는 공공데이터 기반 후보로 제공합니다.
- 공휴일 판단은 한국천문연구원 특일 정보를 사용합니다.
- 외출 계획은 한국관광공사 반려동물 동반여행 정보와 기상청 단기예보를 함께 사용합니다.
- 외부 API 실패 시 가능한 범위의 결과와 `source_warnings_ko`를 함께 반환합니다.
- 개인 보호자 정보, 동물등록번호, RFID 정보는 요구하거나 저장하지 않습니다.

## 설정

배포에 필요한 환경변수 이름은 `.env.example`을 참고합니다. 실제 API 키 값은 코드나 Git 저장소에 커밋하지 않습니다.

## 로컬 실행

```bash
python -m pip install -e .
python -m mypet_life_mcp.server
```

기본 실행은 stdio MCP 서버입니다.

컨테이너 배포 시에는 Dockerfile 설정에 따라 HTTP MCP 서버로 실행됩니다. FastMCP streamable HTTP 경로는 `/mcp`입니다.

## 테스트

외부 API 없이 mock 응답으로 실행되는 단위 테스트:

```bash
python -m unittest
```

실제 `.env` 키로 기능을 확인하는 smoke test:

```bash
python scripts/local_smoke.py
```

실제 MCP 프로토콜로 도구 목록과 도구 호출을 확인하는 smoke test:

```bash
python scripts/mcp_smoke.py
```

## PlayMCP in KC 배포

이 저장소는 PlayMCP in KC의 Git 소스 빌드 방식으로 배포할 수 있도록 `Dockerfile`을 포함합니다.

등록 예시:

```text
MCP 서버 이름: mypet-life-mcp
설명: 반려동물 보호자를 위한 위치 기반 공공데이터 MCP 서버
Git URL: https://github.com/sikk806/KKO.git
브랜치 / ref: main
Dockerfile 경로: Dockerfile
```

PlayMCP in KC 환경변수에는 `.env.example`에 있는 값들을 등록합니다. 실제 키 값은 GitHub에 올리지 않습니다.

컨테이너 실행에 필요한 기본값은 Dockerfile에 설정되어 있습니다.

서버가 Active 상태가 되면 Endpoint URL을 복사해 PlayMCP에 등록합니다. 경로를 직접 지정해야 하는 경우 `/mcp`를 사용합니다.

## 데이터 출처

- [행정안전부_동물_동물병원 조회서비스](https://www.data.go.kr/data/15154952/openapi.do)
- [행정안전부_동물_동물약국 조회서비스](https://www.data.go.kr/data/15155272/openapi.do)
- [행정안전부_동물_동물위탁관리업 조회서비스](https://www.data.go.kr/data/15155055/openapi.do)
- [행정안전부_동물_동물미용업 조회서비스](https://www.data.go.kr/data/15154944/openapi.do)
- [행정안전부_동물_동물운송업 조회서비스](https://www.data.go.kr/data/15155024/openapi.do)
- [행정안전부_동물_동물장묘업 조회서비스](https://www.data.go.kr/data/15155065/openapi.do)
- [한국관광공사_반려동물_동반여행_서비스](https://www.data.go.kr/data/15135102/openapi.do)
- [기상청_단기예보 조회서비스](https://www.data.go.kr/data/15084084/openapi.do)
- [한국천문연구원_특일 정보](https://www.data.go.kr/data/15012690/openapi.do)
- [카카오 Local API](https://developers.kakao.com/docs/latest/ko/local/dev-guide)

## 안전 제한

이 서비스는 다음을 하지 않습니다.

- 동물을 진단하거나 약을 처방하지 않습니다.
- 응급 치료 가능 여부를 보장하지 않습니다.
- 병원, 약국, 장소가 현재 운영 중이라고 보장하지 않습니다.
- 반려동물 동반 입장을 보장하지 않습니다.
- 보호자 개인정보, 동물등록번호, RFID 정보를 요구하거나 저장하지 않습니다.

응답에는 `후보`, `전화 확인 필요`, `인허가 정보 기준`, `지도/공공데이터 기준`, `방문 전 확인 권장`과 같은 신중한 표현을 사용합니다.
