"""Event schemas for fitviz-events library."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class BaseEvent(BaseModel):
    """Base event schema for all FitViz events."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    organization_id: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Ensure event_type is not empty."""
        if not v or not v.strip():
            raise ValueError("event_type cannot be empty")
        return v

    @field_validator("organization_id")
    @classmethod
    def validate_organization_id(cls, v: str) -> str:
        """Ensure organization_id is not empty."""
        if not v or not v.strip():
            raise ValueError("organization_id cannot be empty")
        return v

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserEvent(BaseEvent):
    """Event schema for user-related events."""

    event_type: str = "user"
    user_id: Optional[str] = None


class MembershipEvent(BaseEvent):
    """Event schema for membership-related events."""

    event_type: str = "membership"
    membership_id: Optional[str] = None
    user_id: Optional[str] = None


class ScheduleEvent(BaseEvent):
    """Event schema for schedule-related events."""

    event_type: str = "schedule"
    schedule_id: Optional[str] = None


class WorkoutEvent(BaseEvent):
    """Event schema for workout-related events."""

    event_type: str = "workout"
    workout_id: Optional[str] = None


class ClassEvent(BaseEvent):
    """Event schema for class-related events."""

    event_type: str = "class"
    class_id: Optional[str] = None


class DeviceEvent(BaseEvent):
    """Event schema for device-related events."""

    event_type: str = "device"
    device_id: Optional[str] = None


class OrganizationEvent(BaseEvent):
    """Event schema for organization-related events."""

    event_type: str = "organization"


EVENT_SCHEMA_MAP = {
    "user": UserEvent,
    "membership": MembershipEvent,
    "schedule": ScheduleEvent,
    "workout": WorkoutEvent,
    "class": ClassEvent,
    "device": DeviceEvent,
    "organization": OrganizationEvent,
}


def get_event_schema(event_type: str) -> type[BaseEvent]:
    """Get the appropriate event schema for an event type."""
    return EVENT_SCHEMA_MAP.get(event_type, BaseEvent)
