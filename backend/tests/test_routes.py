def test_index_route(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' route is requested (GET)
    THEN check that the response is valid
    """
    response = client.get('/')
    assert response.status_code == 200

def test_create_and_get_appointment(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/appointments' route is posted to (POST)
    THEN check that the response is valid and the appointment is created
    """
    # To test a protected route, we need to be logged in.
    # We can't do that without a user, so let's create one.
    from app.models import User, db

    with client.application.app_context():
        user = User(username='testuser', role='user')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

    client.post('/api/login', json={'username': 'testuser', 'password': 'password'})

    response = client.post('/api/appointments', json={
        'title': 'Test Appointment',
        'start': '2025-01-01T10:00:00',
        'end': '2025-01-01T11:00:00',
        'description': 'A test appointment'
    })
    assert response.status_code == 201

    response = client.get('/api/appointments')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['title'] == 'Test Appointment'
