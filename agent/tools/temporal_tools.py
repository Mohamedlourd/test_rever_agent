"""
temporal_tools.py — Tools que simulan las APIs del cliente de Temporal

get_workflow_execution_state  → DescribeWorkflowExecution
get_workflow_history          → GetWorkflowHistory
get_workflow_current_step     → QueryWorkflow("current_state")
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from objects.workflow import get_workflow


def get_workflow_execution_state(workflow_id: str) -> str:
    """
    Devuelve el estado vivo del workflow: actividad pendiente,
    número de intentos, último error exacto, señales pendientes.
    Equivale a: temporalClient.DescribeWorkflowExecution()
    """
    wf = get_workflow(workflow_id)
    if not wf:
        return json.dumps({"error": f"Workflow '{workflow_id}' no encontrado"})
    return json.dumps(wf.get_execution_state(), ensure_ascii=False, indent=2)


def get_workflow_history(workflow_id: str) -> str:
    """
    Devuelve el historial completo de eventos del workflow:
    todos los fallos anteriores con error exacto, tipo y timestamp.
    Equivale a: temporalClient.GetWorkflowHistory()
    """
    wf = get_workflow(workflow_id)
    if not wf:
        return json.dumps({"error": f"Workflow '{workflow_id}' no encontrado"})
    return json.dumps(wf.get_history(), ensure_ascii=False, indent=2)


def get_workflow_current_step(workflow_id: str) -> str:
    """
    Devuelve el step actual del workflow y los datos disponibles
    en ese momento (carrier, país, si hay reembolso ya emitido, etc.)
    Equivale a: temporalClient.QueryWorkflow("current_state")
    """
    wf = get_workflow(workflow_id)
    if not wf:
        return json.dumps({"error": f"Workflow '{workflow_id}' no encontrado"})
    return json.dumps(wf.get_current_step(), ensure_ascii=False, indent=2)


# ── Schemas para registrar en la LLM ──────────────────────────────────────────

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_workflow_execution_state",
            "description": "Devuelve el estado vivo del workflow: actividad pendiente, número de intentos y último error.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string", "description": "ID del workflow (ej: 'WORKFLOW-001')"}
                },
                "required": ["workflow_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_workflow_history",
            "description": "Devuelve el historial completo de eventos del workflow con todos los fallos anteriores.",
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
            "name": "get_workflow_current_step",
            "description": "Devuelve el step actual del workflow y los datos disponibles en ese momento.",
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
    "get_workflow_execution_state": get_workflow_execution_state,
    "get_workflow_history":         get_workflow_history,
    "get_workflow_current_step":    get_workflow_current_step,
}