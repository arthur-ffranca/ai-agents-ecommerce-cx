# AI Agents for E-commerce CX

Policy-based multi-agent CX automation for e-commerce support workflows.

## Current MVP

The backend supports:

- intent routing for WISMO, returns, refunds, exchanges, and human handoff;
- deterministic policy evaluation from `app/policies/rules.yaml`;
- mocked Shopify, Stripe, CRM, and shipping integrations;
- a FastAPI service with `GET /health` and `POST /chat`;
- a built-in chat frontend served from `/`.

## Run Locally

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/
```

API docs are available at:

```text
http://127.0.0.1:8000/docs
```

## Deploy on Render

This repo includes `render.yaml` for a single Render web service.

```text
Build command: pip install -r requirements.txt
Start command: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health check: /health
```

## Example Request

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"customer_id\":\"cus_123\",\"order_id\":\"ord_1001\",\"message\":\"I want a refund\"}"
```

## Architecture

```text
User message
  -> RouterAgent
  -> WorkflowEngine
  -> PolicyEngine
  -> Mocked tools
  -> Customer reply
```

`intent` is optional in `/chat`. A UI can send a selected intent, or the RouterAgent can infer it from the message.
