"""Simple usage example for FitViz Events."""

from fitviz_events import EventPublisher
from uuid import uuid4
import logging

logging.basicConfig(level=logging.INFO)


def main():
    """Demonstrate basic usage of EventPublisher."""
    
    # Create publisher
    publisher = EventPublisher(
        rabbitmq_url='amqp://guest:guest@localhost:5672/',
        exchange_name='fitviz.events',
        organization_id_getter=lambda: 'org_123',
        enable_validation=True,
    )
    
    try:
        # Example 1: Publish workout created event
        print("\n1. Publishing workout.created event...")
        success = publisher.publish(
            'workout.created',
            {
                'workout_id': str(uuid4()),
                'title': 'Morning Yoga Session',
                'description': 'Relaxing yoga for beginners',
                'duration_minutes': 45,
                'created_by': 'user_456',
            }
        )
        print(f"Success: {success}")
        
        # Example 2: Publish booking confirmed event
        print("\n2. Publishing booking.confirmed event...")
        success = publisher.publish(
            'booking.confirmed',
            {
                'booking_id': str(uuid4()),
                'user_id': 'user_789',
                'class_id': 'class_101',
                'class_name': 'Advanced HIIT',
                'scheduled_time': '2025-01-20T10:00:00Z',
                'location': 'Studio A',
            }
        )
        print(f"Success: {success}")
        
        # Example 3: Publish membership created event
        print("\n3. Publishing membership.created event...")
        success = publisher.publish(
            'membership.created',
            {
                'membership_id': str(uuid4()),
                'user_id': 'user_789',
                'plan_name': 'Premium Monthly',
                'start_date': '2025-01-01T00:00:00Z',
                'end_date': '2025-02-01T00:00:00Z',
                'price': 99.99,
            }
        )
        print(f"Success: {success}")
        
        # Example 4: Publish payment completed event
        print("\n4. Publishing payment.completed event...")
        success = publisher.publish(
            'payment.completed',
            {
                'payment_id': str(uuid4()),
                'user_id': 'user_789',
                'amount': 99.99,
                'currency': 'USD',
                'payment_method': 'credit_card',
                'reference_type': 'membership',
                'reference_id': 'membership_123',
            }
        )
        print(f"Success: {success}")
        
        # Example 5: Publish class scheduled event
        print("\n5. Publishing class.scheduled event...")
        success = publisher.publish(
            'class.scheduled',
            {
                'class_id': str(uuid4()),
                'class_name': 'Spinning Class',
                'trainer_id': 'trainer_001',
                'trainer_name': 'John Doe',
                'scheduled_time': '2025-01-21T18:00:00Z',
                'duration_minutes': 60,
                'location': 'Cycling Studio',
                'capacity': 20,
            }
        )
        print(f"Success: {success}")
        
        print("\nAll events published successfully!")
        
    finally:
        publisher.close()
        print("\nPublisher closed.")


def context_manager_example():
    """Demonstrate using publisher as context manager."""
    print("\n" + "="*50)
    print("Context Manager Example")
    print("="*50)
    
    with EventPublisher(
        rabbitmq_url='amqp://guest:guest@localhost:5672/',
        organization_id_getter=lambda: 'org_456',
    ) as publisher:
        success = publisher.publish(
            'workout.updated',
            {
                'workout_id': str(uuid4()),
                'title': 'Updated Workout Title',
                'updated_by': 'user_123',
            }
        )
        print(f"Published in context: {success}")
    
    print("Context closed automatically.")


if __name__ == '__main__':
    main()
    context_manager_example()
