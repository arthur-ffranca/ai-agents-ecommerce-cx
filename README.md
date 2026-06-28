# AI Agents for E-commerce CX

Policy-based multi-agent customer experience automation for e-commerce support workflows.

This project automates repetitive support requests such as order tracking, returns, exchanges, refunds, CRM updates, and human handoff. It is structured around a deterministic policy engine, workflow orchestration, mocked business tools, and a working chat frontend.

## Current MVP

The current implementation includes:

- a FastAPI backend;
- a built-in chat frontend served from `/`;
- intent routing for WISMO, returns, refunds, exchanges, and human handoff;
- deterministic policy evaluation from `app/policies/rules.yaml`;
- mocked Shopify, Stripe, CRM, and shipping integrations;
- workflow execution for tracking, refund approval, refund processing, and handoff;
- tests covering the main workflows;
- Render deployment configuration in `render.yaml`.

## Run Locally

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open the chat frontend:

```text
http://127.0.0.1:8000/
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Example API Request

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"customer_id\":\"cus_123\",\"order_id\":\"ord_1001\",\"message\":\"I want a refund\"}"
```

## Architecture

```text
Customer message
  -> RouterAgent
  -> WorkflowEngine
  -> PolicyEngine
  -> Mocked tools
  -> Customer reply
```

The `/chat` endpoint accepts an optional `intent`. A UI can send a selected request type, or the RouterAgent can infer it from the customer message.

## Supported Workflows

- `wismo`: checks Shopify order data and shipping status.
- `return_request`: checks return eligibility against policy rules.
- `refund_request`: evaluates refund policy, processes low-value refunds, and creates approval tickets for high-value refunds.
- `exchange_request`: creates an exchange ticket placeholder for human review.
- `human_handoff`: creates a CRM ticket when the user asks for a person, frustration is detected, or confidence is low.

## Policy Rules

Initial policy rules are stored in `app/policies/rules.yaml`.

Current examples:

- returns allowed within 30 days;
- refunds under `$50` can be automatic;
- refunds above `$50` require manager approval;
- human handoff is triggered by explicit user request, frustration signal, or complex case.

## Deploy on Render

This repo includes `render.yaml` for a single Render web service.

```text
Build command: pip install -r requirements.txt
Start command: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health check: /health
```

## Repository Structure

```text
app/
  agents/
  policies/
  static/
  tools/
  workflows/
diagrams/
docs/
slides/
tests/
render.yaml
requirements.txt
```

## Roadmap

- Add persistent conversation and audit logs.
- Add real Shopify, Stripe, CRM, and shipping integrations.
- Add authentication and tenant-aware configuration.
- Add human approval queue for manager-reviewed refunds.
- Add RAG over policy documents and FAQs.
- Add analytics for automation rate, handoff rate, latency, and CSAT.

## Disclaimer

This MVP uses mocked business tools. Any production implementation should include proper authentication, API permissions, logging, data privacy controls, rate limits, idempotency keys, and human approval for sensitive actions such as refunds and customer data access.
