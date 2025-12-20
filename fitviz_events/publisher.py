"""Event publisher for RabbitMQ integration."""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional
from uuid import UUID, uuid4

import pika
from pika.exceptions import AMQPChannelError, AMQPConnectionError

from fitviz_events.config import EventPublisherConfig
from fitviz_events.events import EVENT_TYPE_MAP, BaseEvent
from fitviz_events.exceptions import (
    ConnectionError,
    EventPublishError,
    EventValidationError,
)

logger = logging.getLogger(__name__)


class EventPublisher:
    """Event publisher for FitViz notification service.

    Thread-safe publisher that handles RabbitMQ connections, retries,
    and event validation for Flask applications.

    Example:
        publisher = EventPublisher(
            rabbitmq_url="amqp://localhost:5672",
            organization_id_getter=lambda: get_current_organization_id()
        )

        # Publish event
        success = publisher.publish("workout.created", {
            "workout_id": "123",
            "title": "Morning Yoga"
        })
    """

    def __init__(
        self,
        rabbitmq_url: str = None,
        exchange_name: str = "fitviz.events",
        organization_id_getter: Callable[[], Optional[UUID]] = None,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
        enable_validation: bool = True,
        config: EventPublisherConfig = None,
    ):
        """Initialize the event publisher.

        Args:
            rabbitmq_url: RabbitMQ connection URL
            exchange_name: Exchange name for publishing events
            organization_id_getter: Callable that returns current organization ID
            retry_attempts: Number of connection retry attempts
            retry_delay: Delay between retries in seconds
            enable_validation: Whether to validate events with Pydantic
            config: EventPublisherConfig instance (overrides individual params)
        """
        if config:
            self.config = config
        else:
            if not rabbitmq_url:
                raise ValueError("rabbitmq_url is required")
            self.config = EventPublisherConfig(
                rabbitmq_url=rabbitmq_url,
                exchange_name=exchange_name,
                retry_attempts=retry_attempts,
                retry_delay=retry_delay,
                enable_validation=enable_validation,
            )

        self.organization_id_getter = organization_id_getter
        self._connection = None
        self._channel = None
        self._lock = threading.Lock()
        self._is_closed = False

    def _get_organization_id(self, organization_id: Optional[UUID] = None) -> Optional[str]:
        """Get organization ID from parameter or getter.

        Args:
            organization_id: Explicit organization ID

        Returns:
            Organization ID as string or None
        """
        if organization_id:
            return str(organization_id)

        if self.organization_id_getter:
            org_id = self.organization_id_getter()
            return str(org_id) if org_id else None

        return None

    def _validate_event(
        self, event_type: str, data: Dict[str, Any], organization_id: str
    ) -> BaseEvent:
        """Validate event data using Pydantic schemas.

        Args:
            event_type: Type of the event
            data: Event data dictionary
            organization_id: Organization ID

        Returns:
            Validated BaseEvent instance

        Raises:
            EventValidationError: If validation fails
        """
        if not self.config.enable_validation:
            return None

        try:
            event_class = EVENT_TYPE_MAP.get(event_type)
            if not event_class:
                logger.warning(f"No validation schema for event type: {event_type}")
                return None

            event = event_class(
                event_id=str(uuid4()),
                event_type=event_type,
                organization_id=organization_id,
                data=data,
            )
            return event

        except Exception as e:
            raise EventValidationError(
                f"Event validation failed for {event_type}: {str(e)}",
                event_type=event_type,
                validation_errors=[str(e)],
            )

    def _connect(self) -> bool:
        """Establish RabbitMQ connection with retry logic.

        Returns:
            True if connection successful, False otherwise
        """
        if self._is_closed:
            logger.warning("Publisher is closed, cannot connect")
            return False

        with self._lock:
            if self._connection and self._connection.is_open:
                return True

            for attempt in range(1, self.config.retry_attempts + 1):
                try:
                    logger.info(
                        f"Connecting to RabbitMQ (attempt {attempt}/{self.config.retry_attempts})"
                    )

                    params = pika.URLParameters(self.config.rabbitmq_url)
                    params_dict = self.config.to_pika_params()
                    for key, value in params_dict.items():
                        if value is not None:
                            setattr(params, key, value)

                    self._connection = pika.BlockingConnection(params)
                    self._channel = self._connection.channel()

                    self._channel.exchange_declare(
                        exchange=self.config.exchange_name,
                        exchange_type="topic",
                        durable=True,
                    )

                    logger.info("Successfully connected to RabbitMQ")
                    return True

                except AMQPConnectionError as e:
                    logger.warning(f"Connection attempt {attempt} failed: {str(e)}")
                    if attempt < self.config.retry_attempts:
                        time.sleep(self.config.retry_delay * attempt)
                    else:
                        logger.error("All connection attempts failed")
                        return False

                except Exception as e:
                    logger.error(f"Unexpected error during connection: {str(e)}")
                    return False

            return False

    def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        organization_id: Optional[UUID] = None,
    ) -> bool:
        """Publish an event to RabbitMQ (synchronous).

        Args:
            event_type: Type of event (e.g., "workout.created")
            data: Event data dictionary
            organization_id: Optional organization ID (uses getter if not provided)

        Returns:
            True if published successfully, False otherwise
        """
        if self._is_closed:
            logger.warning("Publisher is closed, cannot publish event")
            return False

        try:
            org_id = self._get_organization_id(organization_id)
            if not org_id:
                logger.warning("No organization ID available, skipping event publish")
                return False

            validated_event = self._validate_event(event_type, data, org_id)

            if not self._connect():
                logger.error("Failed to connect to RabbitMQ")
                return False

            event_payload = {
                "event_id": str(uuid4()),
                "event_type": event_type,
                "organization_id": org_id,
                "timestamp": (
                    validated_event.timestamp.isoformat()
                    if validated_event
                    else datetime.utcnow().isoformat()
                ),
                "data": data,
            }

            message_body = json.dumps(event_payload)

            with self._lock:
                try:
                    self._channel.basic_publish(
                        exchange=self.config.exchange_name,
                        routing_key=event_type,
                        body=message_body,
                        properties=pika.BasicProperties(
                            delivery_mode=2,
                            content_type="application/json",
                        ),
                    )

                    logger.info(f"Published event: {event_type} (org: {org_id})")
                    return True

                except AMQPChannelError as e:
                    logger.error(f"Channel error during publish: {str(e)}")
                    self._close_connection()
                    return False

        except EventValidationError as e:
            logger.error(f"Event validation failed: {str(e)}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error publishing event: {str(e)}")
            return False

    async def async_publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        organization_id: Optional[UUID] = None,
    ) -> bool:
        """Publish an event asynchronously.

        Args:
            event_type: Type of event (e.g., "workout.created")
            data: Event data dictionary
            organization_id: Optional organization ID

        Returns:
            True if published successfully, False otherwise
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.publish, event_type, data, organization_id)

    def _close_connection(self):
        """Close the RabbitMQ connection."""
        try:
            if self._channel and self._channel.is_open:
                self._channel.close()
        except Exception as e:
            logger.warning(f"Error closing channel: {str(e)}")

        try:
            if self._connection and self._connection.is_open:
                self._connection.close()
        except Exception as e:
            logger.warning(f"Error closing connection: {str(e)}")

        self._channel = None
        self._connection = None

    def close(self):
        """Close the publisher and release resources."""
        with self._lock:
            self._is_closed = True
            self._close_connection()
            logger.info("Publisher closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
