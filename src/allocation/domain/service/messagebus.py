from typing import Callable, Dict, List, Type

from src.allocation.adapters import email
from src.allocation.domain.model import events


def send_out_of_stock_notification(event: events.OutOfStock) -> None:
    email.send_mail(
        "stock@made.com",
        f"Out of stock for {event.sku}",
    )


_EVENT_HANDLERS: Dict[Type[events.Event], List[Callable[..., None]]] = {
    events.OutOfStock: [send_out_of_stock_notification],
}


def handle(event: events.Event) -> None:
    for handler in _EVENT_HANDLERS[type(event)]:
        handler(event)
