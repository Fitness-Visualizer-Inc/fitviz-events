"""Schema tests for class.created and class.cancelled events."""

from datetime import datetime

from fitviz_events.events import ClassCancelledEvent, ClassCreatedEvent, ClassUpdatedEvent


def _created(**data):
    return ClassCreatedEvent(
        organization_id="org-1",
        data={"class_id": "c1", "class_name": "Spin", "created_by": "u1", **data},
    )


def _cancelled(**data):
    return ClassCancelledEvent(
        organization_id="org-1",
        data={
            "class_id": "c1",
            "class_name": "Spin",
            "cancellation_reason": "Class cancelled",
            **data,
        },
    )


def test_created_without_trainer():
    event = _created(trainer_id=None, trainer_name=None)
    assert event.data.trainer_id is None
    assert event.data.trainer_name is None


def test_created_omitting_trainer_fields():
    event = _created()
    assert event.data.trainer_id is None
    assert event.data.trainer_name is None


def test_created_with_trainer_name():
    event = _created(trainer_id="t1", trainer_name="Jane Doe")
    assert event.data.trainer_name == "Jane Doe"
    assert event.model_dump(mode="json")["data"]["trainer_name"] == "Jane Doe"


def test_cancelled_with_times_and_occurrences():
    event = _cancelled(
        start_time="2026-10-20T09:00:00",
        end_time="2026-10-20T10:00:00",
        trainer_name="Jane Doe",
        cancelled_occurrences=[
            {
                "occurrence_id": "o1",
                "start_time": "2026-10-20T09:00:00",
                "end_time": "2026-10-20T10:00:00",
            },
            {"occurrence_id": "o2", "start_time": "2026-10-27T09:00:00"},
        ],
    )
    assert event.data.start_time == datetime(2026, 10, 20, 9, 0)
    assert event.data.end_time == datetime(2026, 10, 20, 10, 0)
    assert event.data.cancelled_occurrences[0].occurrence_id == "o1"
    assert event.data.cancelled_occurrences[1].end_time is None


def test_cancelled_old_shape_scheduled_time_only():
    event = _cancelled(scheduled_time="2026-10-20T09:00:00")
    assert event.data.scheduled_time == datetime(2026, 10, 20, 9, 0)
    assert event.data.start_time is None
    assert event.data.end_time is None
    assert event.data.trainer_name is None
    assert event.data.cancelled_occurrences is None


def test_cancelled_without_any_time():
    event = _cancelled()
    assert event.data.scheduled_time is None
    assert event.data.start_time is None


def test_updated_has_no_trainer_fields():
    assert "trainer_id" not in ClassUpdatedEvent.ClassData.model_fields
