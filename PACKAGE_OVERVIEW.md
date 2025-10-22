# FitViz Events - Package Overview

## Purpose

The `fitviz-events` package is a Python client library designed to simplify event publishing from Flask applications to the FitViz notification service via RabbitMQ. It provides a clean, production-ready interface for publishing domain events with automatic validation, retry logic, and graceful error handling.

## Key Features

### 1. Simple API
- Clean, intuitive interface for publishing events
- Context manager support for resource management
- Both synchronous and asynchronous publishing

### 2. Production-Ready
- Thread-safe for multi-threaded Flask applications
- Automatic connection retry with exponential backoff
- Graceful degradation (returns False on failure, doesn't crash)
- Comprehensive logging for debugging

### 3. Type Safety & Validation
- Pydantic-based event schemas for type safety
- Optional validation (can be disabled for performance)
- Built-in schemas for common FitViz events

### 4. Flexible Configuration
- Support for configuration objects or individual parameters
- Customizable retry attempts, delays, and timeouts
- Environment-based configuration support

## Package Structure

```
fitviz-events/
├── fitviz_events/
│   ├── __init__.py           # Package exports
│   ├── publisher.py          # EventPublisher class (main interface)
│   ├── config.py             # Configuration dataclass
│   ├── events.py             # Event schema definitions
│   └── exceptions.py         # Custom exceptions
├── tests/
│   ├── __init__.py
│   └── test_publisher.py     # Comprehensive test suite
├── examples/
│   ├── simple_usage.py       # Basic usage examples
│   ├── flask_integration.py  # Flask integration example
│   └── async_usage.py        # Async publishing examples
├── setup.py                  # Package configuration
├── pyproject.toml            # Build system configuration
├── README.md                 # User documentation
├── INSTALLATION.md           # Installation guide
└── requirements.txt          # Dependencies

```

## Core Components

### EventPublisher
The main class for publishing events to RabbitMQ.

**Key Methods:**
- `publish(event_type, data, organization_id)` - Synchronous publishing
- `async_publish(event_type, data, organization_id)` - Asynchronous publishing
- `close()` - Clean up resources
- Context manager support (`__enter__`, `__exit__`)

**Features:**
- Thread-safe connection management
- Automatic retry on connection failures
- Event validation with Pydantic
- Organization ID from getter function or parameter

### EventPublisherConfig
Configuration dataclass for publisher settings.

**Parameters:**
- `rabbitmq_url` - RabbitMQ connection URL
- `exchange_name` - Exchange name for publishing
- `retry_attempts` - Number of connection retries
- `retry_delay` - Delay between retries
- `enable_validation` - Enable/disable event validation
- Connection tuning parameters (timeout, heartbeat, etc.)

### Event Schemas
Pydantic models for domain events:
- WorkoutCreatedEvent
- WorkoutUpdatedEvent
- WorkoutDeletedEvent
- BookingConfirmedEvent
- BookingCancelledEvent
- MembershipCreatedEvent
- MembershipExpiredEvent
- PaymentCompletedEvent
- PaymentFailedEvent
- ClassScheduledEvent
- ClassCancelledEvent

### Custom Exceptions
- `EventPublishError` - Publishing failures
- `EventValidationError` - Validation failures
- `ConnectionError` - Connection failures

## Usage Patterns

### Basic Usage
```python
from fitviz_events import EventPublisher

publisher = EventPublisher(
    rabbitmq_url="amqp://localhost:5672",
    organization_id_getter=lambda: get_current_org_id()
)

success = publisher.publish("workout.created", {
    "workout_id": "123",
    "title": "Morning Yoga"
})
```

### Flask Integration
```python
# Initialize as Flask extension
publisher = EventPublisher(
    rabbitmq_url=app.config['RABBITMQ_URL'],
    organization_id_getter=lambda: g.get('organization_id')
)
app.extensions['event_publisher'] = publisher

# Use in routes
@app.route('/workouts', methods=['POST'])
def create_workout():
    # ... create workout ...
    app.extensions['event_publisher'].publish("workout.created", data)
    return jsonify(workout)
```

### Context Manager
```python
with EventPublisher(rabbitmq_url="amqp://localhost:5672") as publisher:
    publisher.publish("event.type", {"data": "value"})
# Automatically closed
```

## Design Decisions

### 1. Graceful Degradation
The library returns `False` on publish failures instead of raising exceptions. This ensures that event publishing failures don't crash the main application.

**Rationale:** Event publishing is often a secondary concern. If RabbitMQ is down, the application should continue serving requests rather than failing.

### 2. Thread Safety
Uses threading locks to ensure safe concurrent access from multiple Flask request handlers.

**Rationale:** Flask applications are often multi-threaded, so the publisher must be thread-safe.

### 3. Organization ID Getter
Accepts a callable that returns the current organization ID rather than requiring it on each call.

**Rationale:** In Flask applications, organization ID is typically stored in request context (`g` object). The getter pattern allows the publisher to access it automatically.

### 4. Optional Validation
Event validation can be disabled for performance-critical applications.

**Rationale:** While validation is helpful, some high-throughput applications may prefer to skip it for better performance.

### 5. Connection Pooling
Reuses connections rather than creating a new connection for each publish.

**Rationale:** Connection establishment is expensive. Reusing connections improves performance.

## Testing

The package includes comprehensive tests using:
- **pytest** - Testing framework
- **pytest-mock** - Mocking support
- **pytest-asyncio** - Async test support

Test coverage includes:
- Initialization scenarios
- Event validation
- Connection management
- Publishing (success and failure cases)
- Async publishing
- Context manager behavior
- Error handling
- Thread safety

## Dependencies

**Runtime Dependencies:**
- `pika>=1.3.0` - RabbitMQ client
- `pydantic>=2.0.0` - Data validation

**Development Dependencies:**
- `pytest>=7.0.0` - Testing
- `pytest-asyncio>=0.21.0` - Async testing
- `pytest-mock>=3.10.0` - Mocking
- `black>=23.0.0` - Code formatting
- `flake8>=6.0.0` - Linting
- `mypy>=1.0.0` - Type checking

## Version Compatibility

- **Python:** 3.9, 3.10, 3.11, 3.12
- **Flask:** 2.0+
- **RabbitMQ:** 3.8+

## Future Enhancements

Potential improvements for future versions:
1. Batch publishing support
2. Dead letter queue integration
3. Event replay functionality
4. Metrics and monitoring integration
5. Schema registry integration
6. Event versioning support
7. Circuit breaker pattern for connection failures
8. Custom serialization formats (MessagePack, Protobuf)

## Contributing

To contribute to this package:
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Format code with black and isort
6. Submit a pull request

## License

MIT License - See LICENSE file for details.
