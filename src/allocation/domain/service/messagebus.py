from typing import Any, Callable, Coroutine, Dict, List, Type

from src.allocation.domain.model import events
from src.allocation.domain.service import handlers, unit_of_work
from src.allocation.lib import base_types

_EVENT_HANDLERS: Dict[
    Type[base_types.Event],
    List[Callable[..., Coroutine[Any, Any, Any]]],
] = {
    events.BatchCreated: [handlers.add_batch],
    events.AllocationRequired: [handlers.allocate],
    events.BatchQuantityChanged: [handlers.change_batch_quantity],
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}


async def handle(
    event: base_types.Event, uow: unit_of_work.AbstractUnitOfWork
) -> List[Any]:
    results: List[Any] = []
    queue: List[base_types.Event] = [event]
    while queue:
        event = queue.pop()
        for handler in _EVENT_HANDLERS[type(event)]:
            results.append(await handler(event=event, uow=uow))
            queue.extend(uow.collect_new_events())
    return results
