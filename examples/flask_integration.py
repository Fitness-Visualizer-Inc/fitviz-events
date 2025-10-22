"""Example Flask integration with FitViz Events."""

from flask import Flask, g, request, jsonify
from fitviz_events import EventPublisher
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Configuration
app.config['RABBITMQ_URL'] = 'amqp://guest:guest@localhost:5672/'
app.config['EVENTS_EXCHANGE'] = 'fitviz.events'


def get_current_organization_id():
    """Get organization ID from Flask request context."""
    return g.get('organization_id')


def init_event_publisher(app):
    """Initialize event publisher as Flask extension."""
    publisher = EventPublisher(
        rabbitmq_url=app.config['RABBITMQ_URL'],
        exchange_name=app.config['EVENTS_EXCHANGE'],
        organization_id_getter=get_current_organization_id,
        enable_validation=True,
        retry_attempts=3,
    )
    app.extensions['event_publisher'] = publisher
    return publisher


# Initialize publisher
event_publisher = init_event_publisher(app)


@app.before_request
def before_request():
    """Set organization context before each request."""
    g.organization_id = request.headers.get('X-Organization-ID')


@app.route('/workouts', methods=['POST'])
def create_workout():
    """Create a new workout and publish event."""
    data = request.json
    
    # Simulate workout creation
    workout = {
        'id': '123',
        'title': data.get('title'),
        'description': data.get('description'),
        'duration_minutes': data.get('duration_minutes'),
    }
    
    # Publish event
    success = app.extensions['event_publisher'].publish(
        'workout.created',
        {
            'workout_id': workout['id'],
            'title': workout['title'],
            'description': workout['description'],
            'duration_minutes': workout['duration_minutes'],
            'created_by': g.get('user_id', 'unknown'),
        }
    )
    
    if success:
        app.logger.info(f"Published workout.created event for workout {workout['id']}")
    else:
        app.logger.error(f"Failed to publish workout.created event")
    
    return jsonify(workout), 201


@app.route('/bookings', methods=['POST'])
def confirm_booking():
    """Confirm a booking and publish event."""
    data = request.json
    
    booking = {
        'id': 'booking_456',
        'user_id': data.get('user_id'),
        'class_id': data.get('class_id'),
        'class_name': data.get('class_name'),
        'scheduled_time': data.get('scheduled_time'),
    }
    
    # Publish event
    app.extensions['event_publisher'].publish(
        'booking.confirmed',
        {
            'booking_id': booking['id'],
            'user_id': booking['user_id'],
            'class_id': booking['class_id'],
            'class_name': booking['class_name'],
            'scheduled_time': booking['scheduled_time'],
        }
    )
    
    return jsonify(booking), 201


@app.route('/payments', methods=['POST'])
def process_payment():
    """Process a payment and publish event."""
    data = request.json
    
    # Simulate payment processing
    success = data.get('success', True)
    
    payment = {
        'id': 'pay_789',
        'user_id': data.get('user_id'),
        'amount': data.get('amount'),
        'currency': 'USD',
    }
    
    if success:
        app.extensions['event_publisher'].publish(
            'payment.completed',
            {
                'payment_id': payment['id'],
                'user_id': payment['user_id'],
                'amount': payment['amount'],
                'currency': payment['currency'],
                'payment_method': data.get('payment_method', 'card'),
                'reference_type': 'membership',
                'reference_id': data.get('membership_id'),
            }
        )
        return jsonify(payment), 200
    else:
        app.extensions['event_publisher'].publish(
            'payment.failed',
            {
                'payment_id': payment['id'],
                'user_id': payment['user_id'],
                'amount': payment['amount'],
                'currency': payment['currency'],
                'failure_reason': data.get('failure_reason', 'Unknown error'),
                'reference_type': 'membership',
                'reference_id': data.get('membership_id'),
            }
        )
        return jsonify({'error': 'Payment failed'}), 400


@app.teardown_appcontext
def cleanup(error=None):
    """Clean up resources on app context teardown."""
    if error:
        app.logger.error(f"Error during request: {error}")


if __name__ == '__main__':
    try:
        app.run(debug=True, port=5000)
    finally:
        event_publisher.close()
