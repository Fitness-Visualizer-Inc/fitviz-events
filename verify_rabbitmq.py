#!/usr/bin/env python
"""Quick verification script to test RabbitMQ connection capability."""

import sys
from uuid import uuid4

from fitviz_events import EventPublisher


def verify_connection():
    """Test connection to RabbitMQ server."""
    print("Testing RabbitMQ connection...")
    print("-" * 50)

    # Try default connection
    rabbitmq_url = "amqp://admin:admin@localhost:5672/"

    try:
        publisher = EventPublisher(
            rabbitmq_url=rabbitmq_url,
            exchange_name="fitviz.events.test",
            enable_validation=True,
        )

        print("[OK] EventPublisher initialized")
        print(f"  URL: {rabbitmq_url}")
        print(f"  Exchange: fitviz.events.test")

        # Test connection
        publisher._connect()
        print("[OK] Connection established successfully")

        # Test publishing an event
        test_data = {
            "workout_id": "test_123",
            "title": "Test Workout",
            "description": "Verification test",
            "duration_minutes": 30,
            "created_by": "test_user",
        }

        success = publisher.publish(
            event_type="workout.created",
            data=test_data,
            organization_id=str(uuid4()),
        )

        if success:
            print("[OK] Test event published successfully")
            print("  Event type: workout.created")
        else:
            print("[FAIL] Failed to publish test event")
            return False

        # Close connection
        publisher.close()
        print("[OK] Connection closed cleanly")

        print("-" * 50)
        print("SUCCESS: All RabbitMQ operations verified!")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("-" * 50)
        print(
            "FAILED: Could not connect to RabbitMQ. Make sure RabbitMQ is running at localhost:5672"
        )
        print("\nTo start RabbitMQ:")
        print("  - Docker: docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management")
        print("  - Windows: net start RabbitMQ")
        print("  - Linux: sudo systemctl start rabbitmq-server")
        return False


if __name__ == "__main__":
    success = verify_connection()
    sys.exit(0 if success else 1)
