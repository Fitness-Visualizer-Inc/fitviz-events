"""Configuration for FitViz event publisher."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EventPublisherConfig:
    """Configuration for EventPublisher.

    Attributes:
        rabbitmq_url: RabbitMQ connection URL (e.g., "amqp://user:pass@host:5672/vhost")
        exchange_name: Name of the RabbitMQ exchange to publish to
        retry_attempts: Number of retry attempts for failed connections
        retry_delay: Delay in seconds between retry attempts
        enable_validation: Whether to validate events using Pydantic schemas
        connection_timeout: Timeout in seconds for establishing connection
        heartbeat: Heartbeat interval in seconds for keeping connection alive
        blocked_connection_timeout: Timeout for blocked connections
        channel_max: Maximum number of channels allowed
        frame_max: Maximum frame size
        socket_timeout: Socket timeout in seconds
    """

    rabbitmq_url: str
    exchange_name: str = "fitviz.events"
    retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_validation: bool = True
    connection_timeout: int = 10
    heartbeat: int = 600
    blocked_connection_timeout: int = 300
    channel_max: Optional[int] = None
    frame_max: Optional[int] = None
    socket_timeout: Optional[float] = 10.0

    def to_pika_params(self) -> dict:
        """Convert config to pika ConnectionParameters kwargs."""
        params = {
            "heartbeat": self.heartbeat,
            "blocked_connection_timeout": self.blocked_connection_timeout,
            "connection_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay,
            "socket_timeout": self.socket_timeout,
        }

        if self.channel_max is not None:
            params["channel_max"] = self.channel_max
        if self.frame_max is not None:
            params["frame_max"] = self.frame_max

        return params
