"""External API adapters."""

from .animal_hospital import AnimalHospitalClient
from .animal_pharmacy import AnimalPharmacyClient
from .holiday import HolidayClient
from .kakao_local import KakaoLocalClient
from .pet_business_license import PetBusinessLicenseClient
from .pet_friendly import PetFriendlyPlaceClient
from .weather import WeatherClient

__all__ = [
    "AnimalHospitalClient",
    "AnimalPharmacyClient",
    "HolidayClient",
    "KakaoLocalClient",
    "PetBusinessLicenseClient",
    "PetFriendlyPlaceClient",
    "WeatherClient",
]
