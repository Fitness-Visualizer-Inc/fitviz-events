"""Basic usage examples for fitviz-events library."""

from fitviz_events import EventPublisher
import asyncio


def sync_example():
    """Example of synchronous event publishing."""
    print("Synchronous Publishing Example")
    print("-" * 50)
    
    # Initialize publisher
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
            "duration": 30,
            "difficulty": "intermediate"
        },
        organization_id="org_456"
    )
    
    if success:
        print("Event published successfully!")
    else:
        print("Event publishing failed")
    
    # Close connection
    publisher.close()
    print()


async def async_example():
    """Example of asynchronous event publishing."""
    print("Asynchronous Publishing Example")
    print("-" * 50)
    
    # Initialize publisher
    publisher = EventPublisher(
        rabbitmq_url="amqp://guest:guest@localhost:5672/",
        exchange="fitviz.events"
    )
    
    # Publish multiple events asynchronously
    results = await asyncio.gather(
        publisher.publish(
            event_type="workout.created",
            data={"workout_id": "workout_1", "title": "HIIT"},
            organization_id="org_456"
        ),
        publisher.publish(
            event_type="class.scheduled",
            data={"class_id": "class_1", "title": "Yoga"},
            organization_id="org_456"
        ),
        publisher.publish(
            event_type="booking.confirmed",
            data={"booking_id": "booking_1", "user_id": "user_1"},
            organization_id="org_456"
        )
    )
    
    print(f"Published {sum(results)} events successfully")
    
    # Close connection
    publisher.close()
    print()


def context_manager_example():
    """Example using context manager."""
    print("Context Manager Example")
    print("-" * 50)
    
    # Use context manager for automatic cleanup
    with EventPublisher(rabbitmq_url="amqp://guest:guest@localhost:5672/") as publisher:
        publisher.publish_sync(
            event_type="membership.created",
            data={
                "membership_id": "membership_123",
                "user_id": "user_456",
                "plan": "premium"
            },
            organization_id="org_456"
        )
        print("Event published and connection closed automatically")
    print()


def error_handling_example():
    """Example with error handling."""
    print("Error Handling Example")
    print("-" * 50)
    
    publisher = EventPublisher(
        rabbitmq_url="amqp://guest:guest@localhost:5672/",
        exchange="fitviz.events"
    )
    
    # Graceful mode (default) - logs error, returns False
    success = publisher.publish_sync(
        event_type="workout.created",
        data={"workout_id": "123"},
        organization_id="org_456",
        graceful=True
    )
    
    if not success:
        print("Event publishing failed gracefully")
    
    # Strict mode - raises exception on error
    try:
        publisher.publish_sync(
            event_type="payment.processed",
            data={"payment_id": "123"},
            organization_id="org_456",
            graceful=False
        )
    except Exception as e:
        print(f"Exception raised in strict mode: {type(e).__name__}")
    
    publisher.close()
    print()


def metadata_example():
    """Example with custom metadata."""
    print("Custom Metadata Example")
    print("-" * 50)
    
    publisher = EventPublisher(
        rabbitmq_url="amqp://guest:guest@localhost:5672/",
        exchange="fitviz.events"
    )
    
    # Publish with custom metadata
    publisher.publish_sync(
        event_type="workout.created",
        data={"workout_id": "123", "title": "HIIT"},
        organization_id="org_456",
        metadata={
            "source": "fitviz-mobile",
            "version": "2.1.0",
            "user_agent": "FitViz-iOS/2.1.0",
            "ip_address": "192.168.1.100"
        }
    )
    
    print("Event published with custom metadata")
    publisher.close()
    print()


def main():
    """Run all examples."""
    print("FitViz Events - Usage Examples")
    print("=" * 50)
    print()
    
    # Run synchronous example
    sync_example()
    
    # Run asynchronous example
    asyncio.run(async_example())
    
    # Run context manager example
    context_manager_example()
    
    # Run error handling example
    error_handling_example()
    
    # Run metadata example
    metadata_example()
    
    print("All examples completed!")


if __name__ == "__main__":
    main()
