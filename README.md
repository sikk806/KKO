# MyPet Life / 마이펫 라이프 MCP

마이펫 라이프는 반려동물 보호자가 외출, 여행, 휴일, 야간 상황에서 참고할 수 있는 공공데이터 기반 후보를 정리하는 PlayMCP-ready 원격 MCP 서버입니다.

이 서비스는 진단, 처방, 영업 중 보장, 응급 진료 보장을 하지 않습니다. 모든 결과는 후보이며, 방문 전 전화 확인이 필요합니다.

## 제공 도구

- `find_pet_emergency_candidates`: 휴일/야간/주말 가능성이 있는 상황에서 동물병원과 동물약국 연락 후보를 정리합니다.
- `make_pet_care_map`: 외출 또는 여행 위치 주변의 동물병원/동물약국 후보 지도를 만듭니다.
- `make_pet_outing_plan`: 반려동물 동반 장소, 날씨, 주변 돌봄 연락처를 묶어 외출 계획을 제안합니다.
- `verify_pet_business`: 반려동물 호텔, 미용, 운송, 장묘 등 업체가 공식 인허가 후보에 나타나는지 확인합니다.

## 설치

```bash
pip install -e .
```

Python이 여러 개 설치된 Windows 환경에서는 사용하는 Python 실행 파일로 다음처럼 실행할 수 있습니다.

```bash
python -m pip install -e .
```

## 환경 변수

`.env.example`을 참고해 배포 환경에 다음 값을 설정합니다. API 키를 코드에 직접 넣지 마세요.

```bash
KAKAO_REST_API_KEY=
DATA_GO_KR_SERVICE_KEY=
KTO_SERVICE_KEY=
KMA_SERVICE_KEY=
KASI_SERVICE_KEY=
```

여러 공공데이터 API가 같은 서비스 키를 사용할 수 있으면 `DATA_GO_KR_SERVICE_KEY`를 fallback으로 사용합니다.

## 로컬 실행

```bash
mypet-life-mcp
```

또는:

```bash
python -m mypet_life_mcp.server
```

## 테스트

테스트는 라이브 API 키 없이 목 응답으로 실행됩니다.

```bash
python -m unittest
```

## 예시 호출

```json
{
  "tool": "find_pet_emergency_candidates",
  "arguments": {
    "location": "서울 강남역",
    "pet_type": "강아지",
    "situation": "구토",
    "radius_km": 5,
    "when": "2026-07-05T22:00:00+09:00"
  }
}
```

카카오 로컬 API 승인이 없더라도, 호출 환경이 사용자의 현재 위치 좌표를 제공할 수 있으면 `latitude`와 `longitude`를 함께 넘겨 거리 계산을 사용할 수 있습니다. 좌표는 저장하지 않고 해당 요청 처리에만 사용합니다.

```json
{
  "tool": "make_pet_care_map",
  "arguments": {
    "location": "현재 위치",
    "latitude": 37.4979,
    "longitude": 127.0276,
    "radius_km": 5
  }
}
```

예시 응답 일부:

```json
{
  "mode": "holiday_or_night_candidates",
  "summary_ko": "서울 강남역 기준 휴일/야간/주말 가능성이 있는 시간대로 판단되어 먼저 연락할 후보를 정리했습니다. 실제 접수 가능 여부는 전화 확인이 필요합니다.",
  "call_script_ko": "안녕하세요. 강아지 때문에 문의드립니다. 현재 구토 상태인데 지금 진료 또는 상담 접수가 가능한가요? 접수 마감 시간, 대기 시간, 준비해서 가야 할 내용을 알려주실 수 있을까요?",
  "safety_note_ko": "이 결과는 진단이나 처방이 아니며, 응급 진료 가능 여부를 보장하지 않습니다. 상태가 급하거나 악화되면 즉시 가까운 동물병원에 전화하거나 이동해 주세요."
}
```

## 데이터 출처 메모

- [카카오 로컬 API](https://developers.kakao.com/docs/latest/ko/local/dev-guide): 주소 검색과 키워드 검색으로 위치 확인 및 지도 후보 보조 확인에 사용합니다.
- [공공데이터포털](https://www.data.go.kr/): 동물병원, 동물약국, 반려동물 관련 영업 인허가 후보 확인에 사용합니다. MVP는 지자체별 파일이 아니라 행정안전부 지방행정 인허가정보 전국 통합 조회서비스를 사용합니다.
  - [행정안전부_동물_동물병원 조회서비스](https://www.data.go.kr/data/15154952/openapi.do)
  - [행정안전부_동물_동물약국 조회서비스](https://www.data.go.kr/data/15155272/openapi.do)
  - [행정안전부_동물_동물위탁관리업 조회서비스](https://www.data.go.kr/data/15155055/openapi.do)
  - [행정안전부_동물_동물미용업 조회서비스](https://www.data.go.kr/data/15154944/openapi.do)
  - [행정안전부_동물_동물운송업 조회서비스](https://www.data.go.kr/data/15155024/openapi.do)
  - [행정안전부_동물_동물장묘업 조회서비스](https://www.data.go.kr/data/15155065/openapi.do)
- [한국관광공사_반려동물_동반여행_서비스](https://www.data.go.kr/data/15135102/openapi.do): 반려동물 동반 여행 정보 기반 외출 장소 후보 확인에 사용합니다.
- [기상청_단기예보 조회서비스](https://www.data.go.kr/data/15084084/openapi.do): 외출 점수 계산에 사용합니다.
- [한국천문연구원_특일 정보](https://www.data.go.kr/data/15012690/openapi.do): 공휴일 판단에 사용합니다.

기관별 API 엔드포인트와 응답 필드는 변경될 수 있으므로, 실제 배포 전 사용하는 데이터셋의 최신 문서를 확인하고 `mypet_life_mcp/clients` 안의 상수와 파서를 조정하세요.

## PlayMCP 배포 메모

- MCP 서버 엔트리포인트는 `mypet_life_mcp.server:create_app`입니다.
- 네 개 도구는 모두 구조화 JSON과 한국어 사용자 문구를 함께 반환합니다.
- 원격 배포 환경에는 API 키를 환경 변수로 주입하세요.
- 외부 API 실패 시 가능한 섹션은 유지하고 `source_warnings_ko`에 한국어 경고를 담습니다.

## 제한 사항

- 동물 진단이나 처방을 제공하지 않습니다.
- 병원, 약국, 장소가 지금 이용 가능하다고 보장하지 않습니다.
- 반려동물 동반 가능 여부를 확정하지 않습니다.
- 인허가 확인은 서비스 품질이나 안전을 보장하지 않습니다.
- 보호자 이름, 연락처, 생년월일, 동물등록번호, RFID 등 개인정보성 입력을 요구하지 않습니다.
- 검색 위치 외 민감한 사용자 데이터를 저장하지 않습니다.
