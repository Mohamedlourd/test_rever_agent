"""
customer_tools.py — Tools de clientes y ecommerce

get_customer_profile        → perfil del cliente con fraud score
get_customer_return_history → historial de devoluciones anteriores
get_order_details           → datos del pedido y producto
get_ecommerce_status        → estado operativo del ecommerce cliente
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from objects.customer import get_customer, CUSTOMERS
from objects.product  import get_product, PRODUCTS


def get_customer_profile(customer_id: str) -> str:
    """
    Devuelve el perfil del cliente: fraud score, flags,
    tasa de devoluciones y elegibilidad de reembolso instantáneo.
    """
    customer = get_customer(customer_id)
    if not customer:
        return json.dumps({"error": f"Cliente '{customer_id}' no encontrado", "available": list(CUSTOMERS.keys())})
    return json.dumps(customer.get_profile(), ensure_ascii=False, indent=2)


def get_customer_return_history(customer_id: str) -> str:
    """
    Devuelve el historial completo de devoluciones del cliente:
    patrones, motivos, resoluciones y si hubo problemas en workflows pasados.
    """
    customer = get_customer(customer_id)
    if not customer:
        return json.dumps({"error": f"Cliente '{customer_id}' no encontrado"})
    return json.dumps(customer.get_return_history(), ensure_ascii=False, indent=2)


def get_order_details(order_id: str, product_id: str) -> str:
    """
    Devuelve los datos del pedido y el producto:
    valor total, método de pago, peso y si es retornable.
    """
    product = get_product(product_id)
    if not product:
        return json.dumps({"error": f"Producto '{product_id}' no encontrado", "available": list(PRODUCTS.keys())})

    data = {
        "order_id":          order_id,
        "ecommerce_id":      product.ecommerce_id,
        "status":            "FULFILLED",
        "purchased_at":      "2024-03-01T10:00:00Z",
        "days_since_purchase": 20,
        "currency":          "EUR",
        "total_value_eur":   product.total_value_eur,
        "product":           product.get_details(),
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def get_ecommerce_status(ecommerce_id: str) -> str:
    """
    Devuelve el estado operativo del sistema del ecommerce cliente:
    si su API está respondiendo y su latencia media.
    """
    data = {
        "ecommerce_id":              ecommerce_id,
        "api_status":                "OPERATIONAL",
        "last_successful_call_at":   "2024-03-21T10:04:00Z",
        "avg_response_time_ms":      230,
        "recent_errors":             [],
        "maintenance_window":        None,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


# ── Schemas ────────────────────────────────────────────────────────────────────

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_customer_profile",
            "description": "Devuelve el perfil del cliente con fraud score, flags y elegibilidad de reembolso instantáneo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "ID del cliente (ej: 'CUST-001')"}
                },
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_return_history",
            "description": "Devuelve el historial completo de devoluciones anteriores del cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "ID del cliente"}
                },
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "Devuelve los datos del pedido y el producto: valor, peso y si es retornable.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id":   {"type": "string", "description": "ID interno del pedido"},
                    "product_id": {"type": "string", "description": "ID del producto (ej: 'PROD-001')"},
                },
                "required": ["order_id", "product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ecommerce_status",
            "description": "Devuelve el estado operativo del sistema del ecommerce cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ecommerce_id": {"type": "string", "description": "ID del ecommerce (ej: 'adidas_es')"}
                },
                "required": ["ecommerce_id"],
            },
        },
    },
]

TOOLS_MAP = {
    "get_customer_profile":        get_customer_profile,
    "get_customer_return_history": get_customer_return_history,
    "get_order_details":           get_order_details,
    "get_ecommerce_status":        get_ecommerce_status,
}