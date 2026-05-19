"""
vectorizer.py — Convierte un caso resuelto a vector y lo guarda en CSV

Uso después de que el agente tome una decisión:

    from vect.vectorizer import vectorize_and_save

    vectorize_and_save(
        workflow_id   = "WORKFLOW-001",
        step_id       = "STEP_3_GENERATE_LABEL",
        error_type    = "503",
        attempt       = 3,
        ...
        decision      = "RETRY_LATER",
        worked        = True,
        resolution_min= 45,
    )
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Config ─────────────────────────────────────────────────────────────────────

CSV_PATH = Path(__file__).parent / "decisions.csv"

STEP_ORDER   = [
    "STEP_1_VALIDATE_ORDER", "STEP_2_RISK_EVALUATION",
    "STEP_3_GENERATE_LABEL", "STEP_4_NOTIFY_CUSTOMER",
    "STEP_5_WAIT_PICKUP",    "STEP_6_TRANSIT",
    "STEP_7_WAREHOUSE_INSPECTION", "STEP_8_PROCESS_REFUND",
    "STEP_9_NOTIFY_ECOMMERCE",
]
ERROR_TYPES  = ["503", "429", "400", "timeout", "fraud", "non_retryable", "unknown"]
SYSTEM_TYPES = ["carrier", "ecommerce", "payment", "internal"]
DECISIONS    = ["RETRY", "RETRY_LATER", "SKIP", "ESCALATE"]
COUNTRY_RISK = {
    "ES": 0.1, "DE": 0.1, "FR": 0.2, "IT": 0.3,
    "US": 0.2, "GB": 0.1, "PT": 0.2, "NL": 0.1,
}

CSV_HEADER = (
    ["timestamp", "workflow_id", "step_id"] +
    ["step_index"] +
    [f"error_type_{e}" for e in ERROR_TYPES] +
    ["attempt_number", "consecutive_same_error",
     "refund_already_issued", "money_at_risk"] +
    [f"system_type_{s}" for s in SYSTEM_TYPES] +
    ["system_has_incident", "incident_severity", "alternative_available"] +
    ["order_value_normalized", "payment_is_refundable",
     "days_since_purchase", "refund_reversible"] +
    ["fraud_score", "return_rate", "account_age_normalized", "returns_this_month"] +
    ["hour_of_day", "is_weekend", "is_international", "country_risk"] +
    [f"decision_{d}" for d in DECISIONS] +
    ["decision_worked", "resolution_time_normalized"]
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _onehot(value: str, categories: list[str]) -> list[float]:
    return [1.0 if value == cat else 0.0 for cat in categories]

def _norm(value: float, max_val: float) -> float:
    return min(value / max_val, 1.0)

def _severity(status: str) -> float:
    return {"OPERATIONAL": 0.0, "DEGRADED": 0.5, "DOWN": 1.0}.get(status.upper(), 0.0)


# ── Función principal ──────────────────────────────────────────────────────────

def vectorize_and_save(
    # metadata
    workflow_id: str,
    step_id:     str,

    # grupo 1 — el fallo
    error_type:             str,
    attempt:                int,
    consecutive_same_error: int,
    refund_already_issued:  bool,
    order_value_eur:        float,

    # grupo 2 — el sistema externo
    system_type:          str,
    system_status:        str,
    alternative_available:bool,

    # grupo 3 — riesgo financiero
    payment_is_refundable:bool,
    days_since_purchase:  int,
    refund_reversible:    bool,

    # grupo 4 — el cliente
    fraud_score:          float,
    return_rate:          float,
    account_age_days:     int,
    returns_this_month:   int,

    # grupo 5 — contexto
    customer_country:     str,
    is_international:     bool,

    # grupo 6 — la decisión
    decision:             str,
    worked:               bool,
    resolution_min:       int,

) -> list[float]:
    """
    Convierte el contexto del caso a vector, lo guarda en el CSV y lo devuelve.
    """
    now = datetime.now()

    vector = (
        # grupo 1
        [_norm(STEP_ORDER.index(step_id) if step_id in STEP_ORDER else 0, 8)] +
        _onehot(error_type, ERROR_TYPES) +
        [_norm(attempt - 1, 4),
         _norm(consecutive_same_error, 5),
         1.0 if refund_already_issued else 0.0,
         _norm(order_value_eur, 500)] +

        # grupo 2
        _onehot(system_type, SYSTEM_TYPES) +
        [1.0 if system_status in ("DEGRADED", "DOWN") else 0.0,
         _severity(system_status),
         1.0 if alternative_available else 0.0] +

        # grupo 3
        [_norm(order_value_eur, 500),
         1.0 if payment_is_refundable else 0.0,
         _norm(days_since_purchase, 180),
         1.0 if refund_reversible else 0.0] +

        # grupo 4
        [max(0.0, min(fraud_score, 1.0)),
         max(0.0, min(return_rate, 1.0)),
         _norm(account_age_days, 1095),
         _norm(returns_this_month, 5)] +

        # grupo 5
        [now.hour / 23,
         1.0 if now.weekday() >= 5 else 0.0,
         1.0 if is_international else 0.0,
         COUNTRY_RISK.get(customer_country.upper(), 0.5)] +

        # grupo 6
        _onehot(decision, DECISIONS) +
        [1.0 if worked else 0.0,
         _norm(resolution_min, 1440)]
    )

    _save_to_csv(now, workflow_id, step_id, vector)

    return vector


def _save_to_csv(timestamp: datetime, workflow_id: str, step_id: str, vector: list[float]):
    """Guarda el vector en el CSV, creando el fichero con cabecera si no existe."""
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    file_exists = CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(CSV_HEADER)
        writer.writerow(
            [timestamp.isoformat(), workflow_id, step_id] +
            [round(v, 4) for v in vector]
        )

    print(f"[vectorizer] Guardado — {workflow_id} | {step_id} | {_get_decision(vector)}")


def _get_decision(vector: list[float]) -> str:
    """Extrae la decisión del vector mirando los campos onehot del grupo 6."""
    # Las 4 decisiones empiezan en la posición 31 del vector
    for i, d in enumerate(DECISIONS):
        if vector[31 + i] == 1.0:
            return d
    return "UNKNOWN"