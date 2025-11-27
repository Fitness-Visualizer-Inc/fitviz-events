"""Unit tests for SNS event publisher."""

import json
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from botocore.exceptions import ClientError

from fitviz_events import SNSEventPublisher, SNSPublisherConfig
from fitviz_events.exceptions import EventValidationError


@pytest.fixture
def sns_config():
    """Create SNS publisher config for testing."""
    return SNSPublisherConfig(
        topic_arn="arn:aws:sns:us-east-2:123456789:test-topic",
        aws_region="us-east-2",
        aws_access_key_id="test-key-id",
        aws_secret_access_key="test-secret-key",
        retry_attempts=3,
        retry_delay=0.1,
        enable_validation=True,
    )


@pytest.fixture
def organization_id():
    """Test organization ID."""
    return uuid4()


@pytest.fixture
def mock_sns_client():
    """Create mock SNS client."""
    with patch("fitviz_events.sns_publisher.boto3.client") as mock_client:
        client_instance = MagicMock()
        client_instance.publish.return_value = {"MessageId": "test-message-id-123"}
        mock_client.return_value = client_instance
        yield client_instance


def test_sns_publisher_config_to_boto3():
    """Test SNSPublisherConfig converts to boto3 config correctly."""
    config = SNSPublisherConfig(
        topic_arn="arn:aws:sns:us-east-2:123456789:test",
        aws_region="us-west-2",
        aws_access_key_id="test-key",
        aws_secret_access_key="test-secret",
    )

    boto_config = config.to_boto3_config()

    assert boto_config["region_name"] == "us-west-2"
    assert boto_config["aws_access_key_id"] == "test-key"
    assert boto_config["aws_secret_access_key"] == "test-secret"
    assert "endpoint_url" not in boto_config


def test_sns_publisher_config_localstack():
    """Test SNSPublisherConfig with LocalStack."""
    config = SNSPublisherConfig(
        topic_arn="arn:aws:sns:us-east-2:123456789:test",
        use_localstack=True,
        localstack_endpoint="http://localhost:4566",
    )

    boto_config = config.to_boto3_config()

    assert boto_config["endpoint_url"] == "http://localhost:4566"


def test_sns_publisher_initialization_with_config(sns_config):
    """Test SNS publisher initializes with config object."""
    publisher = SNSEventPublisher(config=sns_config)

    assert publisher.config.topic_arn == "arn:aws:sns:us-east-2:123456789:test-topic"
    assert publisher.config.aws_region == "us-east-2"
    assert publisher.config.retry_attempts == 3


def test_sns_publisher_initialization_with_params():
    """Test SNS publisher initializes with individual parameters."""
    publisher = SNSEventPublisher(
        topic_arn="arn:aws:sns:us-east-2:123456789:test",
        aws_region="us-west-1",
        retry_attempts=5,
    )

    assert publisher.config.topic_arn == "arn:aws:sns:us-east-2:123456789:test"
    assert publisher.config.aws_region == "us-west-1"
    assert publisher.config.retry_attempts == 5


def test_sns_publisher_requires_topic_arn():
    """Test SNS publisher raises error if topic_arn is missing."""
    with pytest.raises(ValueError, match="topic_arn is required"):
        SNSEventPublisher()


def test_get_organization_id_from_parameter(sns_config):
    """Test organization ID retrieved from parameter."""
    org_id = uuid4()
    publisher = SNSEventPublisher(config=sns_config)

    result = publisher._get_organization_id(organization_id=org_id)

    assert result == str(org_id)


def test_get_organization_id_from_getter(sns_config):
    """Test organization ID retrieved from getter function."""
    org_id = uuid4()
    publisher = SNSEventPublisher(
        config=sns_config, organization_id_getter=lambda: org_id
    )

    result = publisher._get_organization_id()

    assert result == str(org_id)


def test_get_organization_id_parameter_overrides_getter(sns_config):
    """Test explicit parameter overrides getter function."""
    getter_org_id = uuid4()
    param_org_id = uuid4()

    publisher = SNSEventPublisher(
        config=sns_config, organization_id_getter=lambda: getter_org_id
    )

    result = publisher._get_organization_id(organization_id=param_org_id)

    assert result == str(param_org_id)


def test_publish_success(sns_config, organization_id, mock_sns_client):
    """Test successful event publish to SNS."""
    publisher = SNSEventPublisher(
        config=sns_config, organization_id_getter=lambda: organization_id
    )

    success = publisher.publish(
        event_type="workout.created",
        data={
            "workout_id": "workout_123",
            "title": "Morning Yoga",
            "description": "Relaxing yoga session",
            "duration_minutes": 60,
            "created_by": "user_456",
        },
    )

    assert success is True
    mock_sns_client.publish.assert_called_once()

    call_kwargs = mock_sns_client.publish.call_args[1]
    assert call_kwargs["TopicArn"] == sns_config.topic_arn

    message_body = json.loads(call_kwargs["Message"])
    assert message_body["event_type"] == "workout.created"
    assert message_body["organization_id"] == str(organization_id)
    assert "event_id" in message_body
    assert message_body["data"]["workout_id"] == "workout_123"


def test_publish_with_message_attributes(sns_config, organization_id, mock_sns_client):
    """Test SNS message attributes are set correctly."""
    publisher = SNSEventPublisher(
        config=sns_config, organization_id_getter=lambda: organization_id
    )

    publisher.publish(
        event_type="booking.confirmed",
        data={
            "booking_id": "booking_789",
            "user_id": "user_123",
            "class_id": "class_456",
            "class_name": "Spin Class",
            "scheduled_time": datetime.utcnow().isoformat(),
        },
    )

    call_kwargs = mock_sns_client.publish.call_args[1]
    attributes = call_kwargs["MessageAttributes"]

    assert attributes["event_type"]["DataType"] == "String"
    assert attributes["event_type"]["StringValue"] == "booking.confirmed"
    assert attributes["organization_id"]["DataType"] == "String"
    assert attributes["organization_id"]["StringValue"] == str(organization_id)


def test_publish_without_organization_id(sns_config, mock_sns_client):
    """Test publish fails gracefully without organization ID."""
    publisher = SNSEventPublisher(config=sns_config)

    success = publisher.publish(
        event_type="workout.created",
        data={"workout_id": "123", "title": "Test"},
    )

    assert success is False
    mock_sns_client.publish.assert_not_called()


def test_publish_validation_disabled(sns_config, organization_id, mock_sns_client):
    """Test publish works with validation disabled."""
    sns_config.enable_validation = False
    publisher = SNSEventPublisher(
        config=sns_config, organization_id_getter=lambda: organization_id
    )

    success = publisher.publish(
        event_type="custom.event",
        data={"any_field": "any_value"},
    )

    assert success is True
    mock_sns_client.publish.assert_called_once()


def test_publish_invalid_event_data(sns_config, organization_id, mock_sns_client):
    """Test publish fails with invalid event data when validation enabled."""
    publisher = SNSEventPublisher(
        config=sns_config, organization_id_getter=lambda: organization_id
    )

    success = publisher.publish(
        event_type="workout.created",
        data={"invalid_field": "value"},
    )

    assert success is False
    mock_sns_client.publish.assert_not_called()


def test_publish_sns_client_error_with_retry(sns_config, organization_id):
    """Test publish retries on SNS client error."""
    with patch("fitviz_events.sns_publisher.boto3.client") as mock_client:
        client_instance = MagicMock()
        client_instance.publish.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service unavailable"}},
            "publish",
        )
        mock_client.return_value = client_instance

        publisher = SNSEventPublisher(
            config=sns_config, organization_id_getter=lambda: organization_id
        )

        success = publisher.publish(
            event_type="workout.created",
            data={
                "workout_id": "123",
                "title": "Test",
                "created_by": "user_456",
            },
        )

        assert success is False
        assert client_instance.publish.call_count == sns_config.retry_attempts


def test_publish_sns_client_error_eventual_success(sns_config, organization_id):
    """Test publish succeeds after retry."""
    with patch("fitviz_events.sns_publisher.boto3.client") as mock_client:
        client_instance = MagicMock()
        client_instance.publish.side_effect = [
            ClientError(
                {
                    "Error": {
                        "Code": "ServiceUnavailable",
                        "Message": "Service unavailable",
                    }
                },
                "publish",
            ),
            {"MessageId": "test-message-id"},
        ]
        mock_client.return_value = client_instance

        publisher = SNSEventPublisher(
            config=sns_config, organization_id_getter=lambda: organization_id
        )

        success = publisher.publish(
            event_type="workout.created",
            data={
                "workout_id": "123",
                "title": "Test",
                "created_by": "user_456",
            },
        )

        assert success is True
        assert client_instance.publish.call_count == 2


def test_publish_when_closed(sns_config, organization_id, mock_sns_client):
    """Test publish fails when publisher is closed."""
    publisher = SNSEventPublisher(
        config=sns_config, organization_id_getter=lambda: organization_id
    )

    publisher.close()

    success = publisher.publish(
        event_type="workout.created",
        data={"workout_id": "123", "title": "Test"},
    )

    assert success is False
    mock_sns_client.publish.assert_not_called()


def test_context_manager(sns_config, organization_id, mock_sns_client):
    """Test SNS publisher works as context manager."""
    with SNSEventPublisher(
        config=sns_config, organization_id_getter=lambda: organization_id
    ) as publisher:
        success = publisher.publish(
            event_type="workout.created",
            data={
                "workout_id": "123",
                "title": "Test",
                "created_by": "user_456",
            },
        )

        assert success is True

    assert publisher._is_closed is True


@pytest.mark.asyncio
async def test_async_publish(sns_config, organization_id, mock_sns_client):
    """Test async publish method."""
    publisher = SNSEventPublisher(
        config=sns_config, organization_id_getter=lambda: organization_id
    )

    success = await publisher.async_publish(
        event_type="workout.created",
        data={
            "workout_id": "123",
            "title": "Async Test",
            "created_by": "user_456",
        },
    )

    assert success is True
    mock_sns_client.publish.assert_called_once()


def test_validate_event_unknown_type(sns_config, organization_id):
    """Test validation logs warning for unknown event type."""
    publisher = SNSEventPublisher(
        config=sns_config, organization_id_getter=lambda: organization_id
    )

    result = publisher._validate_event(
        event_type="unknown.event",
        data={"field": "value"},
        organization_id=str(organization_id),
    )

    assert result is None


def test_thread_safety(sns_config, organization_id, mock_sns_client):
    """Test publisher is thread-safe."""
    import threading

    publisher = SNSEventPublisher(
        config=sns_config, organization_id_getter=lambda: organization_id
    )

    results = []

    def publish_event(index):
        success = publisher.publish(
            event_type="workout.created",
            data={
                "workout_id": f"workout_{index}",
                "title": f"Test {index}",
                "created_by": "user_456",
            },
        )
        results.append(success)

    threads = [threading.Thread(target=publish_event, args=(i,)) for i in range(10)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert all(results)
    assert mock_sns_client.publish.call_count == 10
