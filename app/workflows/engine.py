from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.agents.router import RouterAgent
from app.policies.engine import PolicyEngine
from app.tools.crm import CRMTool
from app.tools.shipping import ShippingTool
from app.tools.shopify import Order, ShopifyTool
from app.tools.stripe import StripeTool


@dataclass(frozen=True)
class WorkflowRequest:
    customer_id: str
    message: str
    order_id: str | None = None
    intent: str | None = None


@dataclass(frozen=True)
class WorkflowResult:
    intent: str
    workflow: str
    status: str
    reply: str
    data: dict[str, Any]


class WorkflowEngine:
    def __init__(
        self,
        router: RouterAgent,
        policy_engine: PolicyEngine,
        shopify: ShopifyTool,
        shipping: ShippingTool,
        crm: CRMTool,
        stripe: StripeTool,
    ) -> None:
        self.router = router
        self.policy_engine = policy_engine
        self.shopify = shopify
        self.shipping = shipping
        self.crm = crm
        self.stripe = stripe

    def handle(self, request: WorkflowRequest) -> WorkflowResult:
        route = self.router.route(request.message)
        intent = request.intent or route.intent

        handoff_decision = self.policy_engine.evaluate_handoff(
            {
                "user_requested_human": route.user_requested_human,
                "frustration_detected": route.frustration_detected,
                "complex_case": route.confidence < 0.5,
            }
        )
        if handoff_decision.requires_human:
            return self._handle_handoff(request, intent, handoff_decision.reason)

        if intent == "wismo":
            return self._handle_wismo(request)
        if intent == "return_request":
            return self._handle_return(request)
        if intent == "refund_request":
            return self._handle_refund(request)
        if intent == "exchange_request":
            return self._handle_exchange(request)

        return self._handle_handoff(request, intent, "Unable to classify the customer request with enough confidence.")

    def _handle_wismo(self, request: WorkflowRequest) -> WorkflowResult:
        order = self._get_order(request)
        if order is None:
            return self._order_not_found("wismo")

        if order.tracking_number is None:
            return WorkflowResult(
                intent="wismo",
                workflow="wismo",
                status="missing_tracking",
                reply="I found your order, but there is no tracking number available yet.",
                data={"order_id": order.order_id},
            )

        tracking = self.shipping.get_tracking_status(order.tracking_number)
        if tracking is None:
            return WorkflowResult(
                intent="wismo",
                workflow="wismo",
                status="tracking_not_found",
                reply="I found your order, but I could not retrieve the carrier tracking status yet.",
                data={"order_id": order.order_id, "tracking_number": order.tracking_number},
            )

        if tracking.status == "delivered":
            reply = "Your order has been delivered. The latest carrier update says: Package was delivered to the customer."
        else:
            reply = (
                f"Your order is currently {tracking.status}. "
                f"Estimated delivery date: {tracking.estimated_delivery_date}. "
                f"Latest update: {tracking.latest_event}"
            )

        return WorkflowResult(
            intent="wismo",
            workflow="wismo",
            status="resolved",
            reply=reply,
            data={"order": asdict(order), "tracking": asdict(tracking)},
        )

    def _handle_return(self, request: WorkflowRequest) -> WorkflowResult:
        order = self._get_order(request)
        if order is None:
            return self._order_not_found("return_request")

        decision = self.policy_engine.evaluate_return(asdict(order))
        status = "resolved" if decision.decision == "eligible" else "denied"
        reply = (
            "Your order is eligible for return. I can start the return workflow for this order."
            if decision.decision == "eligible"
            else f"I cannot start a return for this order. Reason: {decision.reason}"
        )

        return WorkflowResult(
            intent="return_request",
            workflow="return_request",
            status=status,
            reply=reply,
            data={"order": asdict(order), "policy_decision": asdict(decision)},
        )

    def _handle_refund(self, request: WorkflowRequest) -> WorkflowResult:
        order = self._get_order(request)
        if order is None:
            return self._order_not_found("refund_request")

        decision = self.policy_engine.evaluate_refund(asdict(order), order.total_usd)
        if decision.decision == "approved":
            refund = self.stripe.create_refund(order.order_id, order.total_usd)
            return WorkflowResult(
                intent="refund_request",
                workflow="refund_request",
                status="resolved",
                reply=f"Your refund of ${order.total_usd:.2f} has been approved and processed.",
                data={"order": asdict(order), "policy_decision": asdict(decision), "refund": asdict(refund)},
            )

        if decision.requires_human:
            ticket = self.crm.create_ticket(
                customer_id=request.customer_id,
                order_id=order.order_id,
                reason="refund_requires_approval",
                priority="high",
                notes=[decision.reason],
            )
            return WorkflowResult(
                intent="refund_request",
                workflow="refund_request",
                status="requires_approval",
                reply="This refund requires manager approval. I created a support ticket for review.",
                data={"order": asdict(order), "policy_decision": asdict(decision), "ticket": asdict(ticket)},
            )

        return WorkflowResult(
            intent="refund_request",
            workflow="refund_request",
            status="denied",
            reply=f"I cannot process this refund. Reason: {decision.reason}",
            data={"order": asdict(order), "policy_decision": asdict(decision)},
        )

    def _handle_exchange(self, request: WorkflowRequest) -> WorkflowResult:
        order = self._get_order(request)
        if order is None:
            return self._order_not_found("exchange_request")

        ticket = self.crm.create_ticket(
            customer_id=request.customer_id,
            order_id=order.order_id,
            reason="exchange_request",
            priority="normal",
            notes=["Exchange workflow placeholder created for MVP."],
        )
        return WorkflowResult(
            intent="exchange_request",
            workflow="exchange_request",
            status="ticket_created",
            reply="I created an exchange request ticket. A support specialist will review inventory and eligibility.",
            data={"order": asdict(order), "ticket": asdict(ticket)},
        )

    def _handle_handoff(self, request: WorkflowRequest, intent: str, reason: str) -> WorkflowResult:
        ticket = self.crm.create_ticket(
            customer_id=request.customer_id,
            order_id=request.order_id,
            reason="human_handoff",
            priority="high",
            notes=[f"Detected intent: {intent}", reason, f"Customer message: {request.message}"],
        )
        return WorkflowResult(
            intent=intent,
            workflow="human_handoff",
            status="handoff_created",
            reply="I'm connecting you with a support specialist who can help with this case.",
            data={"ticket": asdict(ticket), "handoff_reason": reason},
        )

    def _get_order(self, request: WorkflowRequest) -> Order | None:
        if request.order_id:
            return self.shopify.get_order(request.order_id)

        return self.shopify.get_latest_order_for_customer(request.customer_id)

    def _order_not_found(self, intent: str) -> WorkflowResult:
        return WorkflowResult(
            intent=intent,
            workflow=intent,
            status="order_not_found",
            reply="I could not find an order for this request. I need a valid order ID to continue.",
            data={},
        )
