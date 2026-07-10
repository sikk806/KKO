from __future__ import annotations

FORBIDDEN_USER_PHRASES = [
    "Here are",
    "available now",
    "open now",
    "guaranteed",
    "safe business",
]


def setup_error_ko(service_name: str, env_var: str) -> str:
    return (
        f"{service_name} 조회에 필요한 {env_var} 환경 변수가 설정되지 않았습니다. "
        "실시간 공공데이터 조회 없이 결과를 확정하지 않도록 요청을 중단했습니다."
    )


def safety_note_ko() -> str:
    return (
        "이 결과는 진단이나 처방이 아니며, 응급 진료 가능 여부를 보장하지 않습니다. "
        "상태가 급하거나 악화되면 즉시 가까운 동물병원에 전화하거나 이동해 주세요."
    )


def confirmation_note_ko() -> str:
    return "지도/공공데이터 기준 후보이며, 방문 전 전화 확인이 필요합니다."


def assert_user_text_is_safe(value: str) -> None:
    for phrase in FORBIDDEN_USER_PHRASES:
        if phrase.lower() in value.lower():
            raise AssertionError(f"금지된 사용자 문구가 포함되었습니다: {phrase}")
