from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4


@dataclass(frozen=True)
class RefundResult:
    refund_id: str
    order_id: str
    amount_usd: float
    status: str
    created_at: str


class StripeTool:
    def __init__(self) -> None:
        self.refunds: dict[str, RefundResult] = {}

    def create_refund(self, order_id: str, amount_usd: float) -> RefundResult:
        refund_id = f"rfnd_{uuid4().hex[:8]}"
        refund = RefundResult(
            refund_id=refund_id,
            order_id=order_id,
            amount_usd=amount_usd,
            status="succeeded",
            created_at=datetime.now(UTC).isoformat(),
        )
        self.refunds[refund_id] = refund
        return refund
