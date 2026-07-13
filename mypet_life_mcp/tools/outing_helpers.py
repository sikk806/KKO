from __future__ import annotations


def compact_weather(items: list[dict]) -> dict:
    if not items:
        return {"rain_probability": 0, "precipitation_mm": 0}
    item = items[0]
    if "rain_probability" in item:
        return item
    return {"rain_probability": item.get("pop", 0), "precipitation_mm": item.get("pcp", 0), "temperature_c": item.get("tmp")}


def filter_items_by_region(items: list[dict], location_text: str) -> list[dict]:
    province = location_text.split(" ", 1)[0]
    filtered = []
    for item in items:
        address = str(item.get("addr1") or item.get("address") or "")
        if location_text in address or province in address:
            filtered.append(item)
    return filtered


def filter_items_by_intent(items: list[dict], intent: str | None, allowed_types: dict[str, set[str]]) -> list[dict]:
    allowed = allowed_types.get(intent or "")
    if not allowed:
        return items
    return [item for item in items if str(item.get("contenttypeid") or "") in allowed]


def dedupe_items(items: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for item in items:
        if not isinstance(item, dict):
            continue
        key = item.get("contentid") or item.get("title") or str(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped
