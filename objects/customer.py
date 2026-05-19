"""
Customer — clase con datos hardcodeados y getters
  - CUST-001: perfil limpio, cliente de confianza
  - CUST-002: perfil sospechoso, alto riesgo de fraude
"""


class Customer:
    def __init__(
        self,
        customer_id: str,
        email: str,
        first_name: str,
        last_name: str,
        account_age_days: int,
        total_orders: int,
        total_returns: int,
        return_rate: float,
        fraud_score: float,
        fraud_flags: list[str],
        lifetime_value_eur: float,
        instant_refund_eligible: bool,
        returns_this_month: int,
        country: str,
        return_history: list[dict],
    ):
        self.customer_id             = customer_id
        self.email                   = email
        self.first_name              = first_name
        self.last_name               = last_name
        self.account_age_days        = account_age_days
        self.total_orders            = total_orders
        self.total_returns           = total_returns
        self.return_rate             = return_rate
        self.fraud_score             = fraud_score
        self.fraud_flags             = fraud_flags
        self.lifetime_value_eur      = lifetime_value_eur
        self.instant_refund_eligible = instant_refund_eligible
        self.returns_this_month      = returns_this_month
        self.country                 = country
        self._return_history         = return_history

    def get_profile(self) -> dict:
        """Perfil del cliente sin el historial detallado."""
        return {
            "customer_id":             self.customer_id,
            "email":                   self.email,
            "first_name":              self.first_name,
            "last_name":               self.last_name,
            "account_age_days":        self.account_age_days,
            "total_orders":            self.total_orders,
            "total_returns":           self.total_returns,
            "return_rate":             self.return_rate,
            "fraud_score":             self.fraud_score,
            "fraud_flags":             self.fraud_flags,
            "lifetime_value_eur":      self.lifetime_value_eur,
            "instant_refund_eligible": self.instant_refund_eligible,
            "returns_this_month":      self.returns_this_month,
            "country":                 self.country,
        }

    def get_return_history(self) -> dict:
        """Historial completo de devoluciones anteriores."""
        return {
            "customer_id":   self.customer_id,
            "total_returns": self.total_returns,
            "return_rate":   self.return_rate,
            "returns":       self._return_history,
        }


# Datos hardcodeados 

CUST_001 = Customer(
    customer_id             = "CUST-001",
    email                   = "john.doe@example.com",
    first_name              = "John",
    last_name               = "Doe",
    account_age_days        = 795,
    total_orders            = 12,
    total_returns           = 3,
    return_rate             = 0.25,
    fraud_score             = 0.05,       # muy bajo — de confianza
    fraud_flags             = [],
    lifetime_value_eur      = 480.00,
    instant_refund_eligible = True,
    returns_this_month      = 1,
    country                 = "US",
    return_history = [
        {
            "return_id": "RET-001", "order_id": "5001", "date": "2023-05-10",
            "reason": "wrong_size", "resolution": "refund",
            "workflow_had_issues": False, "days_to_resolve": 4,
        },
        {
            "return_id": "RET-002", "order_id": "5890", "date": "2023-09-22",
            "reason": "product_damaged", "resolution": "exchange",
            "workflow_had_issues": True, "issue_step": "STEP_3_GENERATE_LABEL",
            "issue_resolution": "RETRY_LATER", "days_to_resolve": 6,
        },
        {
            "return_id": "RET-003", "order_id": "6100", "date": "2023-11-20",
            "reason": "not_as_described", "resolution": "gift_card",
            "workflow_had_issues": False, "days_to_resolve": 3,
        },
    ],
)


CUST_002 = Customer(
    customer_id             = "CUST-002",
    email                   = "m.garcia.returns@tempmail.com",
    first_name              = "Miguel",
    last_name               = "García",
    account_age_days        = 71,          # cuenta muy nueva
    total_orders            = 5,
    total_returns           = 4,           # devuelve casi todo
    return_rate             = 0.80,        # tasa altísima
    fraud_score             = 0.87,        # muy alto — sospechoso
    fraud_flags             = [
        "high_return_rate",
        "new_account_high_value_purchase",
        "temp_email_domain",
        "multiple_returns_same_month",
    ],
    lifetime_value_eur      = 0.00,        # nunca ha retenido nada
    instant_refund_eligible = False,
    returns_this_month      = 3,
    country                 = "ES",
    return_history = [
        {
            "return_id": "RET-101", "order_id": "7001", "date": "2024-01-25",
            "reason": "not_as_described", "resolution": "refund",
            "workflow_had_issues": False, "days_to_resolve": 2,
        },
        {
            "return_id": "RET-102", "order_id": "7105", "date": "2024-02-10",
            "reason": "wrong_item_received", "resolution": "refund",
            "workflow_had_issues": False, "days_to_resolve": 2,
        },
        {
            "return_id": "RET-103", "order_id": "7230", "date": "2024-03-05",
            "reason": "not_as_described", "resolution": "refund",
            "workflow_had_issues": False, "days_to_resolve": 1,
        },
        {
            "return_id": "RET-104", "order_id": "7310", "date": "2024-03-18",
            "reason": "product_damaged", "resolution": "pending",
            "workflow_had_issues": True, "issue_step": "STEP_2_RISK_EVALUATION",
            "issue_resolution": "ESCALATE", "days_to_resolve": None,
        },
    ],
)

CUSTOMERS: dict[str, Customer] = {
    "CUST-001": CUST_001,
    "CUST-002": CUST_002,
}


def get_customer(customer_id: str) -> Customer | None:
    return CUSTOMERS.get(customer_id)