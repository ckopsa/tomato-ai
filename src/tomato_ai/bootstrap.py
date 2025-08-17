from tomato_ai.domain import events
from tomato_ai.adapters import event_bus
from tomato_ai import handlers

def bootstrap():
    """
    Initializes the application by registering event handlers.
    """
    event_bus.register(events.SessionStarted, handlers.log_event)
    event_bus.register(events.SessionCompleted, handlers.log_event)
    event_bus.register(events.SessionPaused, handlers.log_event)
    event_bus.register(events.SessionResumed, handlers.log_event)
    event_bus.register(events.SessionExpired, handlers.log_event)
    event_bus.register(events.SessionCompleted, handlers.send_telegram_notification)
    event_bus.register(events.SessionStarted, handlers.send_telegram_notification_on_start)
    event_bus.register(events.SessionExpired, handlers.send_telegram_notification_on_expiration)
