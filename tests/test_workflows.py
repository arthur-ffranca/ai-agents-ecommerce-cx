from app.agents.router import RouterAgent
from app.policies.engine import PolicyEngine
from app.tools.crm import CRMTool
from app.tools.shipping import ShippingTool
from app.tools.shopify import ShopifyTool
from app.tools.stripe import StripeTool
from app.workflows.engine import WorkflowEngine, WorkflowRequest


def build_engine() -> WorkflowEngine:
    return WorkflowEngine(
        router=RouterAgent(),
        policy_engine=PolicyEngine("app/policies/rules.yaml"),
        shopify=ShopifyTool(),
        shipping=ShippingTool(),
        crm=CRMTool(),
        stripe=StripeTool(),
    )


def test_wismo_flow_returns_tracking_status() -> None:
    result = build_engine().handle(
        WorkflowRequest(customer_id="cus_789", order_id="ord_1003", message="Where is my order?")
    )

    assert result.intent == "wismo"
    assert result.workflow == "wismo"
    assert result.status == "resolved"


def test_low_value_refund_is_processed() -> None:
    result = build_engine().handle(
        WorkflowRequest(customer_id="cus_123", order_id="ord_1001", message="I want a refund")
    )

    assert result.intent == "refund_request"
    assert result.status == "resolved"
    assert result.data["refund"]["status"] == "succeeded"


def test_high_value_refund_requires_approval() -> None:
    result = build_engine().handle(
        WorkflowRequest(customer_id="cus_456", order_id="ord_1002", message="I want a refund")
    )

    assert result.intent == "refund_request"
    assert result.status == "requires_approval"
    assert result.data["ticket"]["reason"] == "refund_requires_approval"


def test_frustration_and_human_request_create_handoff() -> None:
    result = build_engine().handle(
        WorkflowRequest(
            customer_id="cus_123",
            order_id="ord_1001",
            message="This is unacceptable, I want a human now",
        )
    )

    assert result.intent == "human_handoff"
    assert result.workflow == "human_handoff"
    assert result.status == "handoff_created"
