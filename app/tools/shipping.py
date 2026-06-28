from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrackingStatus:
    tracking_number: str
    status: str
    estimated_delivery_date: str | None
    latest_event: str


class ShippingTool:
    def __init__(self) -> None:
        self.tracking_statuses = {
            "TRK-1001": TrackingStatus(
                tracking_number="TRK-1001",
                status="delivered",
                estimated_delivery_date=None,
                latest_event="Package was delivered to the customer.",
            ),
            "TRK-1002": TrackingStatus(
                tracking_number="TRK-1002",
                status="delivered",
                estimated_delivery_date=None,
                latest_event="Package was delivered to the customer.",
            ),
            "TRK-1003": TrackingStatus(
                tracking_number="TRK-1003",
                status="in_transit",
                estimated_delivery_date="2026-07-01",
                latest_event="Package departed the regional carrier facility.",
            ),
        }

    def get_tracking_status(self, tracking_number: str) -> TrackingStatus | None:
        return self.tracking_statuses.get(tracking_number)
