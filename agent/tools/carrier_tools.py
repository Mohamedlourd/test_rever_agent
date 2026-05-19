"""
carrier_tools.py — Tools que simulan las APIs de carriers logísticos

get_carrier_status       → estado operativo del carrier
get_available_carriers   → alternativas disponibles para país + peso
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from objects.carrier import get_carrier, get_availability, CARRIERS


def get_carrier_status(carrier: str) -> str:
    """
    Devuelve el estado operativo actual del carrier:
    si está caído, degradado, incidencias activas y latencia media.
    """
    data = get_carrier(carrier)
    if not data:
        return json.dumps({"error": f"Carrier '{carrier}' no encontrado", "available": list(CARRIERS.keys())})
    return json.dumps(data.get_status(), ensure_ascii=False, indent=2)


def get_available_carriers(country: str, weight_class: str = "light") -> str:
    """
    Devuelve los carriers alternativos disponibles para un país y peso.
    weight_class: 'light' (<1kg) o 'heavy' (>=1kg)
    """
    data = get_availability(country, weight_class)
    if not data:
        return json.dumps({
            "error": f"Sin datos para country='{country}', weight_class='{weight_class}'",
            "hint": "Prueba con country='US' y weight_class='light', o country='ES' y weight_class='heavy'",
        })
    return json.dumps(data.get_options(), ensure_ascii=False, indent=2)


# ── Schemas ────────────────────────────────────────────────────────────────────

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_carrier_status",
            "description": "Devuelve el estado operativo del carrier: si está caído, degradado o con incidencias activas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "carrier": {"type": "string", "description": "Nombre del carrier (ej: 'DHL', 'UPS')"}
                },
                "required": ["carrier"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_carriers",
            "description": "Devuelve carriers alternativos disponibles para un país y clase de peso.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country":      {"type": "string", "description": "Código de país (ej: 'US', 'ES')"},
                    "weight_class": {"type": "string", "enum": ["light", "heavy"], "description": "'light' para <1kg, 'heavy' para >=1kg"},
                },
                "required": ["country"],
            },
        },
    },
]

TOOLS_MAP = {
    "get_carrier_status":      get_carrier_status,
    "get_available_carriers":  get_available_carriers,
}