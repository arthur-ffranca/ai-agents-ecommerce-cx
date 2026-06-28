from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouteResult:
    intent: str
    urgency: str
    frustration_detected: bool
    user_requested_human: bool
    confidence: float


class RouterAgent:
    def route(self, message: str) -> RouteResult:
        normalized_message = message.lower()

        user_requested_human = self._contains_any(
            normalized_message,
            [
                "human",
                "person",
                "agent",
                "manager",
                "support",
                "attendant",
                "representative",
            ],
        )
        frustration_detected = self._contains_any(
            normalized_message,
            [
                "angry",
                "frustrated",
                "terrible",
                "awful",
                "unacceptable",
                "ridiculous",
                "mad",
            ],
        )
        urgency = "high" if self._contains_any(normalized_message, ["urgent", "asap", "now"]) else "normal"

        if user_requested_human:
            return RouteResult(
                intent="human_handoff",
                urgency=urgency,
                frustration_detected=frustration_detected,
                user_requested_human=True,
                confidence=0.95,
            )

        if self._contains_any(normalized_message, ["where is my order", "track", "tracking", "delivery", "delivered"]):
            return RouteResult(
                intent="wismo",
                urgency=urgency,
                frustration_detected=frustration_detected,
                user_requested_human=False,
                confidence=0.90,
            )

        if self._contains_any(normalized_message, ["return", "send back"]):
            return RouteResult(
                intent="return_request",
                urgency=urgency,
                frustration_detected=frustration_detected,
                user_requested_human=False,
                confidence=0.88,
            )

        if self._contains_any(normalized_message, ["refund", "money back", "reimburse"]):
            return RouteResult(
                intent="refund_request",
                urgency=urgency,
                frustration_detected=frustration_detected,
                user_requested_human=False,
                confidence=0.88,
            )

        if self._contains_any(normalized_message, ["exchange", "replace", "different size", "different color"]):
            return RouteResult(
                intent="exchange_request",
                urgency=urgency,
                frustration_detected=frustration_detected,
                user_requested_human=False,
                confidence=0.86,
            )

        return RouteResult(
            intent="unknown",
            urgency=urgency,
            frustration_detected=frustration_detected,
            user_requested_human=False,
            confidence=0.20,
        )

    def _contains_any(self, text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)
