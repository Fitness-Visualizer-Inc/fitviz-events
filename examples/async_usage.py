"""Async usage example for FitViz Events."""

import asyncio
import logging
from uuid import uuid4

from fitviz_events import EventPublisher

logging.basicConfig(level=logging.INFO)


async def publish_workout_events(publisher: EventPublisher):
    """Publish multiple workout events asynchronously."""
    events = [
        {
            'type': 'workout.created',
            'data': {
                'workout_id': str(uuid4()),
                'title': f'Workout {i}',
                'description': f'Description for workout {i}',
                'duration_minutes': 30 + i * 5,
                'created_by': 'user_async',
            }
        }
        for i in range(5)
    ]
    
    tasks = [
        publisher.async_publish(event['type'], event['data'])
        for event in events
    ]
    
    results = await asyncio.gather(*tasks)
    
    successful = sum(results)
    print(f"\nPublished {successful}/{len(results)} events successfully")
    
    return results


async def publish_booking_events(publisher: EventPublisher):
    """Publish booking events asynchronously."""
    success = await publisher.async_publish(
        'booking.confirmed',
        {
            'booking_id': str(uuid4()),
            'user_id': 'user_async',
            'class_id': 'class_async',
            'class_name': 'Async Yoga',
            'scheduled_time': '2025-01-25T10:00:00Z',
        }
    )
    
    print(f"Booking event published: {success}")
    return success


async def main():
    """Main async function demonstrating async event publishing."""
    publisher = EventPublisher(
        rabbitmq_url='amqp://guest:guest@localhost:5672/',
        organization_id_getter=lambda: 'org_async',
        enable_validation=True,
    )
    
    try:
        print("Starting async event publishing...")
        
        # Run multiple async operations concurrently
        workout_results, booking_result = await asyncio.gather(
            publish_workout_events(publisher),
            publish_booking_events(publisher),
        )
        
        print("\nAll async operations completed!")
        print(f"Workout events: {sum(workout_results)}/5 successful")
        print(f"Booking event: {'Success' if booking_result else 'Failed'}")
        
    finally:
        publisher.close()
        print("\nPublisher closed.")


if __name__ == '__main__':
    asyncio.run(main())
