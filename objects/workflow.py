"""
Workflow — clase con datos hardcodeados y getters
Dos workflows con errores distintos:
  - WORKFLOW-001: fallo en STEP_3 por DHL caído (503)
  - WORKFLOW-002: fallo en STEP_2 por fraude detectado
"""

class Workflow:
    def __init__(
            self,
        workflow_id: str,
        order_id: str,
        customer_id: str,
        product_id: str,
        carrier: str | None,
        execution_state: dict,
        history: dict,
        current_step: dict,
        payment: dict,
        refund: dict,    
    ):
        self.workflow_id = workflow_id
        self.order_id = order_id
        self.customer_id = customer_id
        self.product_id = product_id
        self.carrier = carrier
        self.execution_state = execution_state
        self.history = history
        self.current_step = current_step
        self.payment = payment
        self.refund = refund

    def get_execution_state(self) -> dict:
        return self.execution_state
    
    def get_history(self) -> dict:
        return self.history
 
    def get_current_step(self) -> dict:
        return self.current_step
 
    def get_payment(self) -> dict:
        return self.payment
 
    def get_refund(self) -> dict:
        return self.refund


# Datos hardcodeados

WORKFLOW_001 = Workflow(
    workflow_id  = "WORKFLOW-001",
    order_id     = "6754",
    customer_id  = "CUST-001",
    product_id   = "PROD-001",
    carrier      = "DHL",
    execution_state = {
        "workflow_id": "WORKFLOW-001",
        "order_id": "6754",
        "customer_id": "CUST-001",
        "product_id": "PROD-001",
        "carrier": "DHL",
        "status": "RUNNING",
        "started_at": "2024-03-21T10:00:00Z",
        "workflow_type": "ReturnWorkflow",
        "pending_activities": [
            {
                "activity_type": "GenerateShippingLabel",
                "state": "FAILED",
                "attempt": 3,
                "scheduled_at": "2024-03-21T10:05:00Z",
                "last_heartbeat_at": "2024-03-21T10:05:45Z",
                "last_failure_message": "503 Service Unavailable: DHL API temporarily down",
                "last_failure_type": "ApplicationError",
            }
        ],
        "pending_signals": [],
        "timers_active": [],
    },
    history = {
        "workflow_id": "WORKFLOW-001",
        "total_events": 7,
        "events": [
            {"event_id": 1, "type": "WorkflowExecutionStarted",  "timestamp": "2024-03-21T10:00:00Z"},
            {"event_id": 2, "type": "ActivityTaskCompleted", "activity_type": "ValidateOrder",          "timestamp": "2024-03-21T10:00:05Z", "attempt": 1},
            {"event_id": 3, "type": "ActivityTaskCompleted", "activity_type": "EvaluateRisk",           "timestamp": "2024-03-21T10:00:10Z", "attempt": 1},
            {"event_id": 4, "type": "ActivityTaskScheduled", "activity_type": "GenerateShippingLabel",  "timestamp": "2024-03-21T10:00:11Z", "attempt": 1},
            {"event_id": 5, "type": "ActivityTaskFailed",    "activity_type": "GenerateShippingLabel",  "timestamp": "2024-03-21T10:01:00Z", "attempt": 1,
             "error_type": "ApplicationError", "error_message": "Post 'https://api.dhl.com/shipments': dial tcp: i/o timeout"},
            {"event_id": 6, "type": "ActivityTaskFailed",    "activity_type": "GenerateShippingLabel",  "timestamp": "2024-03-21T10:03:00Z", "attempt": 2,
             "error_type": "ApplicationError", "error_message": "503 Service Unavailable: DHL API temporarily down"},
            {"event_id": 7, "type": "ActivityTaskFailed",    "activity_type": "GenerateShippingLabel",  "timestamp": "2024-03-21T10:05:00Z", "attempt": 3,
             "error_type": "ApplicationError", "error_message": "503 Service Unavailable: DHL API temporarily down"},
        ],
    },
    current_step = {
        "workflow_id": "WORKFLOW-001",
        "current_step": "STEP_3_GENERATE_LABEL",
        "step_started_at": "2024-03-21T10:00:11Z",
        "data_available": {
            "order_id": "6754",
            "customer_id": "CUST-001",
            "product_id": "PROD-001",
            "carrier_selected": "DHL",
            "customer_country": "US",
            "warehouse_country": "ES",
            "package_weight_kg": 0.5,
            "is_international": True,
            "refund_already_issued": False,
            "compensation_type": "standard_refund",
        },
    },
    payment = {
        "platform_id": "redsys",
        "transaction_id": "TXN-6754",
        "status": "CAPTURED",
        "amount_eur": 39.98,
        "is_refundable": True,
        "is_expired": False,
        "days_since_capture": 20,
        "days_until_expiry": 160,
        "partial_refunds_issued": [],
    },
    refund = {
        "workflow_id": "WORKFLOW-001",
        "instant_refund_issued": False,
        "refund_amount_eur": None,
        "refund_issued_at": None,
        "is_reversible": None,
    },
)

WORKFLOW_002 = Workflow(
    workflow_id  = "WORKFLOW-002",
    order_id     = "7310",
    customer_id  = "CUST-002",
    product_id   = "PROD-002",
    carrier      = None,
    execution_state = {
        "workflow_id": "WORKFLOW-002",
        "order_id": "7310",
        "customer_id": "CUST-002",
        "product_id": "PROD-002",
        "carrier": None,
        "status": "RUNNING",
        "started_at": "2024-03-21T11:00:00Z",
        "workflow_type": "ReturnWorkflow",
        "pending_activities": [
            {
                "activity_type": "EvaluateRisk",
                "state": "FAILED",
                "attempt": 1,
                "scheduled_at": "2024-03-21T11:00:05Z",
                "last_heartbeat_at": "2024-03-21T11:00:06Z",
                "last_failure_message": "FraudDetected: customer risk score 0.87 exceeds threshold 0.75. Flags: high_return_rate, new_account_high_value_purchase, temp_email_domain",
                "last_failure_type": "NonRetryableApplicationError",
            }
        ],
        "pending_signals": ["manual-review-decision"],
        "timers_active": [],
    },
    history = {
        "workflow_id": "WORKFLOW-002",
        "total_events": 5,
        "events": [
            {"event_id": 1, "type": "WorkflowExecutionStarted", "timestamp": "2024-03-21T11:00:00Z"},
            {"event_id": 2, "type": "ActivityTaskCompleted", "activity_type": "ValidateOrder",  "timestamp": "2024-03-21T11:00:04Z", "attempt": 1},
            {"event_id": 3, "type": "ActivityTaskScheduled", "activity_type": "EvaluateRisk",   "timestamp": "2024-03-21T11:00:05Z", "attempt": 1},
            {"event_id": 4, "type": "ActivityTaskFailed",    "activity_type": "EvaluateRisk",   "timestamp": "2024-03-21T11:00:06Z", "attempt": 1,
             "error_type": "NonRetryableApplicationError",
             "error_message": "FraudDetected: customer risk score 0.87 exceeds threshold 0.75. Flags: high_return_rate, new_account_high_value_purchase, temp_email_domain"},
            {"event_id": 5, "type": "WorkflowTaskCompleted", "timestamp": "2024-03-21T11:00:07Z",
             "note": "Workflow suspendido esperando signal manual-review-decision"},
        ],
    },
    current_step = {
        "workflow_id": "WORKFLOW-002",
        "current_step": "STEP_2_RISK_EVALUATION",
        "step_started_at": "2024-03-21T11:00:05Z",
        "data_available": {
            "order_id": "7310",
            "customer_id": "CUST-002",
            "product_id": "PROD-002",
            "carrier_selected": None,
            "customer_country": "ES",
            "warehouse_country": "ES",
            "package_weight_kg": 1.2,
            "is_international": False,
            "refund_already_issued": False,
            "compensation_type": "instant_refund",
        },
    },
    payment = {
        "platform_id": "paypal",
        "transaction_id": "TXN-7310",
        "status": "CAPTURED",
        "amount_eur": 189.99,
        "is_refundable": True,
        "is_expired": False,
        "days_since_capture": 3,
        "days_until_expiry": 177,
        "partial_refunds_issued": [],
    },
    refund = {
        "workflow_id": "WORKFLOW-002",
        "instant_refund_issued": False,
        "refund_amount_eur": None,
        "refund_issued_at": None,
        "is_reversible": None,
    },
)
 

WORKFLOWS: dict[str, Workflow] = {
    "WORKFLOW-001": WORKFLOW_001,
    "WORKFLOW-002": WORKFLOW_002,
}

def get_workflow(workflow_id: str) -> Workflow | None:
    return WORKFLOWS.get(workflow_id)