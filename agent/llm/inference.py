"""
inference.py — Inferencia con Qwen2.5-1.5B-Instruct + tool calling

Carga el modelo local y expone una función `run_agent` que:
1. Recibe el workflow_id del escenario a analizar
2. Entra en un loop ReAct: llama tools → analiza resultados → decide
3. Devuelve la decisión final (RETRY / RETRY_LATER / SKIP / ESCALATE)

Uso:
    from agent.llm.inference import run_agent
    result = run_agent(workflow_id="WORKFLOW-001")
"""

import json
import re
import sys
from pathlib import Path
from typing import Callable, cast

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from vect.vectorizer import vectorize_and_save

from transformers import AutoModelForCausalLM, AutoTokenizer, PreTrainedTokenizerBase, PreTrainedModel
# ── Config ─────────────────────────────────────────────────────────────────────

MODEL_ID   = "Qwen/Qwen2.5-1.5B-Instruct"
MODEL_PATH = Path(__file__).parent / "models" / "Qwen2.5-1.5B-Instruct"
MAX_STEPS  = 10      # máximo de tool calls por sesión
MAX_TOKENS = 512

# ── Carga del modelo ───────────────────────────────────────────────────────────

_model:     PreTrainedModel | None           = None
_tokenizer: PreTrainedTokenizerBase | None   = None


def load_model() -> tuple[PreTrainedModel, PreTrainedTokenizerBase]:
    """Carga el modelo y tokenizer en memoria (solo la primera vez)."""
    global _model, _tokenizer

    if _model is not None and _tokenizer is not None:
        return cast(PreTrainedModel, _model), cast(PreTrainedTokenizerBase, _tokenizer)

    model_path = str(MODEL_PATH) if MODEL_PATH.exists() else MODEL_ID
    print(f"Cargando modelo desde: {model_path}")

    _tokenizer = AutoTokenizer.from_pretrained(model_path)
    _model     = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype = "auto",
        device_map  = "auto",
    )
    print("Modelo cargado.")
    return cast(PreTrainedModel, _model), cast(PreTrainedTokenizerBase, _tokenizer)


# ── Inferencia base ────────────────────────────────────────────────────────────

def _generate(messages: list[dict], tools_schema: list[dict]) -> str:
    """
    Llama al modelo con el historial de mensajes y el schema de tools.
    Devuelve el texto generado por el modelo.
    """
    model, tokenizer = load_model()

    text: str = tokenizer.apply_chat_template(
        messages,
        tools                 = tools_schema,  # type: ignore[arg-type]
        tokenize              = False,
        add_generation_prompt = True,
    )

    inputs  = tokenizer(text, return_tensors="pt").to(model.device)  # type: ignore[arg-type]
    outputs = model.generate(  # type: ignore[call-overload]
        **inputs,
        max_new_tokens = MAX_TOKENS,
        do_sample      = False,
        pad_token_id   = tokenizer.eos_token_id,
    )

    # Solo los tokens nuevos generados
    new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    decoded: str = tokenizer.decode(new_tokens, skip_special_tokens=True)  # type: ignore[assignment]
    return decoded.strip()


# ── Parser de tool calls ───────────────────────────────────────────────────────

def _parse_tool_calls(response: str) -> list[dict]:
    """
    Extrae TODOS los tool calls del texto generado por el modelo.
    Qwen2.5 genera tool calls en formato JSON dentro de bloques <tool_call>.
    """
    calls = []
    for match in re.finditer(r"<tool_call>(.*?)</tool_call>", response, re.DOTALL):
        try:
            calls.append(json.loads(match.group(1).strip()))
        except json.JSONDecodeError:
            pass
    if calls:
        return calls

    # Fallback: JSON directo en el texto
    for match in re.finditer(r'\{[^{}]*"name"\s*:\s*"[^"]+"\s*,[^{}]*"arguments"\s*:\s*\{[^{}]*\}[^{}]*\}', response):
        try:
            calls.append(json.loads(match.group()))
        except json.JSONDecodeError:
            pass
    return calls


def _is_final_decision(response: str) -> bool:
    """Detecta si el modelo ha tomado una decisión final."""
    # Debe contener explícitamente "DECISIÓN FINAL:" o "DECISION:" seguido de una acción
    pattern = r"(?:DECISI[OÓ]N FINAL|DECISION)\s*:\s*(?:RETRY_LATER|SWITCH_CARRIER|RETRY|SKIP|ESCALATE)"
    return re.search(pattern, response, re.IGNORECASE) is not None


# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres un agente experto en diagnóstico de workflows de devoluciones de REVER.

Se te presenta un workflow que ha fallado. Tu misión es investigarlo con las tools disponibles y emitir una decisión fundamentada.

REGLAS:
- Usa las tools que necesites, en el orden que consideres. Tú decides cuándo y cuáles.
- NUNCA inventes ni asumas resultados de una tool — si necesitas un dato, llama a la tool.
- Solo llama a cada tool una vez con los mismos argumentos.
- No puedes emitir DECISIÓN FINAL sin haber verificado la causa del fallo con al menos una tool.
- Llama a las tools con <tool_call>, no las describas en texto.

TOOLS DISPONIBLES:
- get_workflow_execution_state(workflow_id): estado actual, último error, número de intentos
- get_workflow_history(workflow_id): historial completo de fallos
- get_workflow_current_step(workflow_id): datos del step en curso (carrier, país, etc.)
- get_workflow_step_definition(step_id): qué hace ese step y si tiene alternativa definida
- get_step_error_definitions(step_id): acción recomendada para cada error en ese step
- get_carrier_status(carrier): si el carrier está operativo, degradado o caído
- get_available_carriers(country, weight_class): carriers alternativos disponibles
- get_customer_profile(customer_id): perfil del cliente, nivel de riesgo, flags de fraude
- get_customer_return_history(customer_id): historial de devoluciones del cliente
- get_order_details(order_id, product_id): detalles del pedido y producto
- get_ecommerce_status(ecommerce_id): estado del ecommerce del pedido
- get_payment_status(workflow_id): estado del pago
- get_refund_status(workflow_id): si ya se emitió un reembolso

ACCIONES POSIBLES:
- RETRY          → error puntual y transitorio, reintenta ahora
- RETRY_LATER    → sistema externo caído o degradado, espera antes de reintentar
- SWITCH_CARRIER → carrier caído con alternativas disponibles
- SKIP           → step no crítico, el workflow puede continuar sin él
- ESCALATE       → requiere intervención humana

Cuando tengas evidencia suficiente, responde EXACTAMENTE así:

DECISIÓN FINAL: <ACCIÓN>
Causa: <qué pasó exactamente, basado en datos reales de las tools>
Verificación: <qué confirmaste con las tools llamadas>
Solución: <qué hacer concretamente>
"""


# ── Vectorización post-decisión ────────────────────────────────────────────────

def _save_vector(workflow_id: str, decision_text: str, messages: list[dict], called_tools: set[str]) -> None:
    """Extrae datos de los resultados de tools y guarda el vector en el CSV."""
    try:
        # Recoger todos los JSON de resultados de tools
        all_results = " ".join(
            m.get("content", "") for m in messages if m.get("role") == "tool"
        )

        def _jget(pattern: str, default: str = "") -> str:
            m = re.search(pattern, all_results)
            return m.group(1) if m else default

        def _jget_float(pattern: str, default: float = 0.0) -> float:
            try:
                return float(_jget(pattern, str(default)))
            except ValueError:
                return default

        def _jget_bool(pattern: str) -> bool:
            return _jget(pattern, "false").lower() in ("true", "1", "yes")

        # Extraer campos del fallo
        step_id    = _jget(r'"step_id":\s*"([^"]+)"', "STEP_3_GENERATE_LABEL")
        error_msg  = _jget(r'"last_failure_message":\s*"([^"]+)"', "")
        attempt    = int(_jget_float(r'"attempt":\s*(\d+)', 1))

        error_type = "unknown"
        for code in ("503", "429", "400", "timeout", "fraud", "non_retryable"):
            if code in error_msg.lower():
                error_type = code
                break

        # Sistema externo
        carrier      = _jget(r'"carrier":\s*"([^"]+)"')
        system_type  = "carrier" if carrier else "internal"
        carrier_status = _jget(r'"status":\s*"([A-Z]+)"', "OPERATIONAL")
        alternative  = "get_available_carriers" in called_tools

        # Cliente
        fraud_score      = _jget_float(r'"fraud_score":\s*([\d.]+)')
        return_rate      = _jget_float(r'"return_rate":\s*([\d.]+)')
        account_age_days = int(_jget_float(r'"account_age_days":\s*(\d+)', 365))
        returns_month    = int(_jget_float(r'"returns_this_month":\s*(\d+)', 0))

        # Riesgo financiero
        order_value      = _jget_float(r'"order_value":\s*([\d.]+)', 100.0)
        refund_issued    = _jget_bool(r'"instant_refund_issued":\s*(true|false)')
        country          = _jget(r'"pickup_country":\s*"([^"]+)"', "ES")
        is_intl          = _jget_bool(r'"is_international":\s*(true|false)')

        # Decisión
        dm = re.search(
            r"DECISI[OÓ]N FINAL:\s*(RETRY_LATER|SWITCH_CARRIER|RETRY|SKIP|ESCALATE)",
            decision_text, re.IGNORECASE
        )
        decision = dm.group(1).upper() if dm else "ESCALATE"
        # SWITCH_CARRIER no está en el vector — mapeamos a RETRY_LATER
        decision_mapped = "RETRY_LATER" if decision == "SWITCH_CARRIER" else decision

        vectorize_and_save(
            workflow_id            = workflow_id,
            step_id                = step_id,
            error_type             = error_type,
            attempt                = max(1, attempt),
            consecutive_same_error = max(1, attempt - 1),
            refund_already_issued  = refund_issued,
            order_value_eur        = order_value,
            system_type            = system_type,
            system_status          = carrier_status,
            alternative_available  = alternative,
            payment_is_refundable  = not refund_issued,
            days_since_purchase    = 30,
            refund_reversible      = not refund_issued,
            fraud_score            = fraud_score,
            return_rate            = return_rate,
            account_age_days       = account_age_days,
            returns_this_month     = returns_month,
            customer_country       = country,
            is_international       = is_intl,
            decision               = decision_mapped,
            worked                 = True,
            resolution_min         = 0,
        )
    except Exception as e:
        print(f"[vectorizer] Error al guardar vector: {e}")


# ── Loop principal del agente ──────────────────────────────────────────────────

def run_agent(workflow_id: str, tools_map: dict[str, Callable], tools_schema: list[dict]) -> str:
    """
    Ejecuta el agente para analizar un workflow fallido.

    Args:
        workflow_id:   ID del workflow a analizar (ej: "WORKFLOW-001")
        tools_map:     dict {nombre_tool: función_python}
        tools_schema:  lista de schemas JSON para pasar al modelo

    Returns:
        La decisión final del agente como string.
    """
    # El modelo debe haber llamado al menos una tool de verificación externa antes de decidir
    VERIFICATION_TOOLS = {
        "get_carrier_status", "get_available_carriers",
        "get_customer_profile", "get_customer_return_history",
        "get_order_details", "get_ecommerce_status",
        "get_payment_status", "get_refund_status",
    }
    ALL_TOOL_NAMES = {
        "get_workflow_execution_state", "get_workflow_history", "get_workflow_current_step",
        "get_workflow_step_definition", "get_step_error_definitions",
    } | VERIFICATION_TOOLS

    called_tools: set[str] = set()

    def _verified() -> bool:
        return bool(called_tools & VERIFICATION_TOOLS)

    def _suggested_tool() -> str:
        """Lee los resultados de tools ya ejecutadas y sugiere la siguiente verificación con args concretos."""
        all_results = " ".join(m.get("content", "") for m in messages if m.get("role") == "tool")

        carrier_m = re.search(r'"carrier":\s*"([^"]+)"', all_results)
        if carrier_m:
            carrier = carrier_m.group(1)
            if "get_carrier_status" not in called_tools:
                return f'<tool_call>{{"name": "get_carrier_status", "arguments": {{"carrier": "{carrier}"}}}}</tool_call>'
            if "get_available_carriers" not in called_tools:
                country_m = re.search(r'"pickup_country":\s*"([^"]+)"', all_results)
                country = country_m.group(1) if country_m else "ES"
                return f'<tool_call>{{"name": "get_available_carriers", "arguments": {{"country": "{country}", "weight_class": "light"}}}}</tool_call>'

        customer_m = re.search(r'"customer_id":\s*"([^"]+)"', all_results)
        if customer_m and "get_customer_profile" not in called_tools:
            cid = customer_m.group(1)
            return f'<tool_call>{{"name": "get_customer_profile", "arguments": {{"customer_id": "{cid}"}}}}</tool_call>'

        if "get_payment_status" not in called_tools:
            return f'<tool_call>{{"name": "get_payment_status", "arguments": {{"workflow_id": "{workflow_id}"}}}}</tool_call>'

        return ""

    def _find_hallucinated_tools(text: str) -> list[str]:
        """Detecta tools mencionadas en texto sin haber sido llamadas con <tool_call>."""
        if "<tool_call>" in text:
            return []
        return [t for t in ALL_TOOL_NAMES if t in text]

    messages = [
        {"role": "system",  "content": SYSTEM_PROMPT},
        {"role": "user",    "content": f"El workflow {workflow_id} ha fallado. Investiga qué ha pasado y decide la acción correcta."},
    ]

    print(f"\n{'='*60}")
    print(f"AGENTE INICIANDO — Workflow: {workflow_id}")
    print(f"{'='*60}\n")

    for step in range(MAX_STEPS):
        print(f"[Step {step + 1}] Generando respuesta...")
        response = _generate(messages, tools_schema)
        print(f"Modelo: {response}\n")

        # ¿El modelo ha tomado una decisión final?
        if _is_final_decision(response):
            if not _verified():
                suggestion = _suggested_tool()
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": (
                    f"Antes de decidir debes verificar con una tool externa. "
                    f"Ejecuta esto ahora:\n{suggestion}"
                )})
                continue
            print(f"\n{'='*60}")
            print("DECISIÓN FINAL TOMADA")
            print(f"{'='*60}")
            _save_vector(workflow_id, response, messages, called_tools)
            return response

        # ¿El modelo quiere llamar a tools?
        tool_calls = _parse_tool_calls(response)
        if tool_calls:
            messages.append({"role": "assistant", "content": response})
            executed_any = False

            for tc in tool_calls:
                tool_name = tc.get("name") or ""
                tool_args = tc.get("arguments", {})
                call_key  = f"{tool_name}({json.dumps(tool_args, sort_keys=True)})"

                if call_key in called_tools:
                    continue  # saltar duplicados

                called_tools.add(tool_name)
                called_tools.add(call_key)
                executed_any = True

                print(f"Tool call: {tool_name}({tool_args})")

                if tool_name not in tools_map:
                    tool_result = json.dumps({"error": f"Tool '{tool_name}' no existe"})
                else:
                    try:
                        tool_result = tools_map[tool_name](**tool_args)
                    except Exception as e:
                        tool_result = json.dumps({"error": str(e)})

                print(f"Resultado: {tool_result[:200]}...\n")
                messages.append({
                    "role": "tool",
                    "content": tool_result,
                    "name": tool_name,
                })

            if not executed_any:
                suggestion = _suggested_tool()
                content = "Ya llamaste a esas tools."
                if suggestion:
                    content += f" Ejecuta ahora:\n{suggestion}"
                elif _verified():
                    content += " Tienes suficiente evidencia. Emite tu DECISIÓN FINAL."
                messages.append({"role": "user", "content": content})
        else:
            # El modelo escribió texto sin tool call ni decisión final
            messages.append({"role": "assistant", "content": response})
            hallucinated = _find_hallucinated_tools(response)
            if hallucinated:
                tool_list = ", ".join(hallucinated)
                suggestion = _suggested_tool()
                content = (
                    f"Mencionaste {tool_list} pero NO las llamaste — "
                    f"los resultados que describes son inventados. "
                )
                if suggestion:
                    content += f"Ejecuta ahora:\n{suggestion}"
            elif _verified():
                content = "Tienes datos suficientes. Emite tu DECISIÓN FINAL."
            else:
                suggestion = _suggested_tool()
                content = "Ejecuta ahora:\n" + suggestion if suggestion else "Llama a una tool de verificación."
            messages.append({"role": "user", "content": content})

    return "ESCALATE — El agente alcanzó el máximo de pasos sin llegar a una decisión."