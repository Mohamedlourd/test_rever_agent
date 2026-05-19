"""
KnowledgeBase — fuente de verdad interna de REVER
Definiciones completas de los 9 steps del workflow de devoluciones
y todos sus errores posibles con acción recomendada.
"""


class StepDefinition:
    def __init__(
        self,
        step_id: str,
        name: str,
        description: str,
        systems_involved: list[str],
        is_critical: bool,
        can_use_alternative: bool,
        data_available: list[str],
        max_recommended_attempts: int | None,
        alternative_action: str | None = None,
        timer_deadline_days: int | None = None,
    ):
        self.step_id                  = step_id
        self.name                     = name
        self.description              = description
        self.systems_involved         = systems_involved
        self.is_critical              = is_critical
        self.can_use_alternative      = can_use_alternative
        self.alternative_action       = alternative_action
        self.data_available           = data_available
        self.max_recommended_attempts = max_recommended_attempts
        self.timer_deadline_days      = timer_deadline_days

    def get_definition(self) -> dict:
        return {
            "step_id":                  self.step_id,
            "name":                     self.name,
            "description":              self.description,
            "systems_involved":         self.systems_involved,
            "is_critical":              self.is_critical,
            "can_use_alternative":      self.can_use_alternative,
            "alternative_action":       self.alternative_action,
            "data_available":           self.data_available,
            "max_recommended_attempts": self.max_recommended_attempts,
            "timer_deadline_days":      self.timer_deadline_days,
        }


class ErrorDefinition:
    def __init__(self, step_id: str, errors: list[dict]):
        self.step_id = step_id
        self.errors  = errors

    def get_errors(self) -> dict:
        return {
            "step_id": self.step_id,
            "errors":  self.errors,
        }


# ══════════════════════════════════════════════════════════════════════════════
# STEP DEFINITIONS — los 9 steps completos
# ══════════════════════════════════════════════════════════════════════════════

STEP_DEFINITIONS: dict[str, StepDefinition] = {

    "STEP_1_VALIDATE_ORDER": StepDefinition(
        step_id          = "STEP_1_VALIDATE_ORDER",
        name             = "Validación del pedido",
        description      = (
            "El cliente introduce su número de pedido. REVER llama a la API del ecommerce "
            "para obtener los datos del pedido y validar que es retornable. "
            "Es el primer contacto con el sistema externo del cliente."
        ),
        systems_involved    = ["ecommerce_api"],
        is_critical         = True,
        can_use_alternative = False,
        data_available      = [
            "order_number", "order_id", "customer_info", "currency",
            "purchased_at", "fulfilled_at", "line_items",
            "is_returnable", "non_returnable_reason", "associated_costs",
        ],
        max_recommended_attempts = 5,
    ),

    "STEP_2_RISK_EVALUATION": StepDefinition(
        step_id          = "STEP_2_RISK_EVALUATION",
        name             = "Evaluación de riesgo",
        description      = (
            "El cliente elige qué items devolver y qué compensación quiere. "
            "REVER ejecuta el algoritmo REVER Protect para evaluar el riesgo de fraude "
            "y decidir si ofrece reembolso instantáneo, gift card o reembolso estándar."
        ),
        systems_involved    = ["risk_scoring_service", "customer_db"],
        is_critical         = True,
        can_use_alternative = True,
        alternative_action  = "fallback_to_static_rules",
        data_available      = [
            "customer_history", "total_orders", "total_returns", "return_rate",
            "fraud_score", "fraud_flags", "order_value", "payment_method",
            "items_to_return", "return_reason", "compensation_chosen",
        ],
        max_recommended_attempts = 3,
    ),

    "STEP_3_GENERATE_LABEL": StepDefinition(
        step_id          = "STEP_3_GENERATE_LABEL",
        name             = "Generación de etiqueta logística",
        description      = (
            "REVER selecciona el carrier óptimo según país, peso y preferencias del cliente, "
            "y llama a su API para generar la etiqueta de envío de vuelta. "
            "Es el primer contacto real con un sistema externo de carrier."
        ),
        systems_involved    = ["carrier_api", "label_storage_s3"],
        is_critical         = True,
        can_use_alternative = True,
        alternative_action  = "switch_carrier",
        data_available      = [
            "pickup_address", "pickup_postal_code", "pickup_country",
            "destination_warehouse", "package_weight_kg",
            "carrier_selected", "label_format", "is_international",
        ],
        max_recommended_attempts = 3,
    ),

    "STEP_4_NOTIFY_CUSTOMER": StepDefinition(
        step_id          = "STEP_4_NOTIFY_CUSTOMER",
        name             = "Notificación al cliente",
        description      = (
            "Se envía al cliente la etiqueta de devolución, las instrucciones de envío "
            "y el número de tracking por email y SMS. "
            "Este step es NO crítico — si falla, el workflow puede continuar sin él."
        ),
        systems_involved    = ["email_service", "sms_service"],
        is_critical         = False,
        can_use_alternative = True,
        alternative_action  = "skip_sms_keep_email",
        data_available      = [
            "customer_email", "customer_phone", "tracking_number",
            "label_pdf_url", "pickup_options", "drop_off_points",
            "scheduled_pickup_date",
        ],
        max_recommended_attempts = 3,
    ),

    "STEP_5_WAIT_PICKUP": StepDefinition(
        step_id          = "STEP_5_WAIT_PICKUP",
        name             = "Espera de recogida por carrier",
        description      = (
            "El workflow hiberna esperando el Signal del carrier confirmando que recogió el paquete. "
            "No hay activity corriendo — el workflow duerme en Temporal hasta recibir el signal. "
            "Si el timer de 7 días expira sin signal, el cliente nunca envió el paquete."
        ),
        systems_involved    = ["carrier_webhook", "temporal_signals"],
        is_critical         = True,
        can_use_alternative = False,
        data_available      = [
            "tracking_number", "scheduled_pickup_date",
            "pickup_method", "days_waiting", "timer_deadline",
        ],
        max_recommended_attempts = None,
        timer_deadline_days      = 7,
    ),

    "STEP_6_TRANSIT": StepDefinition(
        step_id          = "STEP_6_TRANSIT",
        name             = "Tránsito hacia el almacén",
        description      = (
            "El paquete está en tránsito. REVER recibe actualizaciones de tracking via Signals "
            "y actualiza el estado en tiempo real. El workflow espera el Signal de llegada al almacén. "
            "Puede durar entre 1 y 14 días según origen y destino."
        ),
        systems_involved    = ["carrier_tracking_api", "temporal_signals"],
        is_critical         = True,
        can_use_alternative = False,
        data_available      = [
            "tracking_events", "current_status", "last_location",
            "estimated_warehouse_arrival", "days_in_transit",
            "origin_country", "destination_country", "is_international",
            "hours_without_movement",
        ],
        max_recommended_attempts = None,
        timer_deadline_days      = 14,
    ),

    "STEP_7_WAREHOUSE_INSPECTION": StepDefinition(
        step_id          = "STEP_7_WAREHOUSE_INSPECTION",
        name             = "Recepción e inspección en almacén",
        description      = (
            "El almacén recibe el paquete, lo inspecciona físicamente y notifica a REVER el resultado. "
            "REVER decide el destino del producto: stock principal, outlet, reparación o descarte. "
            "El resultado de la inspección determina si el reembolso se aprueba o se rechaza."
        ),
        systems_involved    = ["warehouse_management_system"],
        is_critical         = True,
        can_use_alternative = False,
        data_available      = [
            "warehouse_received_at", "inspection_condition",
            "photos", "inspector_notes", "product_destination",
            "return_status",
        ],
        max_recommended_attempts = 5,
    ),

    "STEP_8_PROCESS_REFUND": StepDefinition(
        step_id          = "STEP_8_PROCESS_REFUND",
        name             = "Procesamiento del reembolso final",
        description      = (
            "Con el producto aceptado en el almacén, REVER procesa el reembolso definitivo "
            "via la pasarela de pago original del cliente (Redsys, PayPal, Sequra). "
            "Si el reembolso era instantáneo, aquí se confirma. Si era estándar, aquí se ejecuta. "
            "Nunca se mueve dinero con importes incorrectos — cualquier discrepancia escala."
        ),
        systems_involved    = ["payment_gateway", "redsys", "paypal", "sequra"],
        is_critical         = True,
        can_use_alternative = False,
        data_available      = [
            "refund_amount_before_costs", "refund_amount_after_costs",
            "currency", "payment_method", "transaction_id",
            "refund_type", "return_status", "shipping_cost_refund",
            "return_shipping_cost", "instant_refund_already_issued",
        ],
        max_recommended_attempts = 5,
    ),

    "STEP_9_NOTIFY_ECOMMERCE": StepDefinition(
        step_id          = "STEP_9_NOTIFY_ECOMMERCE",
        name             = "Notificación final al ecommerce",
        description      = (
            "REVER hace POST /rever/return al sistema del ecommerce cliente con el resultado "
            "completo de la devolución para que lo refleje en su ERP o sistema de gestión. "
            "Es el último step del workflow — cierra el ciclo de la devolución."
        ),
        systems_involved    = ["ecommerce_api"],
        is_critical         = True,
        can_use_alternative = False,
        data_available      = [
            "ecommerce_id", "order_id", "return_line_items",
            "return_status", "refund_amounts", "shipping_costs",
        ],
        max_recommended_attempts = 10,
    ),

}


# ══════════════════════════════════════════════════════════════════════════════
# ERROR DEFINITIONS — todos los errores posibles por step
# ══════════════════════════════════════════════════════════════════════════════

ERROR_DEFINITIONS: dict[str, ErrorDefinition] = {

    "STEP_1_VALIDATE_ORDER": ErrorDefinition(
        step_id = "STEP_1_VALIDATE_ORDER",
        errors  = [
            {
                "error_pattern": "500",
                "description": "Servidor del ecommerce caído",
                "likely_cause": "Sistema del cliente con problemas temporales",
                "recommended_action": "RETRY_LATER",
                "retry_delay_minutes": 5,
                "max_attempts_before_escalate": 5,
            },
            {
                "error_pattern": "timeout",
                "description": "Timeout en llamada al ecommerce",
                "likely_cause": "Latencia alta puntual en el sistema del cliente",
                "recommended_action": "RETRY",
                "retry_delay_minutes": 0,
                "max_attempts_before_escalate": 3,
            },
            {
                "error_pattern": "404",
                "description": "Pedido no encontrado",
                "likely_cause": "Número de pedido incorrecto o pedido eliminado del sistema",
                "recommended_action": "NON_RETRYABLE",
                "escalation_reason": "El pedido no existe — workflow termina con mensaje al cliente",
                "non_retryable": True,
            },
            {
                "error_pattern": "is_returnable_false_reason_4",
                "description": "Pedido aún no entregado al cliente",
                "likely_cause": "El pedido está en camino — el cliente no lo ha recibido todavía",
                "recommended_action": "NON_RETRYABLE",
                "escalation_reason": "No se puede iniciar devolución de algo que no se ha recibido",
                "non_retryable": True,
            },
            {
                "error_pattern": "is_returnable_false_reason_5",
                "description": "Fuera del plazo de devolución",
                "likely_cause": "El cliente superó el periodo permitido por la política de la marca",
                "recommended_action": "NON_RETRYABLE",
                "escalation_reason": "Política de la marca — no hay retry posible",
                "non_retryable": True,
            },
            {
                "error_pattern": "401",
                "description": "Error de autenticación con el ecommerce",
                "likely_cause": "Credenciales de integración expiradas o revocadas",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Las credenciales necesitan renovarse — requiere acción del equipo de integraciones",
                "non_retryable": True,
            },
            {
                "error_pattern": "connection_refused",
                "description": "Conexión rechazada al sistema del ecommerce",
                "likely_cause": "El servidor del cliente está completamente caído o la IP de REVER está bloqueada",
                "recommended_action": "RETRY_LATER",
                "retry_delay_minutes": 15,
                "max_attempts_before_escalate": 4,
            },
        ],
    ),

    "STEP_2_RISK_EVALUATION": ErrorDefinition(
        step_id = "STEP_2_RISK_EVALUATION",
        errors  = [
            {
                "error_pattern": "service_unavailable",
                "description": "Servicio de scoring interno caído",
                "likely_cause": "Microservicio interno down temporalmente",
                "recommended_action": "RETRY",
                "retry_delay_minutes": 0,
                "max_attempts_before_escalate": 3,
            },
            {
                "error_pattern": "timeout",
                "description": "Timeout del modelo de scoring",
                "likely_cause": "Modelo de IA tardando más de lo esperado bajo carga alta",
                "recommended_action": "RETRY",
                "retry_delay_minutes": 1,
                "max_attempts_before_escalate": 3,
                "fallback": "Si persiste, aplicar reglas estáticas conservadoras como alternativa",
            },
            {
                "error_pattern": "FraudDetected",
                "description": "Fraude detectado — score del cliente supera el umbral",
                "likely_cause": "El cliente tiene flags de comportamiento fraudulento activos",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Revisión manual obligatoria — no hay retry automático posible",
                "non_retryable": True,
            },
            {
                "error_pattern": "insufficient_data",
                "description": "Datos insuficientes para evaluar el riesgo",
                "likely_cause": "Cliente nuevo sin historial suficiente en la plataforma",
                "recommended_action": "SKIP",
                "skip_reason": "Aplicar política conservadora por defecto: continuar sin reembolso instantáneo",
            },
            {
                "error_pattern": "model_error",
                "description": "Error interno del modelo de scoring",
                "likely_cause": "Bug en el modelo o datos de entrada con formato inesperado",
                "recommended_action": "RETRY",
                "retry_delay_minutes": 0,
                "max_attempts_before_escalate": 2,
                "fallback": "Si persiste, aplicar reglas estáticas y loguear para investigación",
            },
        ],
    ),

    "STEP_3_GENERATE_LABEL": ErrorDefinition(
        step_id = "STEP_3_GENERATE_LABEL",
        errors  = [
            {
                "error_pattern": "503",
                "description": "Carrier API temporalmente no disponible",
                "likely_cause": "El servidor del carrier está caído o en mantenimiento programado",
                "recommended_action": "RETRY_LATER",
                "retry_delay_minutes": 30,
                "max_attempts_before_escalate": 5,
                "alternative": "Si persiste más de 2 horas, considerar cambio a carrier alternativo",
            },
            {
                "error_pattern": "429",
                "description": "Rate limit del carrier alcanzado",
                "likely_cause": "Demasiadas peticiones simultáneas a la API del carrier",
                "recommended_action": "RETRY_LATER",
                "retry_delay_minutes": 10,
                "max_attempts_before_escalate": 3,
            },
            {
                "error_pattern": "400",
                "description": "Datos de dirección inválidos",
                "likely_cause": "Código postal incorrecto o formato de dirección no válido para ese carrier",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Requiere corrección manual de la dirección — no se puede reintentar con los mismos datos",
                "non_retryable": True,
            },
            {
                "error_pattern": "timeout",
                "description": "Timeout en la llamada al carrier",
                "likely_cause": "Latencia alta puntual en la API del carrier",
                "recommended_action": "RETRY",
                "retry_delay_minutes": 0,
                "max_attempts_before_escalate": 3,
            },
            {
                "error_pattern": "carrier_not_available_in_country",
                "description": "El carrier no opera en el país de recogida",
                "likely_cause": "Error de routing — el carrier asignado no cubre esa geografía",
                "recommended_action": "SKIP",
                "skip_reason": "Reasignar automáticamente a un carrier alternativo disponible en ese país",
            },
            {
                "error_pattern": "label_format_not_supported",
                "description": "Formato de etiqueta no soportado por el carrier",
                "likely_cause": "Bug de integración — el carrier no acepta el formato solicitado",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Problema de código en la integración — requiere revisión del equipo de integraciones",
                "non_retryable": True,
            },
            {
                "error_pattern": "invalid_weight",
                "description": "Peso del paquete fuera de los límites del carrier",
                "likely_cause": "El carrier tiene restricciones de peso no verificadas en el routing",
                "recommended_action": "SKIP",
                "skip_reason": "Cambiar a carrier alternativo que soporte ese rango de peso",
            },
        ],
    ),

    "STEP_4_NOTIFY_CUSTOMER": ErrorDefinition(
        step_id = "STEP_4_NOTIFY_CUSTOMER",
        errors  = [
            {
                "error_pattern": "email_provider_down",
                "description": "Proveedor de email caído",
                "likely_cause": "SendGrid, SES o el proveedor de email tiene una incidencia activa",
                "recommended_action": "RETRY_LATER",
                "retry_delay_minutes": 5,
                "max_attempts_before_escalate": 3,
            },
            {
                "error_pattern": "email_bounced",
                "description": "Email rebotado — dirección incorrecta",
                "likely_cause": "El cliente tiene un email inválido o inexistente registrado",
                "recommended_action": "SKIP",
                "skip_reason": "Loguear para revisión posterior — el workflow no se bloquea por una notificación fallida",
            },
            {
                "error_pattern": "sms_failed",
                "description": "SMS no entregado",
                "likely_cause": "Proveedor de SMS caído, número inválido o país no soportado",
                "recommended_action": "SKIP",
                "skip_reason": "El email ya fue enviado — el SMS es complementario y no crítico para el flujo",
            },
            {
                "error_pattern": "label_pdf_not_ready",
                "description": "El PDF de la etiqueta aún no está disponible en S3",
                "likely_cause": "Race condition — el step anterior terminó pero el PDF aún no se subió",
                "recommended_action": "RETRY",
                "retry_delay_minutes": 0,
                "max_attempts_before_escalate": 3,
            },
            {
                "error_pattern": "template_render_error",
                "description": "Error al renderizar la plantilla del email",
                "likely_cause": "Bug en la plantilla o datos con caracteres inesperados",
                "recommended_action": "SKIP",
                "skip_reason": "No es crítico — el cliente puede ver el tracking en el portal aunque el email falle",
            },
        ],
    ),

    "STEP_5_WAIT_PICKUP": ErrorDefinition(
        step_id = "STEP_5_WAIT_PICKUP",
        errors  = [
            {
                "error_pattern": "timer_expired_no_pickup",
                "description": "Timer de 7 días expirado sin Signal de recogida",
                "likely_cause": "El cliente nunca llevó el paquete al punto de entrega o el carrier no pasó",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Contactar al cliente — si se dio reembolso instantáneo, iniciar proceso de reversión",
                "non_retryable": True,
            },
            {
                "error_pattern": "webhook_not_received",
                "description": "El Signal del carrier no llegó pero el tracking muestra recogida",
                "likely_cause": "Bug en la integración del webhook — el evento se perdió",
                "recommended_action": "RETRY",
                "retry_delay_minutes": 0,
                "note": "Hacer polling manual al carrier y enviar el Signal manualmente si el tracking confirma recogida",
            },
            {
                "error_pattern": "carrier_pickup_failed",
                "description": "El carrier reporta fallo en la recogida",
                "likely_cause": "El cliente no estaba en casa, acceso denegado o dirección no encontrada",
                "recommended_action": "RETRY_LATER",
                "retry_delay_minutes": 1440,
                "note": "Reagendar recogida automáticamente con nuevo timer",
                "max_attempts_before_escalate": 2,
            },
            {
                "error_pattern": "package_lost_before_pickup",
                "description": "El carrier reporta pérdida antes de confirmar recogida",
                "likely_cause": "Incidente logístico grave en el carrier",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Abrir reclamación con el carrier — requiere gestión manual",
                "non_retryable": True,
            },
        ],
    ),

    "STEP_6_TRANSIT": ErrorDefinition(
        step_id = "STEP_6_TRANSIT",
        errors  = [
            {
                "error_pattern": "no_movement_48h",
                "description": "Sin actualizaciones de tracking durante más de 48 horas",
                "likely_cause": "Paquete atascado en un hub o posiblemente perdido",
                "recommended_action": "RETRY",
                "retry_delay_minutes": 0,
                "note": "Hacer polling al carrier. Si sigue sin movimiento tras 2 intentos, ESCALAR",
                "max_attempts_before_escalate": 2,
            },
            {
                "error_pattern": "timer_expired",
                "description": "Timer de 14 días expirado sin llegada al almacén",
                "likely_cause": "Retraso extremo o paquete perdido en tránsito",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Investigar con el carrier — posible pérdida, abrir reclamación",
                "non_retryable": True,
            },
            {
                "error_pattern": "customs_blocked",
                "description": "Paquete retenido en aduanas",
                "likely_cause": "Devolución internacional sin documentación aduanera correcta",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Requiere documentación manual — el equipo de operaciones debe gestionar con aduanas",
                "non_retryable": True,
            },
            {
                "error_pattern": "wrong_warehouse_delivered",
                "description": "Paquete entregado en almacén incorrecto",
                "likely_cause": "Error de routing del carrier",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Coordinar reenvío interno entre almacenes — requiere gestión manual",
                "non_retryable": True,
            },
            {
                "error_pattern": "package_damaged_in_transit",
                "description": "El carrier reporta daños al paquete durante el tránsito",
                "likely_cause": "Manipulación incorrecta del paquete por el carrier",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Abrir reclamación con el carrier por daños — el reembolso puede verse afectado",
                "non_retryable": True,
            },
            {
                "error_pattern": "tracking_api_down",
                "description": "API de tracking del carrier no disponible",
                "likely_cause": "El servicio de tracking del carrier tiene una incidencia",
                "recommended_action": "RETRY_LATER",
                "retry_delay_minutes": 30,
                "note": "El paquete sigue en tránsito — esto solo afecta a la visibilidad, no al envío en sí",
                "max_attempts_before_escalate": 5,
            },
        ],
    ),

    "STEP_7_WAREHOUSE_INSPECTION": ErrorDefinition(
        step_id = "STEP_7_WAREHOUSE_INSPECTION",
        errors  = [
            {
                "error_pattern": "wms_unavailable",
                "description": "Sistema de gestión del almacén (WMS) no disponible",
                "likely_cause": "El WMS tiene mantenimiento programado — suele ocurrir de madrugada",
                "recommended_action": "RETRY_LATER",
                "retry_delay_minutes": 60,
                "max_attempts_before_escalate": 5,
            },
            {
                "error_pattern": "timeout",
                "description": "Timeout al comunicarse con el WMS",
                "likely_cause": "El sistema del almacén está lento bajo carga alta",
                "recommended_action": "RETRY",
                "retry_delay_minutes": 0,
                "max_attempts_before_escalate": 3,
            },
            {
                "error_pattern": "photos_upload_failed",
                "description": "Las fotos de inspección no se pudieron subir",
                "likely_cause": "Fallo en el upload a S3 o problema de conectividad en el almacén",
                "recommended_action": "SKIP",
                "skip_reason": "Las fotos son complementarias — si hay notas del inspector, la inspección puede continuar",
            },
            {
                "error_pattern": "wrong_item_received",
                "description": "El producto recibido no coincide con el pedido",
                "likely_cause": "El cliente envió un producto diferente al declarado — posible fraude",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Revisar manualmente — posible fraude. Retener el reembolso hasta investigación",
                "non_retryable": True,
            },
            {
                "error_pattern": "inspection_rejected",
                "description": "Producto rechazado en la inspección — dañado o usado",
                "likely_cause": "El producto llegó en condiciones que no cumplen la política de devolución",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Notificar al cliente — posible disputa. El reembolso puede ser parcial o denegado",
                "non_retryable": True,
            },
            {
                "error_pattern": "package_not_arrived",
                "description": "El tracking dice entregado pero el almacén no lo ha recibido",
                "likely_cause": "Error del carrier al marcar como entregado o recibido en zona equivocada",
                "recommended_action": "RETRY_LATER",
                "retry_delay_minutes": 120,
                "note": "Puede ser un retraso administrativo — esperar antes de escalar",
                "max_attempts_before_escalate": 3,
            },
        ],
    ),

    "STEP_8_PROCESS_REFUND": ErrorDefinition(
        step_id = "STEP_8_PROCESS_REFUND",
        errors  = [
            {
                "error_pattern": "payment_gateway_down",
                "description": "Pasarela de pago caída",
                "likely_cause": "Redsys, PayPal o Sequra tienen una incidencia activa",
                "recommended_action": "RETRY_LATER",
                "retry_delay_minutes": 5,
                "max_attempts_before_escalate": 5,
            },
            {
                "error_pattern": "timeout",
                "description": "Timeout en la llamada a la pasarela de pago",
                "likely_cause": "La pasarela está lenta — puede que el reembolso se haya procesado igualmente",
                "recommended_action": "ESCALATE",
                "escalation_reason": "NUNCA reintentar un reembolso por timeout sin verificar — riesgo de doble reembolso",
                "non_retryable": True,
            },
            {
                "error_pattern": "transaction_expired",
                "description": "La transacción de pago original ha expirado",
                "likely_cause": "Han pasado demasiados días desde la compra — la pasarela no permite el reembolso",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Reembolso manual necesario — la pasarela no puede procesarlo automáticamente",
                "non_retryable": True,
            },
            {
                "error_pattern": "amount_mismatch",
                "description": "Discrepancia en el importe a reembolsar",
                "likely_cause": "Error de cálculo entre sistemas",
                "recommended_action": "ESCALATE",
                "escalation_reason": "NUNCA mover dinero con importes incorrectos — revisión manual obligatoria",
                "non_retryable": True,
            },
            {
                "error_pattern": "card_declined",
                "description": "La tarjeta del cliente rechaza el reembolso",
                "likely_cause": "Tarjeta cancelada, expirada o cuenta bancaria cerrada",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Contactar al cliente para obtener método de pago alternativo",
                "non_retryable": True,
            },
            {
                "error_pattern": "instant_refund_irrecoverable",
                "description": "El reembolso instantáneo ya emitido no puede revertirse",
                "likely_cause": "El cliente ya gastó el dinero o la tarjeta fue cancelada tras el reembolso",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Abrir proceso de recuperación de deuda — requiere gestión manual",
                "non_retryable": True,
            },
        ],
    ),

    "STEP_9_NOTIFY_ECOMMERCE": ErrorDefinition(
        step_id = "STEP_9_NOTIFY_ECOMMERCE",
        errors  = [
            {
                "error_pattern": "500",
                "description": "Sistema del ecommerce caído",
                "likely_cause": "El sistema del cliente tiene una incidencia temporal",
                "recommended_action": "RETRY_LATER",
                "retry_delay_minutes": 5,
                "max_attempts_before_escalate": 10,
                "note": "Es el último step — ser generoso con los reintentos antes de escalar",
            },
            {
                "error_pattern": "timeout",
                "description": "Timeout al notificar al ecommerce",
                "likely_cause": "El sistema del cliente está lento",
                "recommended_action": "RETRY",
                "retry_delay_minutes": 0,
                "max_attempts_before_escalate": 5,
            },
            {
                "error_pattern": "404",
                "description": "El endpoint de notificación no existe",
                "likely_cause": "El ecommerce cambió su API sin actualizar la integración con REVER",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Bug de integración — el equipo de integraciones debe actualizar el endpoint",
                "non_retryable": True,
            },
            {
                "error_pattern": "406",
                "description": "Datos inválidos rechazados por el ecommerce",
                "likely_cause": "Discrepancia en los IDs o formato de datos entre REVER y el ecommerce",
                "recommended_action": "ESCALATE",
                "escalation_reason": "Inconsistencia de datos grave — requiere revisión manual",
                "non_retryable": True,
            },
            {
                "error_pattern": "401",
                "description": "Error de autenticación con el ecommerce",
                "likely_cause": "Credenciales de integración expiradas o token revocado",
                "recommended_action": "ESCALATE",
                "escalation_reason": "El equipo de integraciones debe renovar las credenciales con el ecommerce",
                "non_retryable": True,
            },
            {
                "error_pattern": "duplicate_notification",
                "description": "El ecommerce ya procesó esta notificación",
                "likely_cause": "El step se reintentó y el ecommerce ya había recibido la primera notificación",
                "recommended_action": "SKIP",
                "skip_reason": "La notificación ya llegó correctamente en un intento anterior — el workflow puede cerrarse",
            },
        ],
    ),

}


# ── Getters ────────────────────────────────────────────────────────────────────

def get_step_definition(step_id: str) -> StepDefinition | None:
    return STEP_DEFINITIONS.get(step_id)


def get_error_definition(step_id: str) -> ErrorDefinition | None:
    return ERROR_DEFINITIONS.get(step_id)


def get_all_step_ids() -> list[str]:
    """Devuelve todos los step IDs disponibles en orden."""
    return list(STEP_DEFINITIONS.keys())