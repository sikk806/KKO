from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlencode
from urllib.request import Request, urlopen

from mypet_life_mcp.core.korean import setup_error_ko
from mypet_life_mcp.core.schemas import SourceResult

logger = logging.getLogger("mypet_life_mcp")

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()


class MissingApiKeyError(RuntimeError):
    def __init__(self, service_name: str, env_var: str):
        self.service_name = service_name
        self.env_var = env_var
        super().__init__(setup_error_ko(service_name, env_var))


@dataclass(frozen=True)
class ApiSettings:
    timeout_seconds: float = 5.0
    retries: int = 2
    backoff_seconds: float = 0.25


class BaseApiClient:
    service_name = "공공데이터"
    required_env = "DATA_GO_KR_SERVICE_KEY"

    def __init__(self, api_key: str | None = None, settings: ApiSettings | None = None):
        self.api_key = api_key
        self.settings = settings or ApiSettings()

    def get_key(self, *env_names: str) -> str:
        if self.api_key:
            return self.api_key
        for env_name in env_names or (self.required_env,):
            value = os.getenv(env_name)
            if value:
                return normalize_service_key(value)
        raise MissingApiKeyError(self.service_name, env_names[0] if env_names else self.required_env)

    def source_error(self, exc: Exception) -> SourceResult:
        logger.warning("source failed", extra={"service": self.service_name, "error": str(exc)})
        return SourceResult(items=[], source=self.service_name, ok=False, error_ko=str(exc))

    def get_json(self, url: str, params: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
        query = urlencode({key: value for key, value in params.items() if value is not None})
        full_url = f"{url}?{query}" if query else url
        last_error: Exception | None = None
        for attempt in range(self.settings.retries + 1):
            try:
                request = Request(full_url, headers=headers or {})
                with urlopen(request, timeout=self.settings.timeout_seconds) as response:
                    payload = response.read().decode("utf-8")
                return json.loads(payload)
            except HTTPError as exc:
                last_error = RuntimeError(self._http_error_message(exc))
                if attempt < self.settings.retries:
                    time.sleep(self.settings.backoff_seconds * (2**attempt))
            except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt < self.settings.retries:
                    time.sleep(self.settings.backoff_seconds * (2**attempt))
        if isinstance(last_error, RuntimeError):
            raise last_error
        raise RuntimeError(f"{self.service_name} 조회에 실패했습니다. 잠시 후 다시 시도해 주세요.") from last_error

    def _http_error_message(self, exc: HTTPError) -> str:
        body = exc.read().decode("utf-8", errors="replace")
        detail = ""
        try:
            parsed = json.loads(body)
            detail = parsed.get("message") or parsed.get("error") or parsed.get("error_description") or ""
        except json.JSONDecodeError:
            detail = body[:160]
        if detail:
            return f"{self.service_name} 조회가 거절되었습니다. 상태 코드: {exc.code}. 확인 내용: {detail}"
        return f"{self.service_name} 조회가 거절되었습니다. 상태 코드: {exc.code}."


def first_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return ""


def data_go_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    body = payload.get("response", {}).get("body", {})
    items = body.get("items", {}).get("item", [])
    if isinstance(items, dict):
        return [items]
    if isinstance(items, list):
        return items
    return []


def contains_region(item: dict[str, Any], region: str | None) -> bool:
    if not region:
        return True
    needle = region.replace(" ", "")
    haystack = " ".join(str(value or "") for value in item.values()).replace(" ", "")
    return needle in haystack


def normalize_service_key(value: str) -> str:
    stripped = value.strip()
    if "%" in stripped:
        return unquote(stripped)
    return stripped
