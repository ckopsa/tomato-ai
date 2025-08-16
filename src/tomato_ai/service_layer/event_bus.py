from collections import defaultdict
from typing import Callable, Dict, List, Type

from tomato_ai.domain import events

HANDLERS = defaultdict(list)  # type: Dict[Type[events.Event], List[Callable]]


def register(event_type: Type[events.Event], handler: Callable):
    """
    Registers a handler for a given event type.
    """
    HANDLERS[event_type].append(handler)


def publish(event: events.Event):
    """
    Publishes an event to all registered handlers.
    """
    for handler in HANDLERS[type(event)]:
        handler(event)
