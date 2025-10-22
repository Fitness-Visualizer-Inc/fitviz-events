# Installation Guide for fitviz-events

This guide provides detailed instructions for installing and integrating the fitviz-events library.

## Prerequisites

- Python 3.8 or higher
- RabbitMQ server (local or remote)
- pip package manager

## Installation Methods

### Method 1: Install from Local Source (Development)

```bash
cd C:\Users\among\Desktop\code\fitviz\fitviz-events
pip install -e .
```

This installs the package in editable mode, allowing you to make changes to the source code.

### Method 2: Install from Git Repository

```bash
pip install git+https://github.com/Fitness-Visualizer-Inc/fitviz-events.git@main
```

### Method 3: Install from requirements.txt

Add to your project's requirements.txt:

```
fitviz-events @ git+https://github.com/Fitness-Visualizer-Inc/fitviz-events.git@main
```

Then install:

```bash
pip install -r requirements.txt
```

### Method 4: Install with Development Dependencies

For development work:

```bash
pip install -e ".[dev]"
```

This installs additional tools for testing, linting, and formatting.

## RabbitMQ Setup

### Option 1: Docker (Recommended for Development)

```bash
# Run RabbitMQ with management UI
docker run -d \
  --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=admin \
  -e RABBITMQ_DEFAULT_PASS=admin123 \
  rabbitmq:3-management

# Verify RabbitMQ is running
docker ps | grep rabbitmq
```

Access management UI at http://localhost:15672 (username: admin, password: admin123)

### Option 2: Local Installation (Windows)

1. Download RabbitMQ from https://www.rabbitmq.com/download.html
2. Install Erlang (required dependency)
3. Install RabbitMQ
4. Start RabbitMQ service from Services panel

### Option 3: Cloud-hosted RabbitMQ

Use a managed service like CloudAMQP, AWS MQ, or Azure Service Bus.

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Required
RABBITMQ_URL=amqp://admin:admin123@localhost:5672/

# Optional (with defaults shown)
RABBITMQ_EXCHANGE=fitviz.events
RABBITMQ_EXCHANGE_TYPE=topic
RABBITMQ_MAX_RETRIES=3
RABBITMQ_RETRY_DELAY=1.0
RABBITMQ_RETRY_BACKOFF=2.0
RABBITMQ_CONNECTION_TIMEOUT=10
RABBITMQ_HEARTBEAT=60
RABBITMQ_ENABLED=true
```

### Flask Configuration

Add to your Flask config:

```python
# config.py
import os

class Config:
    RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
    RABBITMQ_EXCHANGE = os.getenv('RABBITMQ_EXCHANGE', 'fitviz.events')
    RABBITMQ_ENABLED = os.getenv('RABBITMQ_ENABLED', 'true').lower() == 'true'
```

## Integration with FitViz Flask

### Step 1: Install the Package

```bash
cd C:\Users\among\Desktop\code\fitviz\fitviz-flask
pip install -e ../fitviz-events
```

### Step 2: Add to Requirements

Add to `requirements.txt`:

```
fitviz-events @ file:///C:/Users/among/Desktop/code/fitviz/fitviz-events
```

### Step 3: Initialize in Application Factory

Edit `app/__init__.py`:

```python
from flask import Flask, g
from fitviz_events import EventPublisher

# Global publisher instance
event_publisher = None

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize event publisher
    global event_publisher
    event_publisher = EventPublisher(
        rabbitmq_url=app.config['RABBITMQ_URL'],
        exchange=app.config.get('RABBITMQ_EXCHANGE', 'fitviz.events'),
        organization_id_getter=lambda: g.get('organization_id')
    )
    
    # Register blueprints
    from app.routes import workouts
    app.register_blueprint(workouts.bp)
    
    return app
```

### Step 4: Use in Routes

Edit `app/routes/workouts.py`:

```python
from flask import Blueprint, request, jsonify, g
from app import event_publisher

bp = Blueprint('workouts', __name__, url_prefix='/workouts')

@bp.route('/', methods=['POST'])
def create_workout():
    data = request.json
    
    # Create workout in database
    workout = Workout.create(data)
    
    # Publish event
    event_publisher.publish_sync(
        event_type='workout.created',
        data={
            'workout_id': str(workout.id),
            'title': workout.title,
            'duration': workout.duration,
            'created_by': g.user_id
        }
        # organization_id auto-injected from g.organization_id
    )
    
    return jsonify(workout.to_dict()), 201
```

### Step 5: Add Middleware for Organization Context

Edit `app/middleware/tenant.py`:

```python
from flask import g, request

def set_organization_context():
    """Set organization ID in Flask context."""
    # Get from JWT token, header, or session
    g.organization_id = request.headers.get('X-Organization-ID')
    
    if not g.organization_id:
        # Extract from JWT token
        from flask_jwt_extended import get_jwt
        jwt_data = get_jwt()
        g.organization_id = jwt_data.get('organization_id')
```

Register middleware in `app/__init__.py`:

```python
from app.middleware.tenant import set_organization_context

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Register middleware
    app.before_request(set_organization_context)
    
    # ... rest of initialization
```

## Verification

### Test the Installation

Create a test script `test_events.py`:

```python
from fitviz_events import EventPublisher

# Test basic publishing
publisher = EventPublisher(
    rabbitmq_url="amqp://admin:admin123@localhost:5672/",
    exchange="fitviz.events"
)

success = publisher.publish_sync(
    event_type="test.event",
    data={"message": "Hello from fitviz-events!"},
    organization_id="test_org"
)

if success:
    print("Event published successfully!")
else:
    print("Event publishing failed")

publisher.close()
```

Run the test:

```bash
python test_events.py
```

### Verify in RabbitMQ Management UI

1. Open http://localhost:15672
2. Navigate to "Exchanges"
3. Look for "fitviz.events" exchange
4. Click on it to see bindings and messages

### Check Application Logs

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('fitviz_events')
logger.setLevel(logging.DEBUG)
```

You should see:

```
INFO:fitviz_events.publisher:Initialized EventPublisher with exchange=fitviz.events, enabled=True
INFO:fitviz_events.publisher:Established RabbitMQ connection
INFO:fitviz_events.publisher:Declared exchange: fitviz.events
INFO:fitviz_events.publisher:Published workout.created event: <uuid> (org: org_123)
```

## Troubleshooting

### Issue: Connection Refused

```
ConnectionError: Failed to connect to RabbitMQ
```

**Solution**:
1. Verify RabbitMQ is running: `docker ps` or check Services panel
2. Check the URL in configuration
3. Verify firewall settings allow port 5672

### Issue: Authentication Failed

```
ProbableAuthenticationError: (403, 'ACCESS_REFUSED')
```

**Solution**:
1. Check username/password in RABBITMQ_URL
2. Verify user has permissions in RabbitMQ
3. Use default credentials: `amqp://guest:guest@localhost:5672/`

### Issue: Import Error

```
ModuleNotFoundError: No module named 'fitviz_events'
```

**Solution**:
1. Verify installation: `pip list | grep fitviz`
2. Reinstall: `pip install -e .`
3. Check virtual environment is activated

### Issue: Organization ID Missing

```
ValidationError: organization_id is required
```

**Solution**:
1. Configure organization_id_getter in publisher initialization
2. Or pass organization_id explicitly in publish_sync calls
3. Verify middleware sets g.organization_id

## Production Deployment

### Environment Variables

Set in production environment:

```bash
export RABBITMQ_URL="amqps://user:pass@production-rabbitmq.com:5671/"
export RABBITMQ_EXCHANGE="fitviz.production.events"
export RABBITMQ_MAX_RETRIES="5"
export RABBITMQ_CONNECTION_TIMEOUT="30"
```

### High Availability

Consider:
- RabbitMQ cluster for redundancy
- Persistent messages (already enabled)
- Monitoring and alerting
- Dead letter queues for failed events

### Security

- Use TLS/SSL (amqps://)
- Implement proper authentication
- Restrict network access
- Use separate credentials per environment

## Next Steps

1. Read the full documentation in README.md
2. Review examples in the `examples/` directory
3. Integrate with your Flask routes
4. Set up the notification service to consume events
5. Monitor event flow in RabbitMQ management UI

## Support

For issues or questions:
- GitHub Issues: https://github.com/Fitness-Visualizer-Inc/fitviz-events/issues
- Email: dev@fitviz.com
