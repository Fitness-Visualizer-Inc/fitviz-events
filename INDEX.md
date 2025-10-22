# FitViz Events - Documentation Index

## Quick Links

### Getting Started
- **[README.md](README.md)** - Main documentation with installation, usage, and API reference
- **[INSTALLATION.md](INSTALLATION.md)** - Detailed installation instructions
- **[NEXT_STEPS.md](NEXT_STEPS.md)** - Integration guide and next steps
- **[SUMMARY.md](SUMMARY.md)** - Complete package summary

### Understanding the Package
- **[PACKAGE_OVERVIEW.md](PACKAGE_OVERVIEW.md)** - Architecture, design decisions, and component details

### Code Examples
- **[examples/simple_usage.py](examples/simple_usage.py)** - Basic usage examples
- **[examples/flask_integration.py](examples/flask_integration.py)** - Flask application integration
- **[examples/async_usage.py](examples/async_usage.py)** - Async/await patterns

### Development
- **[requirements.txt](requirements.txt)** - Runtime dependencies
- **[requirements-dev.txt](requirements-dev.txt)** - Development dependencies
- **[tests/test_publisher.py](tests/test_publisher.py)** - Comprehensive test suite

## Package Contents

### Core Modules

| Module | Description | Lines |
|--------|-------------|-------|
| `fitviz_events/__init__.py` | Package exports and public API | ~50 |
| `fitviz_events/publisher.py` | EventPublisher class - main interface | ~315 |
| `fitviz_events/config.py` | Configuration dataclass | ~53 |
| `fitviz_events/events.py` | Event schema definitions (Pydantic) | ~209 |
| `fitviz_events/exceptions.py` | Custom exceptions | ~29 |

### Documentation Structure

```
fitviz-events/
├── INDEX.md                    # This file - documentation index
├── README.md                   # Main user documentation
├── SUMMARY.md                  # Package summary and overview
├── INSTALLATION.md             # Installation guide
├── NEXT_STEPS.md              # Integration guide
├── PACKAGE_OVERVIEW.md        # Architecture and design
├── LICENSE                     # MIT License
│
├── fitviz_events/             # Main package
│   ├── __init__.py
│   ├── publisher.py           # EventPublisher class
│   ├── config.py              # Configuration
│   ├── events.py              # Event schemas
│   └── exceptions.py          # Custom exceptions
│
├── tests/                      # Test suite
│   ├── __init__.py
│   └── test_publisher.py      # Publisher tests
│
├── examples/                   # Usage examples
│   ├── simple_usage.py        # Basic examples
│   ├── flask_integration.py   # Flask integration
│   └── async_usage.py         # Async examples
│
└── Configuration files
    ├── setup.py               # Package setup
    ├── pyproject.toml         # Build configuration
    ├── pytest.ini             # Test configuration
    ├── requirements.txt       # Dependencies
    └── requirements-dev.txt   # Dev dependencies
```

## Quick Reference

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Basic Usage

```python
from fitviz_events import EventPublisher

publisher = EventPublisher(
    rabbitmq_url="amqp://localhost:5672",
    organization_id_getter=lambda: "org_123"
)

success = publisher.publish("workout.created", {
    "workout_id": "123",
    "title": "Morning Yoga"
})
```

### Flask Integration

```python
# Initialize
publisher = EventPublisher(
    rabbitmq_url=app.config['RABBITMQ_URL'],
    organization_id_getter=lambda: g.get('organization_id')
)
app.extensions['event_publisher'] = publisher

# Use in routes
app.extensions['event_publisher'].publish("event.type", data)
```

## Event Types

| Event Type | Description |
|------------|-------------|
| `workout.created` | New workout created |
| `workout.updated` | Workout updated |
| `workout.deleted` | Workout deleted |
| `booking.confirmed` | Booking confirmed |
| `booking.cancelled` | Booking cancelled |
| `membership.created` | Membership created |
| `membership.expired` | Membership expired |
| `payment.completed` | Payment successful |
| `payment.failed` | Payment failed |
| `class.scheduled` | Class scheduled |
| `class.cancelled` | Class cancelled |

## API Reference

### EventPublisher

**Constructor:**
```python
EventPublisher(
    rabbitmq_url: str,
    exchange_name: str = "fitviz.events",
    organization_id_getter: Callable = None,
    retry_attempts: int = 3,
    retry_delay: float = 1.0,
    enable_validation: bool = True,
    config: EventPublisherConfig = None
)
```

**Methods:**
- `publish(event_type, data, organization_id=None)` - Publish event synchronously
- `async_publish(event_type, data, organization_id=None)` - Publish event asynchronously
- `close()` - Close connection and cleanup resources

**Context Manager:**
```python
with EventPublisher(...) as publisher:
    publisher.publish("event.type", data)
```

### EventPublisherConfig

**Attributes:**
- `rabbitmq_url: str` - RabbitMQ connection URL (required)
- `exchange_name: str` - Exchange name (default: "fitviz.events")
- `retry_attempts: int` - Connection retry attempts (default: 3)
- `retry_delay: float` - Delay between retries (default: 1.0)
- `enable_validation: bool` - Enable event validation (default: True)
- `connection_timeout: int` - Connection timeout in seconds (default: 10)
- `heartbeat: int` - Heartbeat interval (default: 600)

## Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=fitviz_events --cov-report=html
```

### Run Specific Test
```bash
pytest tests/test_publisher.py::TestEventPublisherInit
```

## Development Workflow

1. **Make Changes** - Edit source files
2. **Run Tests** - `pytest`
3. **Format Code** - `black .`
4. **Sort Imports** - `isort .`
5. **Type Check** - `mypy fitviz_events/`
6. **Commit** - Commit changes

## Dependencies

### Runtime
- `pika >= 1.3.0` - RabbitMQ client
- `pydantic >= 2.0.0` - Data validation

### Development
- `pytest >= 7.0.0` - Testing
- `pytest-asyncio >= 0.21.0` - Async testing
- `pytest-mock >= 3.10.0` - Mocking
- `black >= 23.0.0` - Code formatting
- `flake8 >= 6.0.0` - Linting
- `mypy >= 1.0.0` - Type checking

## Support

- **GitHub Issues:** Report bugs or request features
- **Email:** dev@fitviz.com
- **Documentation:** This repository

## Version Information

- **Current Version:** 1.0.0
- **Python Support:** 3.9, 3.10, 3.11, 3.12
- **License:** MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Format code with black and isort
6. Submit a pull request

---

**Package Location:** `C:\Users\among\Desktop\code\fitviz\fitviz-events`

**Status:** Ready for integration and testing
