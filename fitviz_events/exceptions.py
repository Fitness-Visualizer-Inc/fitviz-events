"""Custom exceptions for FitViz event publisher."""


class EventPublishError(Exception):
    """Raised when event publishing fails."""

    def __init__(self, message: str, event_type: str = None, original_error: Exception = None):
        self.event_type = event_type
        self.original_error = original_error
        super().__init__(message)


class EventValidationError(Exception):
    """Raised when event validation fails."""

    def __init__(self, message: str, event_type: str = None, validation_errors: list = None):
        self.event_type = event_type
        self.validation_errors = validation_errors or []
        super().__init__(message)


class ConnectionError(Exception):
    """Raised when RabbitMQ connection fails."""

    def __init__(self, message: str, rabbitmq_url: str = None, original_error: Exception = None):
        self.rabbitmq_url = rabbitmq_url
        self.original_error = original_error
        super().__init__(message)
