from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any


@lru_cache(maxsize=None)
def load_data_json(name: str) -> Any:
    path = files("mypet_life_mcp.data").joinpath(name)
    return json.loads(path.read_text(encoding="utf-8"))
