from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PolicyDecision:
    decision: str
    reason: str
    requires_human: bool = False


class PolicyEngine:
    def __init__(self, rules_path: str | Path) -> None:
        self.rules_path = Path(rules_path)
        self.rules = self._load_rules()

    def evaluate_return(self, order: dict[str, Any]) -> PolicyDecision:
        return_policy = self.rules["return_policy"]
        return_window_days = return_policy["return_window_days"]

        if return_policy["requires_order_delivered"] and order.get("status") != "delivered":
            return PolicyDecision(
                decision="denied",
                reason="Order must be delivered before a return can be started.",
            )

        if order.get("days_since_purchase", 0) > return_window_days:
            return PolicyDecision(
                decision="denied",
                reason=f"Return window exceeded. Limit is {return_window_days} days.",
            )

        return PolicyDecision(
            decision="eligible",
            reason="Order is eligible for return.",
        )

    def evaluate_refund(self, order: dict[str, Any], refund_amount_usd: float) -> PolicyDecision:
        refund_policy = self.rules["refund_policy"]
        automatic_limit = refund_policy["automatic_refund_limit_usd"]

        if refund_policy["requires_payment_confirmed"] and order.get("payment_status") != "paid":
            return PolicyDecision(
                decision="denied",
                reason="Payment must be confirmed before refund.",
            )

        if refund_amount_usd > automatic_limit:
            return PolicyDecision(
                decision="requires_approval",
                reason=f"Refund amount exceeds automatic limit of ${automatic_limit}.",
                requires_human=refund_policy["above_limit_requires_manager_approval"],
            )

        return PolicyDecision(
            decision="approved",
            reason="Refund is within automatic approval limit.",
        )

    def evaluate_handoff(self, message_analysis: dict[str, Any]) -> PolicyDecision:
        handoff_policy = self.rules["handoff_policy"]

        if handoff_policy["user_requested"] and message_analysis.get("user_requested_human"):
            return PolicyDecision(
                decision="handoff_required",
                reason="User requested human support.",
                requires_human=True,
            )

        frustration_detected = message_analysis.get("frustration_detected") or message_analysis.get("anger_detected")
        if handoff_policy["anger_detected"] and frustration_detected:
            return PolicyDecision(
                decision="handoff_required",
                reason="Customer frustration signal detected.",
                requires_human=True,
            )

        if handoff_policy["complex_case"] and message_analysis.get("complex_case"):
            return PolicyDecision(
                decision="handoff_required",
                reason="Case is marked as complex.",
                requires_human=True,
            )

        return PolicyDecision(
            decision="no_handoff_required",
            reason="No handoff rule was triggered.",
        )

    def _load_rules(self) -> dict[str, Any]:
        with self.rules_path.open("r", encoding="utf-8") as rules_file:
            return yaml.safe_load(rules_file)
