"""Tests for EventPublisher."""

import asyncio
import json
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest
import pika

from fitviz_events import EventPublisher, EventPublisherConfig
from fitviz_events.exceptions import EventValidationError


@pytest.fixture
def rabbitmq_url():
    """RabbitMQ connection URL for testing."""
    return "amqp://guest:guest@localhost:5672/"


@pytest.fixture
def mock_organization_id():
    """Mock organization ID."""
    return str(uuid4())


@pytest.fixture
def organization_id_getter(mock_organization_id):
    """Mock organization ID getter function."""
    return lambda: mock_organization_id


@pytest.fixture
def publisher(rabbitmq_url, organization_id_getter):
    """Create EventPublisher instance for testing."""
    return EventPublisher(
        rabbitmq_url=rabbitmq_url,
        exchange_name="test.events",
        organization_id_getter=organization_id_getter,
        enable_validation=True,
    )


@pytest.fixture
def mock_connection():
    """Mock pika connection."""
    connection = MagicMock(spec=pika.BlockingConnection)
    connection.is_open = True
    channel = MagicMock()
    channel.is_open = True
    connection.channel.return_value = channel
    return connection


class TestEventPublisherInit:
    """Test EventPublisher initialization."""

    def test_init_with_url(self, rabbitmq_url):
        """Test initialization with URL."""
        publisher = EventPublisher(rabbitmq_url=rabbitmq_url)
        assert publisher.config.rabbitmq_url == rabbitmq_url
        assert publisher.config.exchange_name == "fitviz.events"

    def test_init_with_config(self):
        """Test initialization with config object."""
        config = EventPublisherConfig(
            rabbitmq_url="amqp://test:5672",
            exchange_name="custom.exchange",
            retry_attempts=5,
        )
        publisher = EventPublisher(config=config)
        assert publisher.config.rabbitmq_url == "amqp://test:5672"
        assert publisher.config.exchange_name == "custom.exchange"
        assert publisher.config.retry_attempts == 5

    def test_init_without_url_raises_error(self):
        """Test initialization without URL raises ValueError."""
        with pytest.raises(ValueError, match="rabbitmq_url is required"):
            EventPublisher()

    def test_init_with_organization_id_getter(self, rabbitmq_url, organization_id_getter):
        """Test initialization with organization ID getter."""
        publisher = EventPublisher(
            rabbitmq_url=rabbitmq_url,
            organization_id_getter=organization_id_getter,
        )
        assert publisher.organization_id_getter is not None


class TestGetOrganizationId:
    """Test _get_organization_id method."""

    def test_get_organization_id_from_parameter(self, publisher):
        """Test getting organization ID from parameter."""
        org_id = uuid4()
        result = publisher._get_organization_id(org_id)
        assert result == str(org_id)

    def test_get_organization_id_from_getter(self, publisher, mock_organization_id):
        """Test getting organization ID from getter."""
        result = publisher._get_organization_id()
        assert result == mock_organization_id

    def test_get_organization_id_no_getter(self, rabbitmq_url):
        """Test getting organization ID when no getter is set."""
        publisher = EventPublisher(rabbitmq_url=rabbitmq_url)
        result = publisher._get_organization_id()
        assert result is None


class TestValidateEvent:
    """Test event validation."""

    def test_validate_workout_created_event(self, publisher, mock_organization_id):
        """Test validating workout.created event."""
        data = {
            "workout_id": "123",
            "title": "Morning Yoga",
            "created_by": "user_456",
        }
        event = publisher._validate_event("workout.created", data, mock_organization_id)
        assert event is not None
        assert event.event_type == "workout.created"
        assert event.organization_id == mock_organization_id

    def test_validate_booking_confirmed_event(self, publisher, mock_organization_id):
        """Test validating booking.confirmed event."""
        data = {
            "booking_id": "booking_123",
            "user_id": "user_456",
            "class_id": "class_789",
            "class_name": "Yoga 101",
            "scheduled_time": "2025-01-15T10:00:00Z",
        }
        event = publisher._validate_event("booking.confirmed", data, mock_organization_id)
        assert event is not None
        assert event.event_type == "booking.confirmed"

    def test_validate_invalid_event_raises_error(self, publisher, mock_organization_id):
        """Test validating invalid event raises EventValidationError."""
        data = {"invalid": "data"}
        with pytest.raises(EventValidationError):
            publisher._validate_event("workout.created", data, mock_organization_id)

    def test_validate_unknown_event_type(self, publisher, mock_organization_id):
        """Test validating unknown event type returns None."""
        data = {"some": "data"}
        event = publisher._validate_event("unknown.event", data, mock_organization_id)
        assert event is None

    def test_validation_disabled(self, rabbitmq_url, organization_id_getter, mock_organization_id):
        """Test validation disabled returns None."""
        publisher = EventPublisher(
            rabbitmq_url=rabbitmq_url,
            organization_id_getter=organization_id_getter,
            enable_validation=False,
        )
        data = {"workout_id": "123"}
        event = publisher._validate_event("workout.created", data, mock_organization_id)
        assert event is None


class TestConnect:
    """Test connection management."""

    @patch('fitviz_events.publisher.pika.BlockingConnection')
    def test_connect_success(self, mock_blocking_connection, publisher, mock_connection):
        """Test successful connection."""
        mock_blocking_connection.return_value = mock_connection
        result = publisher._connect()
        assert result is True
        assert publisher._connection is not None
        assert publisher._channel is not None

    @patch('fitviz_events.publisher.pika.BlockingConnection')
    def test_connect_already_connected(self, mock_blocking_connection, publisher, mock_connection):
        """Test connecting when already connected."""
        mock_blocking_connection.return_value = mock_connection
        publisher._connect()
        
        # Reset mock to verify it's not called again
        mock_blocking_connection.reset_mock()
        result = publisher._connect()
        
        assert result is True
        mock_blocking_connection.assert_not_called()

    @patch('fitviz_events.publisher.pika.BlockingConnection')
    def test_connect_failure_with_retry(self, mock_blocking_connection, publisher):
        """Test connection failure with retry."""
        from pika.exceptions import AMQPConnectionError
        mock_blocking_connection.side_effect = AMQPConnectionError("Connection failed")
        
        result = publisher._connect()
        assert result is False
        assert mock_blocking_connection.call_count == publisher.config.retry_attempts

    @patch('fitviz_events.publisher.pika.BlockingConnection')
    def test_connect_closed_publisher(self, mock_blocking_connection, publisher):
        """Test connecting with closed publisher."""
        publisher._is_closed = True
        result = publisher._connect()
        assert result is False
        mock_blocking_connection.assert_not_called()


class TestPublish:
    """Test event publishing."""

    @patch('fitviz_events.publisher.pika.BlockingConnection')
    def test_publish_success(self, mock_blocking_connection, publisher, mock_connection, mock_organization_id):
        """Test successful event publishing."""
        mock_blocking_connection.return_value = mock_connection
        
        data = {
            "workout_id": "123",
            "title": "Morning Yoga",
            "created_by": "user_456",
        }
        result = publisher.publish("workout.created", data)
        
        assert result is True
        mock_connection.channel().basic_publish.assert_called_once()
        
        # Verify message content
        call_args = mock_connection.channel().basic_publish.call_args
        assert call_args[1]['exchange'] == "test.events"
        assert call_args[1]['routing_key'] == "workout.created"
        
        body = json.loads(call_args[1]['body'])
        assert body['event_type'] == "workout.created"
        assert body['organization_id'] == mock_organization_id
        assert body['data'] == data

    @patch('fitviz_events.publisher.pika.BlockingConnection')
    def test_publish_with_explicit_organization_id(self, mock_blocking_connection, publisher, mock_connection):
        """Test publishing with explicit organization ID."""
        mock_blocking_connection.return_value = mock_connection
        
        org_id = uuid4()
        data = {"workout_id": "123", "title": "Test", "created_by": "user"}
        result = publisher.publish("workout.created", data, organization_id=org_id)
        
        assert result is True
        call_args = mock_connection.channel().basic_publish.call_args
        body = json.loads(call_args[1]['body'])
        assert body['organization_id'] == str(org_id)

    @patch('fitviz_events.publisher.pika.BlockingConnection')
    def test_publish_no_organization_id(self, mock_blocking_connection, publisher, rabbitmq_url):
        """Test publishing without organization ID returns False."""
        publisher_no_org = EventPublisher(rabbitmq_url=rabbitmq_url)
        data = {"workout_id": "123"}
        result = publisher_no_org.publish("workout.created", data)
        assert result is False

    @patch('fitviz_events.publisher.pika.BlockingConnection')
    def test_publish_connection_failure(self, mock_blocking_connection, publisher):
        """Test publishing when connection fails."""
        from pika.exceptions import AMQPConnectionError
        mock_blocking_connection.side_effect = AMQPConnectionError("Failed")
        
        data = {"workout_id": "123", "title": "Test", "created_by": "user"}
        result = publisher.publish("workout.created", data)
        assert result is False

    @patch('fitviz_events.publisher.pika.BlockingConnection')
    def test_publish_validation_error(self, mock_blocking_connection, publisher, mock_connection):
        """Test publishing with validation error returns False."""
        mock_blocking_connection.return_value = mock_connection
        
        # Invalid data for workout.created
        data = {"invalid": "data"}
        result = publisher.publish("workout.created", data)
        assert result is False

    def test_publish_closed_publisher(self, publisher):
        """Test publishing with closed publisher returns False."""
        publisher._is_closed = True
        result = publisher.publish("workout.created", {"workout_id": "123"})
        assert result is False


class TestAsyncPublish:
    """Test async event publishing."""

    @patch('fitviz_events.publisher.pika.BlockingConnection')
    @pytest.mark.asyncio
    async def test_async_publish_success(self, mock_blocking_connection, publisher, mock_connection, mock_organization_id):
        """Test async publishing."""
        mock_blocking_connection.return_value = mock_connection
        
        data = {
            "workout_id": "123",
            "title": "Async Workout",
            "created_by": "user_456",
        }
        result = await publisher.async_publish("workout.created", data)
        assert result is True


class TestContextManager:
    """Test context manager functionality."""

    @patch('fitviz_events.publisher.pika.BlockingConnection')
    def test_context_manager(self, mock_blocking_connection, rabbitmq_url, organization_id_getter, mock_connection):
        """Test using publisher as context manager."""
        mock_blocking_connection.return_value = mock_connection
        
        with EventPublisher(
            rabbitmq_url=rabbitmq_url,
            organization_id_getter=organization_id_getter
        ) as publisher:
            data = {"workout_id": "123", "title": "Test", "created_by": "user"}
            result = publisher.publish("workout.created", data)
            assert result is True
        
        # Verify publisher is closed after context
        assert publisher._is_closed is True


class TestClose:
    """Test publisher cleanup."""

    @patch('fitviz_events.publisher.pika.BlockingConnection')
    def test_close(self, mock_blocking_connection, publisher, mock_connection):
        """Test closing publisher."""
        mock_blocking_connection.return_value = mock_connection
        publisher._connect()
        
        publisher.close()
        assert publisher._is_closed is True
        mock_connection.channel().close.assert_called_once()
        mock_connection.close.assert_called_once()

    def test_close_no_connection(self, publisher):
        """Test closing publisher without connection."""
        publisher.close()
        assert publisher._is_closed is True
