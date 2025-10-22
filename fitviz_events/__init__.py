"""
FitViz Events - Event publishing client for FitViz notification service.

This package provides a simple interface for Flask applications to publish
domain events to the FitViz notification service via RabbitMQ.
"""

from fitviz_events.config import EventPublisherConfig
from fitviz_events.events import (
    BaseEvent,
    BookingCancelledEvent,
    BookingConfirmedEvent,
    ClassCancelledEvent,
    ClassScheduledEvent,
    MembershipCreatedEvent,
    MembershipExpiredEvent,
    PaymentCompletedEvent,
    PaymentFailedEvent,
    WorkoutCreatedEvent,
    WorkoutDeletedEvent,
    WorkoutUpdatedEvent,
)
from fitviz_events.exceptions import (
    ConnectionError,
    EventPublishError,
    EventValidationError,
)
from fitviz_events.publisher import EventPublisher

__version__ = "1.0.0"
__all__ = [
    "EventPublisher",
    "EventPublisherConfig",
    "BaseEvent",
    "WorkoutCreatedEvent",
    "WorkoutUpdatedEvent",
    "WorkoutDeletedEvent",
    "BookingConfirmedEvent",
    "BookingCancelledEvent",
    "MembershipCreatedEvent",
    "MembershipExpiredEvent",
    "PaymentCompletedEvent",
    "PaymentFailedEvent",
    "ClassScheduledEvent",
    "ClassCancelledEvent",
    "EventPublishError",
    "EventValidationError",
    "ConnectionError",
]
