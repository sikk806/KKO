"""External API adapters."""

from .animal_hospital import AnimalHospitalClient
from .animal_pharmacy import AnimalPharmacyClient
from .food_safety_korea import FoodSafetyKoreaClient
from .holiday import HolidayClient
from .pet_business_license import PetBusinessLicenseClient
from .pet_friendly import PetFriendlyPlaceClient
from .weather import WeatherClient

__all__ = [
    "AnimalHospitalClient",
    "AnimalPharmacyClient",
    "FoodSafetyKoreaClient",
    "HolidayClient",
    "PetBusinessLicenseClient",
    "PetFriendlyPlaceClient",
    "WeatherClient",
]
