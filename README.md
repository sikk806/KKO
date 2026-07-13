# MyPet Life MCP

MyPet Life MCP는 반려동물 보호자가 외출, 여행, 야간/휴일 상황, 업체 확인, 음식 섭취 관련 질문을 할 때 공공/공식 데이터 기반의 후보와 근거를 정리해 주는 PlayMCP-ready MCP 서버입니다.

이 서버는 진단, 처방, 응급 진료 가능 여부, 영업 중 여부, 반려동물 동반 입장을 보장하지 않습니다. 결과는 항상 후보와 참고 근거이며, 방문 전 전화 확인이 필요합니다.

## MCP Tools

- `find_pet_emergency_candidates`: 휴일, 야간, 주말 상황에서 동물병원/동물약국 연락 후보를 정리합니다.
- `make_pet_care_map`: 외출/여행 위치 주변의 동물병원/동물약국 후보를 정리합니다.
- `make_pet_outing_plan`: 반려동물 동반 여행/외출 장소, 날씨, 주변 케어 후보를 묶어 외출 계획을 만듭니다.
- `verify_pet_business`: 반려동물 호텔, 미용, 운송, 장묘 등 업체의 인허가 후보를 확인합니다.
- `check_pet_food_safety`: 반려견/반려묘가 음식, 제품, 원재료를 먹었거나 먹어도 되는지 물었을 때 원재료와 공개 레퍼런스 기준으로 안내합니다.

## External API Keys

| API | 실제 사용 | 역할 | `.env` 이름 |
| --- | --- | --- | --- |
| 공공데이터포털 OpenAPI | 사용 | 병원, 약국, 인허가 등 공공데이터 조회 | `DATA_GO_KR_SERVICE_KEY` |
| 한국관광공사 TourAPI | 사용 | 반려동물 동반 여행/외출 후보 조회 | `KTO_SERVICE_KEY` |
| 식품안전나라 OpenAPI C002 | 사용 | 식품/제품 원재료 조회 | `FOOD_SAFETY_KOREA_API_KEY` |
| 식품안전나라 OpenAPI I2520 | 사용 | 원재료명, 영문명, 이명 정규화 | `FOOD_SAFETY_KOREA_API_KEY` |
| 기상청 단기예보 | 선택 사용 | 외출 계획의 날씨 참고 | `KMA_SERVICE_KEY` |
| 한국천문연구원 특일 정보 | 선택 사용 | 휴일/특일 참고 | `KASI_SERVICE_KEY` |

별도 화학물질 DB API와 Kakao Map API는 현재 사용하지 않습니다.

## API 발급 및 문서

- 식품안전나라 OpenAPI: [식품안전나라 데이터활용서비스](https://www.foodsafetykorea.go.kr/apiMain.do)
- 식품안전나라 OpenAPI 이용 방법: [OpenAPI 사용 안내](https://www.foodsafetykorea.go.kr/api/howToUseApi.do?menu_grp=MENU_GRP34&menu_no=687)
- 공공데이터포털: [https://www.data.go.kr](https://www.data.go.kr)
- 한국관광공사 TourAPI: [https://api.visitkorea.or.kr](https://api.visitkorea.or.kr)

음식 안전 레퍼런스는 API가 아니라 코드에 포함된 공개 근거 맵입니다.

- ASPCA People Foods to Avoid Feeding Your Pets: [ASPCA](https://www.aspca.org/pet-care/aspca-poison-control/people-foods-avoid-feeding-your-pets)
- FDA Paws Off Xylitol: [FDA](https://www.fda.gov/animal-veterinary/animal-health-literacy/paws-xylitol-its-dangerous-dogs)
- Merck Veterinary Manual Grape/Raisin/Tamarind Toxicosis: [Merck Vet Manual](https://www.merckvetmanual.com/toxicology/food-hazards/grape-raisin-and-tamarind-vitis-spp-tamarindus-spp-toxicosis-in-dogs)

## Environment

`.env.example`의 형태는 다음과 같습니다.

```env
DATA_GO_KR_SERVICE_KEY=
KTO_SERVICE_KEY=
KMA_SERVICE_KEY=
KASI_SERVICE_KEY=

FOOD_SAFETY_KOREA_API_KEY=
```

실제 `.env` 파일과 실제 API Key 값은 Git에 올리지 않습니다.

## Local Run

```bash
python -m pip install -e .
python -m mypet_life_mcp.server
```

기본 실행은 stdio MCP 서버입니다. 컨테이너/PlayMCP 배포에서는 `MCP_TRANSPORT=streamable-http`로 실행하며 MCP 경로는 `/mcp`입니다.

## Tests

외부 API는 unit test에서 직접 호출하지 않고 fake client와 fixture를 사용합니다.

```bash
python -m unittest
```

MCP protocol smoke test:

```bash
python scripts/mcp_smoke.py
```

음식 안전 live log:

```bash
python scripts/live_food_safety_mcp_log.py
```

## Food Safety Tool Flow

`check_pet_food_safety`는 다음 순서로 동작합니다.

1. `food`, `pet_type`, `weight_kg`, `amount_gram` 입력을 검증합니다.
2. 식품안전나라 C002로 제품/식품 원재료 후보를 조회합니다.
3. C002 결과가 없으면 입력값 자체를 원재료 후보로 사용합니다.
4. 식품안전나라 I2520으로 원재료명, 영문명, 이명, 학명을 정규화합니다.
5. 정규화된 원재료와 입력 음식명을 공개 레퍼런스 맵과 매칭합니다.
6. 결과를 `SPECIES_REFERENCE_FOUND`, `GENERAL_REFERENCE_FOUND`, `NO_REFERENCE_FOUND` 같은 근거 상태로 반환합니다.

이 도구는 `safe: true`, `risk: TOXIC` 같은 확정 판정을 만들지 않습니다. 근거가 없다는 뜻은 안전하다는 뜻이 아닙니다.

## Safety Limits

- 동물을 진단하거나 약을 처방하지 않습니다.
- 병원/약국이 지금 진료 또는 영업 중이라고 보장하지 않습니다.
- 반려동물 동반 입장 가능 여부를 보장하지 않습니다.
- 인허가 정보가 확인되어도 업체가 안전하거나 신뢰할 수 있다고 말하지 않습니다.
- 보호자 개인정보, 동물등록번호, RFID 정보를 요구하거나 저장하지 않습니다.
- 음식 안전성 도구는 공개 레퍼런스 기준의 후보 안내만 제공합니다.

## PlayMCP in KC

Git 소스 빌드로 등록할 때는 다음 값을 사용합니다.

```text
MCP 서버 이름: mypet-life-mcp
설명: 반려동물 보호자를 위한 공공/공식 데이터 기반 생활 지원 MCP 서버
Git URL: https://github.com/sikk806/KKO.git
브랜치 / ref: main
Dockerfile 경로: Dockerfile
container_port: 8000
MCP Endpoint: /mcp
인증 방식: 인증 사용하지 않음
```
