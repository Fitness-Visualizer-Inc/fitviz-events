# FitViz Events - Quick Start Guide

Get up and running with fitviz-events in 5 minutes!

## 1. Start RabbitMQ (Docker - Easiest)

```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

Access management UI: http://localhost:15672 (guest/guest)

## 2. Install the Package

```bash
cd C:\Users\among\Desktop\code\fitviz\fitviz-events
pip install -e .
```

## 3. Test Basic Publishing

Create `test_publish.py`:

```python
from fitviz_events import EventPublisher

# Create publisher
publisher = EventPublisher(
    rabbitmq_url="amqp://guest:guest@localhost:5672/",
    exchange="fitviz.events"
)

# Publish an event
success = publisher.publish_sync(
    event_type="workout.created",
    data={
        "workout_id": "workout_123",
        "title": "Morning HIIT",
        "duration": 30
    },
    organization_id="org_456"
)

print(f"Event published: {success}")
publisher.close()
```

Run it:
```bash
python test_publish.py
```

Expected output:
```
Event published: True
```

## 4. Verify in RabbitMQ

1. Open http://localhost:15672
2. Login with guest/guest
3. Go to "Exchanges" tab
4. You should see "fitviz.events" exchange

## 5. Integrate with Flask

### Method 1: Quick Integration

Add to your Flask app:

```python
from flask import Flask, g
from fitviz_events import EventPublisher

app = Flask(__name__)

# Initialize publisher
publisher = EventPublisher(
    rabbitmq_url="amqp://guest:guest@localhost:5672/",
    exchange="fitviz.events",
    organization_id_getter=lambda: g.get('organization_id', 'default_org')
)

@app.route('/test-event', methods=['POST'])
def test_event():
    # Publish event
    success = publisher.publish_sync(
        event_type="test.event",
        data={"message": "Hello from Flask!"}
    )
    return {"success": success}, 200

if __name__ == '__main__':
    app.run(debug=True)
```

### Method 2: FitViz Flask Integration

In `C:\Users\among\Desktop\code\fitviz\fitviz-flask`:

**Step 1**: Install package
```bash
cd C:\Users\among\Desktop\code\fitviz\fitviz-flask
pip install -e ../fitviz-events
```

**Step 2**: Update `app/__init__.py`
```python
from fitviz_events import EventPublisher

event_publisher = None

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Initialize publisher
    global event_publisher
    event_publisher = EventPublisher(
        rabbitmq_url=app.config.get('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/'),
        exchange=app.config.get('RABBITMQ_EXCHANGE', 'fitviz.events'),
        organization_id_getter=lambda: g.get('organization_id')
    )
    
    return app
```

**Step 3**: Use in routes (e.g., `app/routes/workouts.py`)
```python
from app import event_publisher

@workouts_bp.route('/', methods=['POST'])
def create_workout():
    # Your existing workout creation code
    workout = Workout.create(request.json)
    
    # Publish event
    event_publisher.publish_sync(
        event_type='workout.created',
        data={
            'workout_id': str(workout.id),
            'title': workout.title,
            'duration': workout.duration
        }
    )
    
    return jsonify(workout.to_dict()), 201
```

**Step 4**: Set environment variables
```bash
export RABBITMQ_URL="amqp://guest:guest@localhost:5672/"
export RABBITMQ_EXCHANGE="fitviz.events"
```

**Step 5**: Run Flask app
```bash
python run.py
```

**Step 6**: Test it
```bash
curl -X POST http://localhost:5000/workouts \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Workout", "duration": 30}'
```

Check RabbitMQ management UI to see the event!

## 6. Common Event Types

```python
# Workout events
publisher.publish_sync(event_type="workout.created", data={...})
publisher.publish_sync(event_type="workout.updated", data={...})
publisher.publish_sync(event_type="workout.deleted", data={...})

# Booking events
publisher.publish_sync(event_type="booking.confirmed", data={...})
publisher.publish_sync(event_type="booking.cancelled", data={...})

# Class events
publisher.publish_sync(event_type="class.scheduled", data={...})
publisher.publish_sync(event_type="class.cancelled", data={...})

# Membership events
publisher.publish_sync(event_type="membership.created", data={...})
publisher.publish_sync(event_type="membership.expired", data={...})

# User events
publisher.publish_sync(event_type="user.registered", data={...})
```

## 7. Troubleshooting

### Connection Refused
```
ConnectionError: Failed to connect to RabbitMQ
```
**Fix**: Make sure RabbitMQ is running
```bash
docker ps | grep rabbitmq
```

### Module Not Found
```
ModuleNotFoundError: No module named 'fitviz_events'
```
**Fix**: Install the package
```bash
pip install -e C:\Users\among\Desktop\code\fitviz\fitviz-events
```

### Organization ID Missing
```
ValidationError: organization_id is required
```
**Fix**: Either pass it explicitly or configure auto-injection
```python
# Option 1: Pass explicitly
publisher.publish_sync(event_type="...", data={...}, organization_id="org_123")

# Option 2: Configure auto-injection
publisher = EventPublisher(
    rabbitmq_url="...",
    organization_id_getter=lambda: g.organization_id
)
```

## 8. Next Steps

- Read full documentation: [README.md](README.md)
- Integration guide: [INSTALL.md](INSTALL.md)
- Check examples: `examples/` directory
- Review project summary: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

## Need Help?

- Check RabbitMQ management UI: http://localhost:15672
- Enable debug logging:
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  ```
- Review troubleshooting sections in README.md

## Done!

You're ready to publish events from your Flask application to RabbitMQ!
