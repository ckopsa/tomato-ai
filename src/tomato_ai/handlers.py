import logging

from tomato_ai.domain import events

logger = logging.getLogger(__name__)

def log_event(event: events.Event):
    """
    A simple event handler that logs the event.
    """
    logger.info(f"Handled event: {event}")
