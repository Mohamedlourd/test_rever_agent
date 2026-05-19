# REVER — AI Agent for Workflow Failure Resolution

## The Problem

REVER's return workflows are complex, multi-step processes that can run for days. A return journey involves validating an order, evaluating fraud risk, generating shipping labels, coordinating with carriers, waiting for warehouse inspection, and finally processing the refund.

Any of these steps can fail — a carrier API goes down, a payment gateway times out, a fraud score spikes unexpectedly. Today, when a step fails, Temporal retries it based on a static policy defined in code before deployment. The system doesn't know *why* something failed. It doesn't know if DHL has an active incident, if the customer is suspicious, or if there's a working alternative available. It just retries blindly — or escalates to a human.

This prototype explores a different approach: **let an AI agent investigate each failure and decide what to do.**

---

## The Idea

When a workflow step fails, instead of applying a static retry policy, an LLM agent is triggered. The agent receives the workflow ID and one objective: *figure out what happened and decide the best course of action.*

The agent has five possible decisions:

- **RETRY** — the error is transient, retry immediately
- **RETRY_LATER** — the external system needs time to recover, wait and retry
- **SWITCH_CARRIER** — the current carrier is down, switch to an available alternative
- **SKIP** — the step is non-critical, the workflow can continue without it
- **ESCALATE** — no automation can solve this, a human needs to intervene

To reach that decision, the agent doesn't guess. It investigates using a set of tools that let it query real data — the workflow's execution state, its failure history, the carrier's live status, the customer's fraud profile, the payment transaction, and a knowledge base that defines what each error means in the context of REVER's business.

The agent reasons step by step, calling tools in sequence, building up a picture of the situation before committing to a decision. The same way a senior engineer would investigate an on-call alert before acting.

---

## How It Works

```
Temporal workflow fails on a step
            │
            ▼
Agent receives: { workflow_id: "WORKFLOW-001" }
            │
            ▼
Agent investigates using tools:
  1. What is the current state of the workflow?
  2. How many times has this step failed? With what exact error?
  3. What does this step do and what errors can it have?
  4. Is the carrier currently operational? Any active incidents?
  5. Are there alternative carriers available?
  6. Does the customer have a suspicious profile?
  7. Has a refund already been issued? Is money at risk?
            │
            ▼
Agent reasons over all findings
            │
            ▼
DECISION: RETRY_LATER — DHL has a confirmed active incident,
          UPS is available as alternative,
          no refund issued yet, low-risk customer.
          Recommended action: switch carrier or wait 30 min.
```

The agent loop runs until it has enough information to commit to a decision, or until it reaches a maximum number of steps.

---

## Long-Term Memory — The Vector Layer

Every time the agent resolves a failure, the full context of that case is converted into a numerical vector and saved to a CSV file. This vector captures everything relevant about the situation:

- Which step failed and what type of error occurred
- How many attempts had already been made
- Whether the external system had an active incident
- The customer's fraud score and return rate
- The financial risk (order value, whether a refund was already issued)
- The temporal context (time of day, weekend or not, international shipment)
- The decision taken and whether it worked
- How long it took to resolve

Over time, as hundreds and then thousands of cases accumulate, the system gains a memory. When a new failure arrives, instead of always triggering the full LLM agent, the system can first search for similar past cases using a simple **KNN (K-Nearest Neighbors)** algorithm. If the closest historical cases are sufficiently similar and consistently led to the same decision with a high success rate, the system can act directly — no LLM call needed.

```
New failure arrives
        │
        ▼
Convert context to vector
        │
        ▼
Search for K most similar cases in history
        │
        ├── High similarity + clear majority decision
        │         └── Act directly (KNN decides, no LLM needed)
        │
        └── Low similarity or ambiguous cases
                  └── Trigger full LLM agent
                            └── Save result as new vector
```

The more failures the system processes, the more accurate and autonomous it becomes. The LLM handles the unknown cases. The KNN handles the ones it has seen before.

---

## What This Prototype Includes

The project is intentionally simple — the goal is to demonstrate the concept clearly, not to build production infrastructure.

**Simulated objects** — workflows, customers, products, and carriers are defined as Python classes with hardcoded data. The parameters used (fraud scores, carrier statuses, order values) are assumed values built to represent realistic scenarios, not real REVER data. Two contrasting scenarios are included: a carrier outage causing repeated 503 errors, and a fraud detection case that should always escalate.

**Tools** — the agent has access to a set of tools that simulate API calls to Temporal, the carrier network, the ecommerce platform, the customer database, and the payment gateway. Each tool returns a realistic JSON response based on the hardcoded objects.

**LLM** — the prototype uses a small local model (Qwen2.5-1.5B-Instruct) for inference. This model is lightweight and runs without GPU, which makes the prototype portable. In a real deployment, replacing this with a capable model via API (Claude, GPT-4, etc.) would dramatically improve the quality of reasoning, the reliability of tool calling, and the accuracy of decisions. The architecture is model-agnostic — swapping the inference layer requires changing one file.

**Vectorizer** — after each decision, the full context is converted to a 37-dimensional numerical vector and appended to a CSV file. Each dimension is documented in `vect/vect_definition.txt`.

---

## Project Structure

```
test_rever_agent/
├── main.py                        ← entry point, run with --scenario or --workflow
├── Taskfile.yml                   ← task runner shortcuts (install, run, download model)
├── requirements.txt               ← Python dependencies
├── objects/
│   ├── workflow.py                ← workflow objects with execution state and history
│   ├── customer.py                ← customer profiles (low-risk and high-risk)
│   ├── product.py                 ← product objects
│   ├── carrier.py                 ← carrier objects (DHL degraded, UPS operational)
│   └── knowledge_base.py          ← all 9 workflow steps and 52 error definitions
├── agent/
│   ├── llm/
│   │   ├── download.py            ← downloads Qwen2.5-1.5B-Instruct locally
│   │   ├── inference.py           ← LLM loop with tool calling (ReAct pattern)
│   │   └── models/                ← not included in repo, generated by download.py
│   └── tools/
│       ├── temporal_tools.py      ← workflow state, history, current step
│       ├── knowledge_tools.py     ← step definitions, error definitions
│       ├── carrier_tools.py       ← carrier status, available alternatives
│       ├── customer_tools.py      ← customer profile, return history, order details
│       └── payment_tools.py       ← payment status, refund status
└── vect/
    ├── vectorizer.py              ← converts a resolved case to a vector and saves to CSV
    ├── vect_definition.txt        ← human-readable definition of each vector field
    └── decisions.csv              ← grows with every resolved case
```

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Download the local model (only needed once)
python agent/llm/download.py

# Run scenario 1 — DHL carrier outage, clean customer
python main.py --scenario SCENARIO_1

# Run scenario 2 — Fraud detected, high-risk customer
python main.py --scenario SCENARIO_2
```

---

## What This Is Not

This is a proof of concept. The tools return simulated data, the objects have assumed parameters, and the LLM used is intentionally small. The real value of this idea scales with:

- **More tools** — real Temporal API integration, live carrier status pages, real fraud scoring systems, warehouse management APIs
- **More scenarios** — the full 9-step workflow, edge cases, international returns, customs failures
- **A better model** — a capable LLM via API makes tool calling dramatically more reliable and the reasoning significantly sharper
- **Volume** — the KNN layer only becomes meaningful with hundreds of real resolved cases, where true patterns emerge from production data

The architecture is designed to support all of this. The concept is what matters here.