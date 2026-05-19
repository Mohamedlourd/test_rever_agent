"""
Carrier — clase con datos hardcodeados y getters
  - DHL: degradado, con incidencia activa
  - UPS: operativo, disponible como alternativa
"""


class Carrier:
    def __init__(
        self,
        carrier_id: str,
        status: str,
        incidents: list[dict],
        last_successful_request_at: str,
        api_latency_ms_avg: int,
    ):
        self.carrier_id                 = carrier_id
        self.status                     = status
        self.incidents                  = incidents
        self.last_successful_request_at = last_successful_request_at
        self.api_latency_ms_avg         = api_latency_ms_avg

    def get_status(self) -> dict:
        return {
            "carrier":                      self.carrier_id,
            "status":                       self.status,
            "incidents":                    self.incidents,
            "last_successful_request_at":   self.last_successful_request_at,
            "api_latency_ms_avg":           self.api_latency_ms_avg,
        }

    def is_operational(self) -> bool:
        return self.status == "OPERATIONAL"


class CarrierAvailability:
    """Carriers disponibles para una combinación país + peso."""
    def __init__(
        self,
        country: str,
        weight_class: str,
        available: list[dict],
        unavailable: list[dict],
    ):
        self.country       = country
        self.weight_class  = weight_class
        self.available     = available
        self.unavailable   = unavailable

    def get_options(self) -> dict:
        return {
            "country":              self.country,
            "weight_class":         self.weight_class,
            "available_carriers":   self.available,
            "unavailable_carriers": self.unavailable,
        }


# Datos hardcodeados

DHL = Carrier(
    carrier_id  = "DHL",
    status      = "DEGRADED",
    incidents   = [
        {
            "id":                  "INC-DHL-2024-0321",
            "title":               "API de generación de etiquetas intermitente",
            "severity":            "HIGH",
            "started_at":          "2024-03-21T09:30:00Z",
            "estimated_resolution":"2024-03-21T14:00:00Z",
            "affected_services":   ["label_generation", "shipment_creation"],
            "affected_countries":  ["US", "CA", "ES"],
        }
    ],
    last_successful_request_at = "2024-03-21T09:28:00Z",
    api_latency_ms_avg         = 8500,
)

UPS = Carrier(
    carrier_id  = "UPS",
    status      = "OPERATIONAL",
    incidents   = [],
    last_successful_request_at = "2024-03-21T10:06:00Z",
    api_latency_ms_avg         = 210,
)

# Disponibilidad US paquete ligero (<1kg)
AVAILABILITY_US_LIGHT = CarrierAvailability(
    country      = "US",
    weight_class = "light",
    available    = [
        {"carrier": "UPS",   "status": "OPERATIONAL", "estimated_cost_eur": 8.50, "estimated_days": 5, "supports_home_pickup": True},
        {"carrier": "FEDEX", "status": "OPERATIONAL", "estimated_cost_eur": 9.20, "estimated_days": 4, "supports_home_pickup": True},
    ],
    unavailable  = [
        {"carrier": "DHL", "reason": "API_DEGRADED"},
    ],
)

# Disponibilidad ES paquete pesado (>=1kg)
AVAILABILITY_ES_HEAVY = CarrierAvailability(
    country      = "ES",
    weight_class = "heavy",
    available    = [
        {"carrier": "SEUR",            "status": "OPERATIONAL", "estimated_cost_eur": 5.90, "estimated_days": 2, "supports_home_pickup": True},
        {"carrier": "CORREOS_EXPRESS", "status": "OPERATIONAL", "estimated_cost_eur": 4.50, "estimated_days": 3, "supports_home_pickup": False},
    ],
    unavailable  = [],
)


# ── Registros ──────────────────────────────────────────────────────────────────

CARRIERS: dict[str, Carrier] = {
    "DHL": DHL,
    "UPS": UPS,
}

AVAILABILITIES: dict[tuple, CarrierAvailability] = {
    ("US", "light"): AVAILABILITY_US_LIGHT,
    ("ES", "heavy"): AVAILABILITY_ES_HEAVY,
}


def get_carrier(carrier_id: str) -> Carrier | None:
    return CARRIERS.get(carrier_id.upper())


def get_availability(country: str, weight_class: str) -> CarrierAvailability | None:
    return AVAILABILITIES.get((country.upper(), weight_class.lower()))