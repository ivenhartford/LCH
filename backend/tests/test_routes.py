def test_index_route(client):
    """
    GIVEN a Flask application configured for testing (API-only backend)
    WHEN the '/' route is requested (GET)
    THEN check that the response returns 404 (no root route in API)
    """
    response = client.get("/")
    assert response.status_code == 404  # API-only backend, no root route


def test_create_and_get_appointment(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/appointments' route is posted to (POST)
    THEN check that the response is valid and the appointment is created
    """
    # To test a protected route, we need to be logged in.
    # We can't do that without a user, so let's create one.
    from app.models import User, db

    with app.app_context():
        user = User(username="testuser", role="user")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

    client.post("/api/login", json={"username": "testuser", "password": "password"})

    # Create a client first (required for appointments)
    from app.models import Client

    with app.app_context():
        test_client = Client(first_name="Test", last_name="Client", phone_primary="555-1234")
        db.session.add(test_client)
        db.session.commit()
        client_id = test_client.id

    response = client.post(
        "/api/appointments",
        json={
            "title": "Test Appointment",
            "start_time": "2025-01-01T10:00:00",
            "end_time": "2025-01-01T11:00:00",
            "client_id": client_id,
            "notes": "A test appointment",
        },
    )
    assert response.status_code == 201

    response = client.get("/api/appointments")
    assert response.status_code == 200
    assert "appointments" in response.json
    assert len(response.json["appointments"]) == 1
    assert response.json["appointments"][0]["title"] == "Test Appointment"
