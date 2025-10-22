"""Example Flask application using fitviz-events."""

from flask import Flask, g, request, jsonify
from fitviz_events import EventPublisher

app = Flask(__name__)

app.config["RABBITMQ_URL"] = "amqp://guest:guest@localhost:5672/"

publisher = EventPublisher(
    rabbitmq_url=app.config["RABBITMQ_URL"],
    organization_id=lambda: g.organization_id,
    graceful_degradation=True
)


@app.before_request
def set_organization_id():
    """Extract organization ID from request headers."""
    g.organization_id = request.headers.get("X-Organization-ID", "default_org")


@app.route("/users", methods=["POST"])
def create_user():
    """Create a user and publish event."""
    user_data = request.json
    
    user = {
        "id": "user_123",
        "email": user_data.get("email"),
        "name": user_data.get("name")
    }
    
    publisher.publish_sync(
        event_type="user",
        data={
            "action": "created",
            "user_id": user["id"],
            "email": user["email"]
        },
        metadata={
            "source": "api",
            "endpoint": request.endpoint
        }
    )
    
    return jsonify(user), 201


@app.route("/memberships", methods=["POST"])
def create_membership():
    """Create a membership and publish event."""
    membership_data = request.json
    
    membership = {
        "id": "mem_456",
        "user_id": membership_data.get("user_id"),
        "plan": membership_data.get("plan")
    }
    
    publisher.publish_sync(
        event_type="membership",
        data={
            "action": "subscription_created",
            "membership_id": membership["id"],
            "user_id": membership["user_id"],
            "plan": membership["plan"]
        }
    )
    
    return jsonify(membership), 201


@app.route("/workouts/<workout_id>/complete", methods=["POST"])
def complete_workout(workout_id):
    """Mark workout as complete and publish event."""
    completion_data = request.json
    
    publisher.publish_sync(
        event_type="workout",
        data={
            "action": "completed",
            "workout_id": workout_id,
            "duration_seconds": completion_data.get("duration_seconds"),
            "calories_burned": completion_data.get("calories_burned")
        }
    )
    
    return jsonify({"status": "completed"}), 200


if __name__ == "__main__":
    app.run(debug=True)
