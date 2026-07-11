from __future__ import annotations

from .region_aliases import PROVINCE_ALIASES
from .region_centroids import REGION_CENTROIDS
from .region_sigungu_metro import SIGUNGU_BY_METRO
from .region_sigungu_province import SIGUNGU_BY_PROVINCE_AREA

SIGUNGU_SUFFIXES = ("시", "군", "구")

SIGUNGU_BY_PROVINCE = {**SIGUNGU_BY_METRO, **SIGUNGU_BY_PROVINCE_AREA}
