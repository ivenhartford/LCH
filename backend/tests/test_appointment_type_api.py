"""
Unit tests for AppointmentType API endpoints

Tests all CRUD operations for the /api/appointment-types endpoints including:
- GET /api/appointment-types (list with filtering)
- GET /api/appointment-types/<id> (single type)
- POST /api/appointment-types (create)
- PUT /api/appointment-types/<id> (update)
- DELETE /api/appointment-types/<id> (soft and hard delete)
"""

import pytest
from app.models import User, AppointmentType, db


@pytest.fixture
def authenticated_client(client):
    """Create authenticated test client with logged-in user"""
    with client.application.app_context():
        user = User(username="testuser", role="user")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

    client.post("/api/login", json={"username": "testuser", "password": "password"})
    return client


@pytest.fixture
def admin_client(app):
    """Create authenticated test client with admin user"""
    with app.app_context():
        admin = User(username="admin", role="administrator")
        admin.set_password("password")
        db.session.add(admin)
        db.session.commit()

    test_client = app.test_client()
    test_client.post("/api/login", json={"username": "admin", "password": "password"})
    return test_client


@pytest.fixture
def sample_appointment_types(authenticated_client):
    """Create sample appointment types for testing"""
    with authenticated_client.application.app_context():
        types = [
            AppointmentType(
                name="Wellness Exam",
                description="Annual wellness checkup",
                default_duration_minutes=30,
                color="#10b981",
                is_active=True,
            ),
            AppointmentType(
                name="Surgery",
                description="Surgical procedure",
                default_duration_minutes=120,
                color="#ef4444",
                is_active=True,
            ),
            AppointmentType(
                name="Emergency",
                description="Emergency visit",
                default_duration_minutes=60,
                color="#f59e0b",
                is_active=True,
            ),
            AppointmentType(
                name="Deprecated Type",
                description="No longer used",
                default_duration_minutes=30,
                color="#6b7280",
                is_active=False,
            ),
        ]
        for apt_type in types:
            db.session.add(apt_type)
        db.session.commit()

        return [t.id for t in types]

    return []


class TestAppointmentTypeList:
    """Tests for GET /api/appointment-types"""

    def test_get_appointment_types_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN GET /api/appointment-types is called
        THEN it should return 401 Unauthorized
        """
        response = client.get("/api/appointment-types")
        assert response.status_code == 401

    def test_get_appointment_types_empty_list(self, authenticated_client):
        """
        GIVEN no appointment types in database
        WHEN GET /api/appointment-types is called
        THEN it should return empty list
        """
        response = authenticated_client.get("/api/appointment-types")
        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_appointment_types_with_data(self, authenticated_client, sample_appointment_types):
        """
        GIVEN appointment types in database
        WHEN GET /api/appointment-types is called
        THEN it should return active types by default
        """
        response = authenticated_client.get("/api/appointment-types")
        assert response.status_code == 200
        data = response.json
        assert len(data) == 3  # Only active types
        assert all(t["is_active"] for t in data)

    def test_get_appointment_types_include_inactive(
        self, authenticated_client, sample_appointment_types
    ):
        """
        GIVEN appointment types with mixed active status
        WHEN GET /api/appointment-types?active_only=false is called
        THEN it should return all types
        """
        response = authenticated_client.get("/api/appointment-types?active_only=false")
        assert response.status_code == 200
        data = response.json
        assert len(data) == 4  # All types including inactive

    def test_get_appointment_types_ordered_by_name(
        self, authenticated_client, sample_appointment_types
    ):
        """
        GIVEN appointment types in database
        WHEN GET /api/appointment-types is called
        THEN it should return types ordered alphabetically by name
        """
        response = authenticated_client.get("/api/appointment-types")
        assert response.status_code == 200
        data = response.json
        names = [t["name"] for t in data]
        assert names == sorted(names)


class TestAppointmentTypeDetail:
    """Tests for GET /api/appointment-types/<id>"""

    def test_get_appointment_type_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN GET /api/appointment-types/<id> is called
        THEN it should return 401 Unauthorized
        """
        response = client.get("/api/appointment-types/1")
        assert response.status_code == 401

    def test_get_appointment_type_not_found(self, authenticated_client):
        """
        GIVEN a non-existent appointment type ID
        WHEN GET /api/appointment-types/<id> is called
        THEN it should return 404 Not Found
        """
        response = authenticated_client.get("/api/appointment-types/99999")
        assert response.status_code == 404

    def test_get_appointment_type_success(self, authenticated_client, sample_appointment_types):
        """
        GIVEN a valid appointment type ID
        WHEN GET /api/appointment-types/<id> is called
        THEN it should return the appointment type details
        """
        apt_type_id = sample_appointment_types[0]
        response = authenticated_client.get(f"/api/appointment-types/{apt_type_id}")
        assert response.status_code == 200
        data = response.json
        assert data["id"] == apt_type_id
        assert data["name"] == "Wellness Exam"
        assert data["default_duration_minutes"] == 30
        assert data["color"] == "#10b981"


class TestAppointmentTypeCreate:
    """Tests for POST /api/appointment-types"""

    def test_create_appointment_type_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN POST /api/appointment-types is called
        THEN it should return 401 Unauthorized
        """
        response = client.post("/api/appointment-types", json={"name": "Test"})
        assert response.status_code == 401

    def test_create_appointment_type_minimal(self, authenticated_client):
        """
        GIVEN valid minimal appointment type data
        WHEN POST /api/appointment-types is called
        THEN it should create the appointment type
        """
        data = {"name": "Vaccination"}
        response = authenticated_client.post("/api/appointment-types", json=data)
        assert response.status_code == 201
        result = response.json
        assert result["name"] == "Vaccination"
        assert result["default_duration_minutes"] == 30  # Default value
        assert result["color"] == "#2563eb"  # Default color
        assert result["is_active"] is True

    def test_create_appointment_type_full(self, authenticated_client):
        """
        GIVEN valid complete appointment type data
        WHEN POST /api/appointment-types is called
        THEN it should create the appointment type with all fields
        """
        data = {
            "name": "Dental Cleaning",
            "description": "Professional dental cleaning",
            "default_duration_minutes": 45,
            "color": "#8b5cf6",
            "is_active": True,
        }
        response = authenticated_client.post("/api/appointment-types", json=data)
        assert response.status_code == 201
        result = response.json
        assert result["name"] == "Dental Cleaning"
        assert result["description"] == "Professional dental cleaning"
        assert result["default_duration_minutes"] == 45
        assert result["color"] == "#8b5cf6"

    def test_create_appointment_type_duplicate_name(
        self, authenticated_client, sample_appointment_types
    ):
        """
        GIVEN an appointment type name that already exists
        WHEN POST /api/appointment-types is called
        THEN it should return 409 Conflict
        """
        data = {"name": "Wellness Exam"}
        response = authenticated_client.post("/api/appointment-types", json=data)
        assert response.status_code == 409
        assert "already exists" in response.json["error"].lower()

    def test_create_appointment_type_invalid_color(self, authenticated_client):
        """
        GIVEN invalid hex color format
        WHEN POST /api/appointment-types is called
        THEN it should return 400 Bad Request
        """
        data = {"name": "Test Type", "color": "invalid"}
        response = authenticated_client.post("/api/appointment-types", json=data)
        assert response.status_code == 400

    def test_create_appointment_type_missing_name(self, authenticated_client):
        """
        GIVEN appointment type data without name
        WHEN POST /api/appointment-types is called
        THEN it should return 400 Bad Request
        """
        data = {"description": "Test"}
        response = authenticated_client.post("/api/appointment-types", json=data)
        assert response.status_code == 400


class TestAppointmentTypeUpdate:
    """Tests for PUT /api/appointment-types/<id>"""

    def test_update_appointment_type_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN PUT /api/appointment-types/<id> is called
        THEN it should return 401 Unauthorized
        """
        response = client.put("/api/appointment-types/1", json={"name": "Updated"})
        assert response.status_code == 401

    def test_update_appointment_type_not_found(self, authenticated_client):
        """
        GIVEN a non-existent appointment type ID
        WHEN PUT /api/appointment-types/<id> is called
        THEN it should return 404 Not Found
        """
        response = authenticated_client.put(
            "/api/appointment-types/99999", json={"name": "Updated"}
        )
        assert response.status_code == 404

    def test_update_appointment_type_name(self, authenticated_client, sample_appointment_types):
        """
        GIVEN valid updated appointment type data
        WHEN PUT /api/appointment-types/<id> is called
        THEN it should update the appointment type
        """
        apt_type_id = sample_appointment_types[0]
        data = {"name": "Annual Wellness Exam"}
        response = authenticated_client.put(f"/api/appointment-types/{apt_type_id}", json=data)
        assert response.status_code == 200
        result = response.json
        assert result["name"] == "Annual Wellness Exam"

    def test_update_appointment_type_multiple_fields(
        self, authenticated_client, sample_appointment_types
    ):
        """
        GIVEN multiple field updates
        WHEN PUT /api/appointment-types/<id> is called
        THEN it should update all specified fields
        """
        apt_type_id = sample_appointment_types[0]
        data = {
            "description": "Updated description",
            "default_duration_minutes": 60,
            "color": "#3b82f6",
        }
        response = authenticated_client.put(f"/api/appointment-types/{apt_type_id}", json=data)
        assert response.status_code == 200
        result = response.json
        assert result["description"] == "Updated description"
        assert result["default_duration_minutes"] == 60
        assert result["color"] == "#3b82f6"

    def test_update_appointment_type_duplicate_name(
        self, authenticated_client, sample_appointment_types
    ):
        """
        GIVEN a name that conflicts with another type
        WHEN PUT /api/appointment-types/<id> is called
        THEN it should return 409 Conflict
        """
        apt_type_id = sample_appointment_types[0]
        data = {"name": "Surgery"}  # Already exists
        response = authenticated_client.put(f"/api/appointment-types/{apt_type_id}", json=data)
        assert response.status_code == 409


class TestAppointmentTypeDelete:
    """Tests for DELETE /api/appointment-types/<id>"""

    def test_delete_appointment_type_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN DELETE /api/appointment-types/<id> is called
        THEN it should return 401 Unauthorized
        """
        response = client.delete("/api/appointment-types/1")
        assert response.status_code == 401

    def test_soft_delete_appointment_type(self, authenticated_client, sample_appointment_types):
        """
        GIVEN a valid appointment type ID
        WHEN DELETE /api/appointment-types/<id> is called (soft delete)
        THEN it should deactivate the appointment type
        """
        apt_type_id = sample_appointment_types[0]
        response = authenticated_client.delete(f"/api/appointment-types/{apt_type_id}")
        assert response.status_code == 200
        assert "deactivated" in response.json["message"].lower()

        # Verify it's deactivated
        get_response = authenticated_client.get(f"/api/appointment-types/{apt_type_id}")
        assert get_response.json["is_active"] is False

    def test_hard_delete_appointment_type_non_admin(
        self, authenticated_client, sample_appointment_types
    ):
        """
        GIVEN a non-admin user
        WHEN DELETE /api/appointment-types/<id>?hard=true is called
        THEN it should return 403 Forbidden
        """
        apt_type_id = sample_appointment_types[0]
        response = authenticated_client.delete(f"/api/appointment-types/{apt_type_id}?hard=true")
        assert response.status_code == 403

    def test_hard_delete_appointment_type_admin(self, admin_client):
        """
        GIVEN an admin user
        WHEN DELETE /api/appointment-types/<id>?hard=true is called
        THEN it should permanently delete the appointment type
        """
        # Create an appointment type directly in this test
        with admin_client.application.app_context():
            apt_type = AppointmentType(name="Test Type", default_duration_minutes=30)
            db.session.add(apt_type)
            db.session.commit()
            apt_type_id = apt_type.id

        response = admin_client.delete(f"/api/appointment-types/{apt_type_id}?hard=true")
        assert response.status_code == 200
        assert "permanently deleted" in response.json["message"].lower()

        # Verify it's deleted
        get_response = admin_client.get(f"/api/appointment-types/{apt_type_id}")
        assert get_response.status_code == 404
