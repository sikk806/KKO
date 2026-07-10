from __future__ import annotations

import re


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = value.lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^\w가-힣]", "", text)
    return text


def normalize_address(value: str | None) -> str:
    text = normalize_text(value)
    for suffix in ("대한민국", "kr"):
        text = text.replace(suffix, "")
    return text


def similarity(a: str, b: str) -> float:
    left = set(normalize_text(a))
    right = set(normalize_text(b))
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)
