from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.agents.router import RouterAgent
from app.policies.engine import PolicyEngine
from app.tools.crm import CRMTool
from app.tools.shipping import ShippingTool
from app.tools.shopify import ShopifyTool
from app.tools.stripe import StripeTool
from app.workflows.engine import WorkflowEngine, WorkflowRequest


class ChatRequest(BaseModel):
    customer_id: str = Field(..., examples=["cus_123"])
    message: str = Field(..., examples=["I want a refund"])
    order_id: str | None = Field(default=None, examples=["ord_1001"])
    intent: str | None = Field(default=None, examples=["refund_request"])


class ChatResponse(BaseModel):
    intent: str
    workflow: str
    status: str
    reply: str
    data: dict[str, Any]


def build_workflow_engine() -> WorkflowEngine:
    rules_path = Path(__file__).resolve().parent / "policies" / "rules.yaml"
    return WorkflowEngine(
        router=RouterAgent(),
        policy_engine=PolicyEngine(rules_path),
        shopify=ShopifyTool(),
        shipping=ShippingTool(),
        crm=CRMTool(),
        stripe=StripeTool(),
    )


app = FastAPI(
    title="AI Agents for E-commerce CX",
    version="0.1.0",
    description="Policy-based multi-agent CX automation for e-commerce support workflows.",
)
workflow_engine = build_workflow_engine()
app_dir = Path(__file__).resolve().parent
static_dir = app_dir / "static"
project_root = app_dir.parent

app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/project-assets", StaticFiles(directory=project_root / "diagrams"), name="project-assets")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    result = workflow_engine.handle(
        WorkflowRequest(
            customer_id=request.customer_id,
            message=request.message,
            order_id=request.order_id,
            intent=request.intent,
        )
    )
    return ChatResponse(**asdict(result))
