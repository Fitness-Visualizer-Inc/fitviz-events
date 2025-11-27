# FitViz Events

Event publishing client library for integrating Flask applications with the FitViz notification service via RabbitMQ or AWS SNS.

## Installation

```bash
pip install fitviz-events
```

For development:
```bash
pip install fitviz-events[dev]
```

## Quick Start

### RabbitMQ Mode (On-Premise)

```python
from fitviz_events import EventPublisher

# Initialize publisher
publisher = EventPublisher(
    rabbitmq_url="amqp://user:password@localhost:5672/",
    exchange_name="fitviz.events",
    organization_id_getter=lambda: get_current_organization_id()
)

# Publish an event
success = publisher.publish("workout.created", {
    "workout_id": "123",
    "title": "Morning Yoga",
    "duration_minutes": 60,
    "created_by": "user_456"
})

if success:
    print("Event published successfully")
```

### AWS SNS Mode (Cloud-Native)

```python
from fitviz_events import SNSEventPublisher, SNSPublisherConfig

# Initialize SNS publisher
config = SNSPublisherConfig(
    topic_arn="arn:aws:sns:us-east-2:123456789:fitviz-domain-events",
    aws_region="us-east-2"
)

publisher = SNSEventPublisher(
    config=config,
    organization_id_getter=lambda: get_current_organization_id()
)

# Publish an event
success = publisher.publish("workout.created", {
    "workout_id": "123",
    "title": "Morning Yoga",
    "duration_minutes": 60,
    "created_by": "user_456"
})

if success:
    print("Event published to SNS successfully")
```

### Flask Integration

```python
from flask import Flask, g
from fitviz_events import EventPublisher

app = Flask(__name__)

# Initialize publisher as application extension
def init_event_publisher(app):
    publisher = EventPublisher(
        rabbitmq_url=app.config['RABBITMQ_URL'],
        exchange_name=app.config.get('EVENTS_EXCHANGE', 'fitviz.events'),
        organization_id_getter=lambda: g.get('organization_id'),
        enable_validation=True
    )
    app.extensions['event_publisher'] = publisher
    return publisher

# Initialize in application factory
publisher = init_event_publisher(app)

# Use in route handlers
@app.route('/workouts', methods=['POST'])
def create_workout():
    # Create workout logic
    workout = create_workout_in_db(request.json)
    
    # Publish event
    app.extensions['event_publisher'].publish("workout.created", {
        "workout_id": str(workout.id),
        "title": workout.title,
        "description": workout.description,
        "duration_minutes": workout.duration_minutes,
        "created_by": str(g.user_id)
    })
    
    return jsonify(workout.to_dict()), 201
```

### Using Context Manager

```python
from fitviz_events import EventPublisher

with EventPublisher(
    rabbitmq_url="amqp://localhost:5672",
    organization_id_getter=lambda: "org_123"
) as publisher:
    publisher.publish("booking.confirmed", {
        "booking_id": "booking_789",
        "user_id": "user_456",
        "class_id": "class_123",
        "class_name": "Yoga 101",
        "scheduled_time": "2025-01-15T10:00:00Z"
    })
```

### RabbitMQ Configuration Object

```python
from fitviz_events import EventPublisher, EventPublisherConfig

config = EventPublisherConfig(
    rabbitmq_url="amqp://localhost:5672",
    exchange_name="fitviz.events",
    retry_attempts=5,
    retry_delay=2.0,
    enable_validation=True,
    connection_timeout=15,
    heartbeat=600
)

publisher = EventPublisher(config=config)
```

### SNS Configuration Object

```python
from fitviz_events import SNSEventPublisher, SNSPublisherConfig

config = SNSPublisherConfig(
    topic_arn="arn:aws:sns:us-east-2:123456789:fitviz-domain-events",
    aws_region="us-east-2",
    aws_access_key_id="YOUR_ACCESS_KEY",
    aws_secret_access_key="YOUR_SECRET_KEY",
    retry_attempts=5,
    retry_delay=2.0,
    enable_validation=True
)

publisher = SNSEventPublisher(config=config)
```

### SNS with LocalStack (Development)

```python
from fitviz_events import SNSEventPublisher, SNSPublisherConfig

config = SNSPublisherConfig(
    topic_arn="arn:aws:sns:us-east-2:000000000000:fitviz-domain-events",
    aws_region="us-east-2",
    use_localstack=True,
    localstack_endpoint="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

publisher = SNSEventPublisher(config=config)
```

## Supported Events

The library includes built-in validation for the following event types:

### Workout Events
- `workout.created` - New workout created
- `workout.updated` - Workout details updated
- `workout.deleted` - Workout removed

### Booking Events
- `booking.confirmed` - Class booking confirmed
- `booking.cancelled` - Booking cancelled

### Membership Events
- `membership.created` - New membership purchased
- `membership.expired` - Membership expired

### Payment Events
- `payment.completed` - Payment successful
- `payment.failed` - Payment failed

### Class Events
- `class.scheduled` - New class scheduled
- `class.cancelled` - Class cancelled

## Event Publishing

### Synchronous Publishing

```python
success = publisher.publish(
    event_type="workout.created",
    data={
        "workout_id": "123",
        "title": "HIIT Training"
    },
    organization_id=None  # Uses organization_id_getter if None
)
```

### Asynchronous Publishing

```python
import asyncio

async def publish_event():
    success = await publisher.async_publish(
        event_type="payment.completed",
        data={
            "payment_id": "pay_123",
            "user_id": "user_456",
            "amount": 99.99,
            "currency": "USD",
            "payment_method": "credit_card"
        }
    )
    return success

# Run async
asyncio.run(publish_event())
```

## Configuration Options

### RabbitMQ Configuration (EventPublisherConfig)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rabbitmq_url` | str | Required | RabbitMQ connection URL |
| `exchange_name` | str | "fitviz.events" | Exchange name for events |
| `organization_id_getter` | Callable | None | Function to get current org ID |
| `retry_attempts` | int | 3 | Connection retry attempts |
| `retry_delay` | float | 1.0 | Delay between retries (seconds) |
| `enable_validation` | bool | True | Validate events with Pydantic |
| `connection_timeout` | int | 10 | Connection timeout (seconds) |
| `heartbeat` | int | 600 | Heartbeat interval (seconds) |

### AWS SNS Configuration (SNSPublisherConfig)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `topic_arn` | str | Required | SNS topic ARN |
| `aws_region` | str | "us-east-2" | AWS region for SNS service |
| `aws_access_key_id` | str | None | AWS access key (uses boto3 defaults if None) |
| `aws_secret_access_key` | str | None | AWS secret key (uses boto3 defaults if None) |
| `use_localstack` | bool | False | Enable LocalStack for local development |
| `localstack_endpoint` | str | None | LocalStack endpoint URL |
| `retry_attempts` | int | 3 | Publish retry attempts |
| `retry_delay` | float | 1.0 | Delay between retries (seconds) |
| `enable_validation` | bool | True | Validate events with Pydantic |
| `organization_id_getter` | Callable | None | Function to get current org ID |

## Error Handling

The library uses graceful degradation - failed publishes return `False` instead of raising exceptions:

```python
success = publisher.publish("workout.created", data)

if not success:
    # Log error, send to dead letter queue, etc.
    logger.error("Failed to publish workout.created event")
    # Application continues normally
```

For strict error handling, check the logs:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fitviz_events')
```

## Thread Safety

The `EventPublisher` is thread-safe and can be used in multi-threaded Flask applications:

```python
# Shared publisher instance
publisher = EventPublisher(rabbitmq_url="amqp://localhost:5672")

# Multiple threads can safely publish
def worker_task():
    publisher.publish("event.type", {"data": "value"})

# Safe in Flask request handlers
@app.route('/endpoint')
def handle_request():
    publisher.publish("request.received", {"path": request.path})
    return "OK"
```

## SNS Message Format

When using `SNSEventPublisher`, events are published to SNS with the following structure:

### Message Body

```json
{
  "event_id": "uuid-here",
  "event_type": "workout.created",
  "organization_id": "org-uuid",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "workout_id": "123",
    "title": "Morning Yoga"
  }
}
```

### Message Attributes

SNS message attributes are automatically added for filtering:

```json
{
  "event_type": {
    "DataType": "String",
    "StringValue": "workout.created"
  },
  "organization_id": {
    "DataType": "String",
    "StringValue": "org-uuid"
  }
}
```

These attributes enable SNS filter policies on subscriptions:

```json
{
  "event_type": ["workout.created", "workout.updated"]
}
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black fitviz_events/

# Sort imports
isort fitviz_events/

# Type checking
mypy fitviz_events/
```

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: https://github.com/Fitness-Visualizer-Inc/fitviz-events/issues
- Email: dev@fitviz.com
