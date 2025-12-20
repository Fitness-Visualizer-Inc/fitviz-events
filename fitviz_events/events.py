"""Event schema definitions for FitViz domain events."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseEvent(BaseModel):
    """Base event schema for all FitViz events."""

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    )

    event_id: Optional[str] = None
    event_type: str
    organization_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]


class WorkoutCreatedEvent(BaseEvent):
    """Event emitted when a workout is created."""

    event_type: str = "workout.created"

    class WorkoutData(BaseModel):
        workout_id: str
        title: str
        description: Optional[str] = None
        duration_minutes: Optional[int] = None
        created_by: str

    data: WorkoutData


class WorkoutUpdatedEvent(BaseEvent):
    """Event emitted when a workout is updated."""

    event_type: str = "workout.updated"

    class WorkoutData(BaseModel):
        workout_id: str
        title: Optional[str] = None
        description: Optional[str] = None
        duration_minutes: Optional[int] = None
        updated_by: str

    data: WorkoutData


class WorkoutDeletedEvent(BaseEvent):
    """Event emitted when a workout is deleted."""

    event_type: str = "workout.deleted"

    class WorkoutData(BaseModel):
        workout_id: str
        deleted_by: str

    data: WorkoutData


class BookingCreatedEvent(BaseEvent):
    """Event emitted when a booking is created."""

    event_type: str = "booking.created"

    class BookingData(BaseModel):
        booking_id: str
        user_id: str
        class_id: str
        class_name: str
        scheduled_time: Optional[datetime] = None
        location: Optional[str] = None

    data: BookingData


class BookingConfirmedEvent(BaseEvent):
    """Event emitted when a booking is confirmed."""

    event_type: str = "booking.confirmed"

    class BookingData(BaseModel):
        booking_id: str
        user_id: str
        class_id: str
        class_name: str
        scheduled_time: datetime
        location: Optional[str] = None

    data: BookingData


class BookingCancelledEvent(BaseEvent):
    """Event emitted when a booking is cancelled."""

    event_type: str = "booking.cancelled"

    class BookingData(BaseModel):
        booking_id: str
        user_id: str
        class_id: str
        class_name: str
        cancellation_reason: Optional[str] = None

    data: BookingData


class MembershipCreatedEvent(BaseEvent):
    """Event emitted when a membership is created."""

    event_type: str = "membership.created"

    class MembershipData(BaseModel):
        membership_id: str
        user_id: str
        plan_name: str
        start_date: datetime
        end_date: datetime
        price: float

    data: MembershipData


class MembershipExpiredEvent(BaseEvent):
    """Event emitted when a membership expires."""

    event_type: str = "membership.expired"

    class MembershipData(BaseModel):
        membership_id: str
        user_id: str
        plan_name: str
        expired_date: datetime

    data: MembershipData


class PaymentCompletedEvent(BaseEvent):
    """Event emitted when a payment is completed."""

    event_type: str = "payment.completed"

    class PaymentData(BaseModel):
        payment_id: str
        user_id: str
        amount: float
        currency: str = "USD"
        payment_method: str
        reference_type: str
        reference_id: str

    data: PaymentData


class PaymentFailedEvent(BaseEvent):
    """Event emitted when a payment fails."""

    event_type: str = "payment.failed"

    class PaymentData(BaseModel):
        payment_id: str
        user_id: str
        amount: float
        currency: str = "USD"
        failure_reason: str
        reference_type: str
        reference_id: str

    data: PaymentData


class ClassScheduledEvent(BaseEvent):
    """Event emitted when a class is scheduled."""

    event_type: str = "class.scheduled"

    class ClassData(BaseModel):
        class_id: str
        class_name: str
        trainer_id: str
        trainer_name: str
        scheduled_time: datetime
        duration_minutes: int
        location: str
        capacity: int

    data: ClassData


class ClassCreatedEvent(BaseEvent):
    """Event emitted when a class is created."""

    event_type: str = "class.created"

    class ClassData(BaseModel):
        class_id: str
        class_name: str
        trainer_id: str
        max_slots: Optional[int] = None
        price: Optional[float] = None
        created_by: str
        occurrence_count: Optional[int] = None

    data: ClassData


class ClassUpdatedEvent(BaseEvent):
    """Event emitted when a class is updated."""

    event_type: str = "class.updated"

    class ClassData(BaseModel):
        class_id: str
        class_name: str
        changes: Optional[Dict[str, Any]] = None
        updated_by: str

    data: ClassData


class ClassCancelledEvent(BaseEvent):
    """Event emitted when a class is cancelled."""

    event_type: str = "class.cancelled"

    class ClassData(BaseModel):
        class_id: str
        class_name: str
        scheduled_time: datetime
        cancellation_reason: str
        affected_users: list[str] = Field(default_factory=list)

    data: ClassData


EVENT_TYPE_MAP = {
    "workout.created": WorkoutCreatedEvent,
    "workout.updated": WorkoutUpdatedEvent,
    "workout.deleted": WorkoutDeletedEvent,
    "booking.created": BookingCreatedEvent,
    "booking.confirmed": BookingConfirmedEvent,
    "booking.cancelled": BookingCancelledEvent,
    "membership.created": MembershipCreatedEvent,
    "membership.expired": MembershipExpiredEvent,
    "payment.completed": PaymentCompletedEvent,
    "payment.failed": PaymentFailedEvent,
    "class.created": ClassCreatedEvent,
    "class.updated": ClassUpdatedEvent,
    "class.scheduled": ClassScheduledEvent,
    "class.cancelled": ClassCancelledEvent,
}
