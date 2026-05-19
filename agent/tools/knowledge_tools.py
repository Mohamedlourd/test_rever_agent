"""
knowledge_tools.py — Tools de la knowledge base interna de REVER

get_workflow_step_definition  → definición del step
get_step_error_definitions    → errores posibles y acciones recomendadas
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from objects.knowledge_base import get_step_definition, get_error_definition, STEP_DEFINITIONS


def get_workflow_step_definition(step_id: str) -> str:
    """
    Devuelve la definición del step: qué hace, qué sistemas toca,
    si es crítico, si tiene alternativa y cuántos intentos se recomiendan.
    """
    step = get_step_definition(step_id)
    if not step:
        available = list(STEP_DEFINITIONS.keys())
        return json.dumps({"error": f"Step '{step_id}' no encontrado", "available_steps": available})
    return json.dumps(step.get_definition(), ensure_ascii=False, indent=2)


def get_step_error_definitions(step_id: str) -> str:
    """
    Devuelve todos los errores posibles de un step con su causa probable
    y la acción recomendada (RETRY, RETRY_LATER, SKIP, ESCALATE).
    """
    errors = get_error_definition(step_id)
    if not errors:
        return json.dumps({"error": f"No hay definiciones de error para el step '{step_id}'"})
    return json.dumps(errors.get_errors(), ensure_ascii=False, indent=2)


# ── Schemas ────────────────────────────────────────────────────────────────────

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_workflow_step_definition",
            "description": "Devuelve la definición del step: qué hace, qué sistemas toca y si tiene alternativa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "step_id": {"type": "string", "description": "ID del step (ej: 'STEP_3_GENERATE_LABEL')"}
                },
                "required": ["step_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_step_error_definitions",
            "description": "Devuelve todos los errores posibles de un step con su acción recomendada.",
            "parameters": {
                "type": "object",
                "properties": {
                    "step_id": {"type": "string", "description": "ID del step"}
                },
                "required": ["step_id"],
            },
        },
    },
]

TOOLS_MAP = {
    "get_workflow_step_definition": get_workflow_step_definition,
    "get_step_error_definitions":   get_step_error_definitions,
}