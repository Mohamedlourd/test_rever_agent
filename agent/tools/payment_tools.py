"""
payment_tools.py — Tools de pagos y reembolsos

get_payment_status → estado de la transacción original
get_refund_status  → si ya se emitió reembolso instantáneo
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from objects.workflow import get_workflow, WORKFLOWS


def get_payment_status(workflow_id: str) -> str:
    """
    Devuelve el estado de la transacción de pago original:
    si sigue activa, si es reversible y días hasta expiración.
    Crítico para saber si el reembolso es técnicamente posible.
    """
    wf = get_workflow(workflow_id)
    if not wf:
        return json.dumps({"error": f"Workflow '{workflow_id}' no encontrado", "available": list(WORKFLOWS.keys())})
    return json.dumps(wf.get_payment(), ensure_ascii=False, indent=2)


def get_refund_status(workflow_id: str) -> str:
    """
    Devuelve si ya se emitió un reembolso instantáneo en este workflow:
    cuándo, cuánto y si es reversible.
    Fundamental antes de tomar cualquier decisión que involucre dinero.
    """
    wf = get_workflow(workflow_id)
    if not wf:
        return json.dumps({"error": f"Workflow '{workflow_id}' no encontrado"})
    return json.dumps(wf.get_refund(), ensure_ascii=False, indent=2)


# ── Schemas ────────────────────────────────────────────────────────────────────

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_payment_status",
            "description": "Devuelve el estado de la transacción de pago original: si es reversible y días hasta expiración.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string", "description": "ID del workflow"}
                },
                "required": ["workflow_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_refund_status",
            "description": "Devuelve si ya se emitió un reembolso instantáneo en este workflow y si es reversible.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string", "description": "ID del workflow"}
                },
                "required": ["workflow_id"],
            },
        },
    },
]

TOOLS_MAP = {
    "get_payment_status": get_payment_status,
    "get_refund_status":  get_refund_status,
}