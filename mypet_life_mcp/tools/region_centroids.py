from __future__ import annotations

from mypet_life_mcp.tools.data_files import load_data_json


REGION_CENTROIDS = {key: tuple(value) for key, value in load_data_json("region_centroids.json").items()}
