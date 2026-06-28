from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrderItem:
    sku: str
    name: str
    category: str
    quantity: int
    unit_price_usd: float


@dataclass(frozen=True)
class Order:
    order_id: str
    customer_id: str
    status: str
    fulfillment_status: str
    payment_status: str
    days_since_purchase: int
    total_usd: float
    tracking_number: str | None
    items: list[OrderItem]


class ShopifyTool:
    def __init__(self) -> None:
        self.orders = {
            "ord_1001": Order(
                order_id="ord_1001",
                customer_id="cus_123",
                status="delivered",
                fulfillment_status="fulfilled",
                payment_status="paid",
                days_since_purchase=12,
                total_usd=35.00,
                tracking_number="TRK-1001",
                items=[
                    OrderItem(
                        sku="shirt-blue-m",
                        name="Blue Shirt",
                        category="apparel",
                        quantity=1,
                        unit_price_usd=35.00,
                    )
                ],
            ),
            "ord_1002": Order(
                order_id="ord_1002",
                customer_id="cus_456",
                status="delivered",
                fulfillment_status="fulfilled",
                payment_status="paid",
                days_since_purchase=8,
                total_usd=120.00,
                tracking_number="TRK-1002",
                items=[
                    OrderItem(
                        sku="jacket-black-l",
                        name="Black Jacket",
                        category="apparel",
                        quantity=1,
                        unit_price_usd=120.00,
                    )
                ],
            ),
            "ord_1003": Order(
                order_id="ord_1003",
                customer_id="cus_789",
                status="in_transit",
                fulfillment_status="shipped",
                payment_status="paid",
                days_since_purchase=3,
                total_usd=64.00,
                tracking_number="TRK-1003",
                items=[
                    OrderItem(
                        sku="mug-white",
                        name="White Mug",
                        category="home",
                        quantity=2,
                        unit_price_usd=32.00,
                    )
                ],
            ),
        }

    def get_order(self, order_id: str) -> Order | None:
        return self.orders.get(order_id)

    def get_latest_order_for_customer(self, customer_id: str) -> Order | None:
        customer_orders = [order for order in self.orders.values() if order.customer_id == customer_id]
        if not customer_orders:
            return None

        return min(customer_orders, key=lambda order: order.days_since_purchase)
