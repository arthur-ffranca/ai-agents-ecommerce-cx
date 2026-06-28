from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    customer_id: str
    order_id: str | None
    status: str
    priority: str
    reason: str
    notes: list[str] = field(default_factory=list)


class CRMTool:
    def __init__(self) -> None:
        self.tickets: dict[str, Ticket] = {}

    def create_ticket(
        self,
        customer_id: str,
        reason: str,
        priority: str = "normal",
        order_id: str | None = None,
        notes: list[str] | None = None,
    ) -> Ticket:
        ticket_id = f"tkt_{uuid4().hex[:8]}"
        timestamp = datetime.now(UTC).isoformat()
        ticket_notes = [f"{timestamp}: {note}" for note in notes or []]
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_id=customer_id,
            order_id=order_id,
            status="open",
            priority=priority,
            reason=reason,
            notes=ticket_notes,
        )
        self.tickets[ticket_id] = ticket
        return ticket

    def add_note(self, ticket_id: str, note: str) -> Ticket | None:
        ticket = self.tickets.get(ticket_id)
        if ticket is None:
            return None

        timestamp = datetime.now(UTC).isoformat()
        updated_ticket = Ticket(
            ticket_id=ticket.ticket_id,
            customer_id=ticket.customer_id,
            order_id=ticket.order_id,
            status=ticket.status,
            priority=ticket.priority,
            reason=ticket.reason,
            notes=[*ticket.notes, f"{timestamp}: {note}"],
        )
        self.tickets[ticket_id] = updated_ticket
        return updated_ticket
