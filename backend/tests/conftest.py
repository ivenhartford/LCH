import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db

import tempfile
import shutil


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    static_folder = tempfile.mkdtemp()

    app = create_app(
        config_overrides={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "STATIC_FOLDER": static_folder,
            "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
        }
    )

    with open(os.path.join(static_folder, "index.html"), "w") as f:
        f.write("test")

    with app.app_context():
        db.create_all()

    yield app

    # Clean up database after test
    with app.app_context():
        db.session.remove()
        db.drop_all()

    shutil.rmtree(static_folder)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(autouse=True)
def reset_db(app):
    """
    Automatically reset database session after each test.
    This prevents "Working outside of application context" errors
    during fixture teardown.
    """
    yield
    # Clean up any remaining database sessions
    with app.app_context():
        db.session.remove()


@pytest.fixture
def test_user(app):
    """Create a test user for authentication"""
    from app.models import User

    with app.app_context():
        user = User(username="testuser", role="user")
        user.set_password("testpassword123")
        db.session.add(user)
        db.session.commit()

        # Return the user object (need to refresh to access outside context)
        user_id = user.id
        user_username = user.username
        user_role = user.role

    # Return a fresh user object accessible outside app context
    with app.app_context():
        return db.session.get(User, user_id)


@pytest.fixture
def auth_headers(app, client, test_user):
    """
    Create authenticated session for the test client.
    Note: This returns an empty dict because authentication is session-based,
    but the login is performed so the client has an authenticated session.
    """
    # Log in the test user to establish session
    response = client.post(
        "/api/login",
        json={"username": "testuser", "password": "testpassword123"}
    )

    if response.status_code != 200:
        # Better error message with status code
        error_msg = f"Login failed with status {response.status_code}: {response.get_json() or response.data}"
        print(f"DEBUG: {error_msg}")
        raise Exception(error_msg)

    # Return empty dict (headers not used for session auth, but tests expect this parameter)
    return {}


@pytest.fixture
def test_patient(app, test_user):
    """Create a test patient with owner for testing"""
    from app.models import Client, Patient

    with app.app_context():
        # Create a client (owner) first
        client_obj = Client(
            first_name="Test",
            last_name="Owner",
            email="testowner@example.com",
            phone_primary="555-0100"
        )
        db.session.add(client_obj)
        db.session.flush()

        # Create a patient
        patient = Patient(
            name="Test Patient",
            species="Dog",
            breed="Labrador",
            sex="Male",
            owner_id=client_obj.id,
            status="Active"
        )
        db.session.add(patient)
        db.session.commit()

        patient_id = patient.id

    # Return fresh patient object accessible outside app context
    with app.app_context():
        return db.session.get(Patient, patient_id)


@pytest.fixture
def session(app):
    """Provide database session within app context"""
    with app.app_context():
        yield db.session
