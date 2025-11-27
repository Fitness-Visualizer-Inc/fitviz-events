"""Event publisher for AWS SNS integration."""

import asyncio
import json
import logging
import threading
import time
from typing import Any, Callable, Dict, Optional
from uuid import UUID, uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from fitviz_events.events import EVENT_TYPE_MAP, BaseEvent
from fitviz_events.exceptions import EventValidationError
from fitviz_events.sns_config import SNSPublisherConfig

logger = logging.getLogger(__name__)


class SNSEventPublisher:
    """Event publisher for FitViz notification service using AWS SNS.

    Thread-safe publisher that handles SNS connections, retries, and event
    validation for Flask applications in AWS-native deployments.

    Example:
        config = SNSPublisherConfig(
            topic_arn="arn:aws:sns:us-east-2:123456789:domain-events",
            aws_region="us-east-2"
        )
        publisher = SNSEventPublisher(
            config=config,
            organization_id_getter=lambda: get_current_organization_id()
        )

        success = publisher.publish("workout.created", {
            "workout_id": "123",
            "title": "Morning Yoga"
        })
    """

    def __init__(
        self,
        topic_arn: str = None,
        aws_region: str = "us-east-2",
        organization_id_getter: Callable[[], Optional[UUID]] = None,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
        enable_validation: bool = True,
        config: SNSPublisherConfig = None,
    ):
        """Initialize the SNS event publisher.

        Args:
            topic_arn: SNS topic ARN for publishing events
            aws_region: AWS region for SNS service
            organization_id_getter: Callable that returns current organization ID
            retry_attempts: Number of retry attempts for failed publishes
            retry_delay: Delay between retries in seconds
            enable_validation: Whether to validate events with Pydantic
            config: SNSPublisherConfig instance (overrides individual params)
        """
        if config:
            self.config = config
        else:
            if not topic_arn:
                raise ValueError("topic_arn is required")
            self.config = SNSPublisherConfig(
                topic_arn=topic_arn,
                aws_region=aws_region,
                retry_attempts=retry_attempts,
                retry_delay=retry_delay,
                enable_validation=enable_validation,
            )

        self.organization_id_getter = organization_id_getter
        self._sns_client = None
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
            Validated BaseEvent instance or None

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

    def _get_sns_client(self):
        """Get or create SNS client.

        Returns:
            boto3 SNS client instance
        """
        if self._is_closed:
            logger.warning("Publisher is closed, cannot create SNS client")
            return None

        with self._lock:
            if self._sns_client is None:
                try:
                    boto_config = self.config.to_boto3_config()
                    self._sns_client = boto3.client("sns", **boto_config)
                    logger.info(
                        f"SNS client created for region {self.config.aws_region}"
                    )
                except Exception as e:
                    logger.error(f"Failed to create SNS client: {str(e)}")
                    return None

            return self._sns_client

    def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        organization_id: Optional[UUID] = None,
    ) -> bool:
        """Publish an event to SNS topic (synchronous).

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

            sns_client = self._get_sns_client()
            if not sns_client:
                logger.error("Failed to get SNS client")
                return False

            event_payload = {
                "event_id": str(uuid4()),
                "event_type": event_type,
                "organization_id": org_id,
                "timestamp": (
                    validated_event.timestamp.isoformat() if validated_event else None
                ),
                "data": data,
            }

            message_body = json.dumps(event_payload)

            message_attributes = {
                "event_type": {"DataType": "String", "StringValue": event_type},
                "organization_id": {"DataType": "String", "StringValue": org_id},
            }

            for attempt in range(1, self.config.retry_attempts + 1):
                try:
                    response = sns_client.publish(
                        TopicArn=self.config.topic_arn,
                        Message=message_body,
                        MessageAttributes=message_attributes,
                    )

                    message_id = response.get("MessageId")
                    logger.info(
                        f"Published event to SNS: {event_type} (org: {org_id}, "
                        f"message_id: {message_id})"
                    )
                    return True

                except (BotoCoreError, ClientError) as e:
                    logger.warning(
                        f"SNS publish attempt {attempt}/{self.config.retry_attempts} failed: {str(e)}"
                    )
                    if attempt < self.config.retry_attempts:
                        time.sleep(self.config.retry_delay * attempt)
                    else:
                        logger.error(f"All SNS publish attempts failed: {str(e)}")
                        return False

        except EventValidationError as e:
            logger.error(f"Event validation failed: {str(e)}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error publishing event to SNS: {str(e)}")
            return False

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
        return await loop.run_in_executor(
            None, self.publish, event_type, data, organization_id
        )

    def close(self):
        """Close the publisher and release resources."""
        with self._lock:
            self._is_closed = True
            self._sns_client = None
            logger.info("SNS publisher closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
