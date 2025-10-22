# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FitViz Events is a Python library that provides event publishing capabilities for Flask applications to integrate with the FitViz notification service via RabbitMQ. The library is designed to be a reusable package that can be installed in other FitViz projects.

**Key Characteristics:**
- Python library package (not a standalone application)
- Installable via pip (local editable install or from PyPI)
- Thread-safe RabbitMQ event publishing
- Flask-optimized with automatic organization ID injection
- Pydantic-based event validation

## Development Commands

### Installation

```bash
# Install package in editable mode (for development)
pip install -e .

# Install with dev dependencies
pip install -e .[dev]

# Install for production use
pip install fitviz-events
```

### Testing

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=fitviz_events --cov-report=html

# Run specific test markers
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m asyncio       # Async tests only

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with Black (line length: 100)
black fitviz_events/

# Sort imports with isort
isort fitviz_events/

# Type checking with mypy
mypy fitviz_events/

# Linting with flake8
flake8 fitviz_events/
```

## Architecture

### Core Components

**Publisher (`fitviz_events/publisher.py`)**
- `EventPublisher` class: Main thread-safe publisher with connection pooling
- Handles RabbitMQ connections with automatic retry logic
- Supports both sync (`publish`) and async (`async_publish`) methods
- Uses pika library for RabbitMQ protocol
- Context manager support for automatic cleanup

**Configuration (`fitviz_events/config.py`)**
- `EventPublisherConfig` dataclass: All configuration options
- Converts to pika ConnectionParameters
- Defaults optimized for Flask applications (heartbeat: 600s, timeout: 10s)

**Event Schemas (`fitviz_events/events.py`)**
- `BaseEvent`: Abstract base with common fields (event_id, timestamp, organization_id)
- 10 concrete event types with Pydantic validation
- `EVENT_TYPE_MAP`: Maps string event types to schema classes

**Exceptions (`fitviz_events/exceptions.py`)**
- `EventPublishError`: Publishing failures
- `EventValidationError`: Schema validation failures
- `ConnectionError`: RabbitMQ connection issues

### Event Publishing Flow

```
1. Application calls publisher.publish(event_type, data)
2. Publisher validates data against event schema (if enable_validation=True)
3. Publisher injects organization_id (from getter or parameter)
4. Event serialized to JSON with metadata (event_id, timestamp)
5. Published to RabbitMQ exchange with routing key (event_type)
6. Returns True on success, False on failure (graceful degradation)
```

### Thread Safety

- Uses `threading.Lock` for connection management
- Single persistent connection shared across threads
- Safe for concurrent use in Flask request handlers
- Connection automatically recreated on failure

### Flask Integration Pattern

The library is designed to be initialized once at application startup and reused:

```python
# app/__init__.py
from fitviz_events import EventPublisher
from flask import g

def create_app():
    app = Flask(__name__)

    # Initialize once as application extension
    publisher = EventPublisher(
        rabbitmq_url=app.config['RABBITMQ_URL'],
        organization_id_getter=lambda: g.get('organization_id')  # Auto-inject from Flask context
    )
    app.extensions['event_publisher'] = publisher

    return app
```

## Supported Event Types

All events follow the pattern `<domain>.<action>`:

- `workout.created`, `workout.updated`, `workout.deleted`
- `booking.confirmed`, `booking.cancelled`
- `class.scheduled`, `class.cancelled`
- `membership.created`, `membership.expired`
- `payment.completed`, `payment.failed`

Each event type has a corresponding Pydantic schema class in `events.py` that defines required/optional fields.

## Package Distribution

The package is configured for PyPI distribution:

- `setup.py`: Package metadata and dependencies
- `pyproject.toml`: Modern Python packaging config (PEP 518)
- `MANIFEST.in`: Includes non-Python files in distribution
- Version managed manually in `__init__.py` and `setup.py`

**Build and distribute:**
```bash
# Build distribution
python -m build

# Upload to PyPI (requires credentials)
python -m twine upload dist/*
```

## Testing Strategy

Tests are located in `tests/test_publisher.py` and cover:
- Connection handling and retry logic
- Event validation and serialization
- Thread safety
- Async publishing
- Error handling and graceful degradation

**RabbitMQ is NOT mocked in integration tests** - they expect a running RabbitMQ instance at `localhost:5672` (use pytest markers to skip integration tests if RabbitMQ unavailable).

## Configuration Standards

**Black formatting:**
- Line length: 100 characters
- Target Python versions: 3.9, 3.10, 3.11

**Import sorting (isort):**
- Profile: black-compatible
- Line length: 100

**Type checking (mypy):**
- Configured but lenient (disallow_untyped_defs=false)
- Ignores missing imports for third-party libraries

## Important Notes

1. **Organization ID Injection**: The `organization_id_getter` callable is critical for multi-tenant applications. It's typically set to `lambda: g.get('organization_id')` in Flask apps.

2. **Graceful Degradation**: By default, publishing failures return `False` rather than raising exceptions. This prevents event publishing issues from breaking application logic.

3. **Connection Persistence**: The publisher maintains a single persistent connection that's reused across all publish calls. Don't create multiple publisher instances unnecessarily.

4. **Event Validation**: When `enable_validation=True` (default), events are validated against Pydantic schemas before publishing. Invalid events raise `EventValidationError`.

5. **Async Support**: The library provides both sync and async methods. Use `async_publish()` in async contexts (runs in thread pool executor).

6. **Python Version**: Requires Python 3.9+ (uses modern type hints and dataclasses)
