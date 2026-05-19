"""
main.py — Entry point del agente REVER

Uso:
    python main.py --scenario SCENARIO_1
    python main.py --scenario SCENARIO_2
    python main.py --workflow WORKFLOW-001   # directo por workflow_id
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ── Importar todas las tools ───────────────────────────────────────────────────

from agent.tools.temporal_tools  import TOOLS_MAP as TEMPORAL_TOOLS,  SCHEMAS as TEMPORAL_SCHEMAS
from agent.tools.knowledge_tools import TOOLS_MAP as KNOWLEDGE_TOOLS, SCHEMAS as KNOWLEDGE_SCHEMAS
from agent.tools.carrier_tools   import TOOLS_MAP as CARRIER_TOOLS,   SCHEMAS as CARRIER_SCHEMAS
from agent.tools.customer_tools  import TOOLS_MAP as CUSTOMER_TOOLS,  SCHEMAS as CUSTOMER_SCHEMAS
from agent.tools.payment_tools   import TOOLS_MAP as PAYMENT_TOOLS,   SCHEMAS as PAYMENT_SCHEMAS

# ── Merge de todas las tools ───────────────────────────────────────────────────

ALL_TOOLS_MAP = {
    **TEMPORAL_TOOLS,
    **KNOWLEDGE_TOOLS,
    **CARRIER_TOOLS,
    **CUSTOMER_TOOLS,
    **PAYMENT_TOOLS,
}

ALL_SCHEMAS = (
    TEMPORAL_SCHEMAS  +
    KNOWLEDGE_SCHEMAS +
    CARRIER_SCHEMAS   +
    CUSTOMER_SCHEMAS  +
    PAYMENT_SCHEMAS
)

# ── Escenarios predefinidos ────────────────────────────────────────────────────

SCENARIOS = {
    "SCENARIO_1": {
        "description": "Carrier DHL caído — fallo en STEP_3 con cliente limpio",
        "workflow_id":  "WORKFLOW-001",
        "expected":     "RETRY_LATER o SWITCH_CARRIER a UPS",
    },
    "SCENARIO_2": {
        "description": "Fraude detectado — fallo en STEP_2 con cliente sospechoso",
        "workflow_id":  "WORKFLOW-002",
        "expected":     "ESCALATE — revisión manual obligatoria",
    },
}


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Agente REVER — análisis de workflows fallidos")
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario",  choices=list(SCENARIOS.keys()), help="Escenario predefinido")
    group.add_argument("--workflow",  help="ID de workflow directo (ej: WORKFLOW-001)")
    args = parser.parse_args()

    if args.scenario:
        scenario    = SCENARIOS[args.scenario]
        workflow_id = scenario["workflow_id"]
        print(f"Escenario: {args.scenario}")
        print(f"Descripción: {scenario['description']}")
        print(f"Decisión esperada: {scenario['expected']}")
    else:
        workflow_id = args.workflow
        print(f"Workflow directo: {workflow_id}")

    # Importar y ejecutar el agente
    from agent.llm.inference import run_agent

    result = run_agent(
        workflow_id  = workflow_id,
        tools_map    = ALL_TOOLS_MAP,
        tools_schema = ALL_SCHEMAS,
    )

    print(f"\nResultado del agente:\n{result}")


if __name__ == "__main__":
    main()