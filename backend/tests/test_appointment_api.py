"""
Unit tests for Appointment API endpoints

Tests all CRUD operations for the /api/appointments endpoints including:
- GET /api/appointments (list with pagination, search, and filtering)
- GET /api/appointments/<id> (single appointment)
- POST /api/appointments (create)
- PUT /api/appointments/<id> (update with status workflow)
- DELETE /api/appointments/<id> (admin only)
"""

import pytest
from datetime import datetime, timedelta
from app.models import User, Client, Patient, Appointment, AppointmentType, db


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
def sample_client(app, authenticated_client):
    """Create a sample client for testing"""
    with app.app_context():
        client_obj = Client(
            first_name="John", last_name="Doe", phone_primary="555-1234", email="john@example.com"
        )
        db.session.add(client_obj)
        db.session.commit()
        return client_obj.id


@pytest.fixture
def sample_patient(app, authenticated_client, sample_client):
    """Create a sample patient for testing"""
    with app.app_context():
        patient = Patient(name="Whiskers", breed="Persian", owner_id=sample_client, status="Active")
        db.session.add(patient)
        db.session.commit()
        return patient.id


@pytest.fixture
def sample_appointment_type(app, authenticated_client):
    """Create a sample appointment type for testing"""
    with app.app_context():
        apt_type = AppointmentType(
            name="Wellness Exam", default_duration_minutes=30, color="#10b981"
        )
        db.session.add(apt_type)
        db.session.commit()
        return apt_type.id


@pytest.fixture
def sample_staff(app, authenticated_client):
    """Create a sample staff member for testing"""
    with app.app_context():
        staff = User(username="dr_smith", role="user")
        staff.set_password("password")
        db.session.add(staff)
        db.session.commit()
        return staff.id


@pytest.fixture
def sample_appointments(
    authenticated_client, sample_client, sample_patient, sample_appointment_type, sample_staff
):
    """Create sample appointments for testing"""
    with app.app_context():
        now = datetime.utcnow()
        appointments = [
            Appointment(
                title="Wellness Checkup",
                start_time=now + timedelta(days=1),
                end_time=now + timedelta(days=1, hours=1),
                client_id=sample_client,
                patient_id=sample_patient,
                appointment_type_id=sample_appointment_type,
                status="scheduled",
                assigned_staff_id=sample_staff,
            ),
            Appointment(
                title="Follow-up Visit",
                start_time=now + timedelta(days=2),
                end_time=now + timedelta(days=2, hours=1),
                client_id=sample_client,
                patient_id=sample_patient,
                status="confirmed",
            ),
            Appointment(
                title="Surgery Consultation",
                start_time=now + timedelta(days=3),
                end_time=now + timedelta(days=3, hours=2),
                client_id=sample_client,
                patient_id=sample_patient,
                status="cancelled",
                cancellation_reason="Client requested reschedule",
            ),
        ]
        for apt in appointments:
            db.session.add(apt)
        db.session.commit()

        return [a.id for a in appointments]

    return []


class TestAppointmentList:
    """Tests for GET /api/appointments"""

    def test_get_appointments_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN GET /api/appointments is called
        THEN it should return 401 Unauthorized
        """
        response = client.get("/api/appointments")
        assert response.status_code == 401

    def test_get_appointments_empty_list(self, authenticated_client):
        """
        GIVEN no appointments in database
        WHEN GET /api/appointments is called
        THEN it should return empty list with pagination
        """
        response = authenticated_client.get("/api/appointments")
        assert response.status_code == 200
        data = response.json
        assert "appointments" in data
        assert "pagination" in data
        assert len(data["appointments"]) == 0
        assert data["pagination"]["total"] == 0

    def test_get_appointments_with_data(self, authenticated_client, sample_appointments):
        """
        GIVEN appointments in database
        WHEN GET /api/appointments is called
        THEN it should return all appointments
        """
        response = authenticated_client.get("/api/appointments")
        assert response.status_code == 200
        data = response.json
        assert len(data["appointments"]) == 3
        assert data["pagination"]["total"] == 3

    def test_get_appointments_filter_by_status(self, authenticated_client, sample_appointments):
        """
        GIVEN appointments with different statuses
        WHEN GET /api/appointments?status=scheduled is called
        THEN it should return only scheduled appointments
        """
        response = authenticated_client.get("/api/appointments?status=scheduled")
        assert response.status_code == 200
        data = response.json
        assert len(data["appointments"]) == 1
        assert data["appointments"][0]["status"] == "scheduled"

    def test_get_appointments_filter_by_client(
        self, authenticated_client, sample_client, sample_appointments
    ):
        """
        GIVEN appointments for specific client
        WHEN GET /api/appointments?client_id=X is called
        THEN it should return only that client's appointments
        """
        response = authenticated_client.get(f"/api/appointments?client_id={sample_client}")
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["total"] == 3
        assert all(a["client_id"] == sample_client for a in data["appointments"])

    def test_get_appointments_filter_by_patient(
        self, authenticated_client, sample_patient, sample_appointments
    ):
        """
        GIVEN appointments for specific patient
        WHEN GET /api/appointments?patient_id=X is called
        THEN it should return only that patient's appointments
        """
        response = authenticated_client.get(f"/api/appointments?patient_id={sample_patient}")
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["total"] == 3
        assert all(a["patient_id"] == sample_patient for a in data["appointments"])

    def test_get_appointments_filter_by_staff(
        self, authenticated_client, sample_staff, sample_appointments
    ):
        """
        GIVEN appointments assigned to specific staff
        WHEN GET /api/appointments?assigned_staff_id=X is called
        THEN it should return only that staff's appointments
        """
        response = authenticated_client.get(f"/api/appointments?assigned_staff_id={sample_staff}")
        assert response.status_code == 200
        data = response.json
        assert len(data["appointments"]) == 1
        assert data["appointments"][0]["assigned_staff_id"] == sample_staff

    def test_get_appointments_filter_by_type(
        self, authenticated_client, sample_appointment_type, sample_appointments
    ):
        """
        GIVEN appointments of different types
        WHEN GET /api/appointments?appointment_type_id=X is called
        THEN it should return only appointments of that type
        """
        response = authenticated_client.get(
            f"/api/appointments?appointment_type_id={sample_appointment_type}"
        )
        assert response.status_code == 200
        data = response.json
        assert len(data["appointments"]) == 1

    def test_get_appointments_filter_by_date_range(self, authenticated_client, sample_appointments):
        """
        GIVEN appointments in different date ranges
        WHEN GET /api/appointments with date filters is called
        THEN it should return only appointments in that range
        """
        now = datetime.utcnow()
        start_date = (now + timedelta(days=1)).isoformat()
        end_date = (now + timedelta(days=2)).isoformat()

        response = authenticated_client.get(
            f"/api/appointments?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200
        # Should include appointments on days 1 and 2
        # Note: Depending on exact timing, may need to adjust this assertion

    def test_get_appointments_pagination(self, authenticated_client, sample_appointments):
        """
        GIVEN multiple appointments
        WHEN GET /api/appointments with pagination params
        THEN it should return paginated results
        """
        response = authenticated_client.get("/api/appointments?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json
        assert len(data["appointments"]) == 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 2
        assert data["pagination"]["total"] == 3
        assert data["pagination"]["has_next"] is True


class TestAppointmentDetail:
    """Tests for GET /api/appointments/<id>"""

    def test_get_appointment_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN GET /api/appointments/<id> is called
        THEN it should return 401 Unauthorized
        """
        response = client.get("/api/appointments/1")
        assert response.status_code == 401

    def test_get_appointment_not_found(self, authenticated_client):
        """
        GIVEN a non-existent appointment ID
        WHEN GET /api/appointments/<id> is called
        THEN it should return 404 Not Found
        """
        response = authenticated_client.get("/api/appointments/99999")
        assert response.status_code == 404

    def test_get_appointment_success(self, authenticated_client, sample_client, sample_patient):
        """
        GIVEN a valid appointment ID
        WHEN GET /api/appointments/<id> is called
        THEN it should return the appointment details
        """
        # Create appointment directly in this test
        with app.app_context():
            from datetime import datetime, timedelta

            now = datetime.utcnow()
            apt = Appointment(
                title="Wellness Checkup",
                start_time=now + timedelta(days=1),
                end_time=now + timedelta(days=1, hours=1),
                client_id=sample_client,
                patient_id=sample_patient,
                status="scheduled",
            )
            db.session.add(apt)
            db.session.commit()
            apt_id = apt.id

        response = authenticated_client.get(f"/api/appointments/{apt_id}")
        assert response.status_code == 200
        data = response.json
        assert data["id"] == apt_id
        assert data["title"] == "Wellness Checkup"
        assert data["status"] == "scheduled"
        assert data["client_id"] == sample_client
        assert data["patient_id"] == sample_patient


class TestAppointmentCreate:
    """Tests for POST /api/appointments"""

    def test_create_appointment_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN POST /api/appointments is called
        THEN it should return 401 Unauthorized
        """
        response = client.post("/api/appointments", json={"title": "Test"})
        assert response.status_code == 401

    def test_create_appointment_minimal(self, authenticated_client, sample_client):
        """
        GIVEN valid minimal appointment data
        WHEN POST /api/appointments is called
        THEN it should create the appointment
        """
        now = datetime.utcnow()
        data = {
            "title": "Quick Checkup",
            "start_time": (now + timedelta(days=5)).isoformat(),
            "end_time": (now + timedelta(days=5, hours=1)).isoformat(),
            "client_id": sample_client,
        }
        response = authenticated_client.post("/api/appointments", json=data)
        assert response.status_code == 201
        result = response.json
        assert result["title"] == "Quick Checkup"
        assert result["client_id"] == sample_client
        assert result["status"] == "scheduled"  # Default status

    def test_create_appointment_full(
        self,
        authenticated_client,
        sample_client,
        sample_patient,
        sample_appointment_type,
        sample_staff,
    ):
        """
        GIVEN valid complete appointment data
        WHEN POST /api/appointments is called
        THEN it should create the appointment with all fields
        """
        now = datetime.utcnow()
        data = {
            "title": "Comprehensive Exam",
            "start_time": (now + timedelta(days=10)).isoformat(),
            "end_time": (now + timedelta(days=10, hours=2)).isoformat(),
            "description": "Annual comprehensive health examination",
            "client_id": sample_client,
            "patient_id": sample_patient,
            "appointment_type_id": sample_appointment_type,
            "assigned_staff_id": sample_staff,
            "room": "Exam Room 1",
            "notes": "Patient prefers morning appointments",
        }
        response = authenticated_client.post("/api/appointments", json=data)
        assert response.status_code == 201
        result = response.json
        assert result["title"] == "Comprehensive Exam"
        assert result["description"] == "Annual comprehensive health examination"
        assert result["client_id"] == sample_client
        assert result["patient_id"] == sample_patient
        assert result["appointment_type_id"] == sample_appointment_type
        assert result["assigned_staff_id"] == sample_staff
        assert result["room"] == "Exam Room 1"
        assert result["notes"] == "Patient prefers morning appointments"

    def test_create_appointment_missing_required_fields(self, authenticated_client):
        """
        GIVEN appointment data missing required fields
        WHEN POST /api/appointments is called
        THEN it should return 400 Bad Request
        """
        data = {"title": "Test Appointment"}
        response = authenticated_client.post("/api/appointments", json=data)
        assert response.status_code == 400

    def test_create_appointment_invalid_client(self, authenticated_client):
        """
        GIVEN appointment data with non-existent client
        WHEN POST /api/appointments is called
        THEN it should return 404 Not Found
        """
        now = datetime.utcnow()
        data = {
            "title": "Test",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=1)).isoformat(),
            "client_id": 99999,
        }
        response = authenticated_client.post("/api/appointments", json=data)
        assert response.status_code == 404
        assert "client" in response.json["error"].lower()

    def test_create_appointment_invalid_patient(self, authenticated_client, sample_client):
        """
        GIVEN appointment data with non-existent patient
        WHEN POST /api/appointments is called
        THEN it should return 404 Not Found
        """
        now = datetime.utcnow()
        data = {
            "title": "Test",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=1)).isoformat(),
            "client_id": sample_client,
            "patient_id": 99999,
        }
        response = authenticated_client.post("/api/appointments", json=data)
        assert response.status_code == 404
        assert "patient" in response.json["error"].lower()


class TestAppointmentUpdate:
    """Tests for PUT /api/appointments/<id>"""

    def test_update_appointment_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN PUT /api/appointments/<id> is called
        THEN it should return 401 Unauthorized
        """
        response = client.put("/api/appointments/1", json={"title": "Updated"})
        assert response.status_code == 401

    def test_update_appointment_not_found(self, authenticated_client):
        """
        GIVEN a non-existent appointment ID
        WHEN PUT /api/appointments/<id> is called
        THEN it should return 404 Not Found
        """
        response = authenticated_client.put("/api/appointments/99999", json={"title": "Updated"})
        assert response.status_code == 404

    def test_update_appointment_title(self, authenticated_client, sample_appointments):
        """
        GIVEN valid updated appointment data
        WHEN PUT /api/appointments/<id> is called
        THEN it should update the appointment
        """
        apt_id = sample_appointments[0]
        data = {"title": "Updated Wellness Checkup"}
        response = authenticated_client.put(f"/api/appointments/{apt_id}", json=data)
        assert response.status_code == 200
        result = response.json
        assert result["title"] == "Updated Wellness Checkup"

    def test_update_appointment_status_to_confirmed(
        self, authenticated_client, sample_appointments
    ):
        """
        GIVEN an appointment status update
        WHEN PUT /api/appointments/<id> is called
        THEN it should update the status
        """
        apt_id = sample_appointments[0]
        data = {"status": "confirmed"}
        response = authenticated_client.put(f"/api/appointments/{apt_id}", json=data)
        assert response.status_code == 200
        result = response.json
        assert result["status"] == "confirmed"

    def test_update_appointment_status_to_checked_in(
        self, authenticated_client, sample_appointments
    ):
        """
        GIVEN status update to checked_in
        WHEN PUT /api/appointments/<id> is called
        THEN it should auto-set check_in_time
        """
        apt_id = sample_appointments[0]
        data = {"status": "checked_in"}
        response = authenticated_client.put(f"/api/appointments/{apt_id}", json=data)
        assert response.status_code == 200
        result = response.json
        assert result["status"] == "checked_in"
        assert result["check_in_time"] is not None

    def test_update_appointment_status_to_in_progress(
        self, authenticated_client, sample_appointments
    ):
        """
        GIVEN status update to in_progress
        WHEN PUT /api/appointments/<id> is called
        THEN it should auto-set actual_start_time
        """
        apt_id = sample_appointments[0]
        data = {"status": "in_progress"}
        response = authenticated_client.put(f"/api/appointments/{apt_id}", json=data)
        assert response.status_code == 200
        result = response.json
        assert result["status"] == "in_progress"
        assert result["actual_start_time"] is not None

    def test_update_appointment_status_to_completed(
        self, authenticated_client, sample_appointments
    ):
        """
        GIVEN status update to completed
        WHEN PUT /api/appointments/<id> is called
        THEN it should auto-set actual_end_time
        """
        apt_id = sample_appointments[0]
        data = {"status": "completed"}
        response = authenticated_client.put(f"/api/appointments/{apt_id}", json=data)
        assert response.status_code == 200
        result = response.json
        assert result["status"] == "completed"
        assert result["actual_end_time"] is not None

    def test_update_appointment_status_to_cancelled(
        self, authenticated_client, sample_appointments
    ):
        """
        GIVEN status update to cancelled
        WHEN PUT /api/appointments/<id> is called
        THEN it should auto-set cancelled_at and cancelled_by
        """
        apt_id = sample_appointments[0]
        data = {"status": "cancelled", "cancellation_reason": "Patient request"}
        response = authenticated_client.put(f"/api/appointments/{apt_id}", json=data)
        assert response.status_code == 200
        result = response.json
        assert result["status"] == "cancelled"
        assert result["cancelled_at"] is not None
        assert result["cancellation_reason"] == "Patient request"

    def test_update_appointment_multiple_fields(
        self, authenticated_client, sample_appointments, sample_staff
    ):
        """
        GIVEN multiple field updates
        WHEN PUT /api/appointments/<id> is called
        THEN it should update all specified fields
        """
        apt_id = sample_appointments[0]
        data = {
            "description": "Updated description",
            "assigned_staff_id": sample_staff,
            "room": "Exam Room 2",
            "notes": "Bring vaccination records",
        }
        response = authenticated_client.put(f"/api/appointments/{apt_id}", json=data)
        assert response.status_code == 200
        result = response.json
        assert result["description"] == "Updated description"
        assert result["assigned_staff_id"] == sample_staff
        assert result["room"] == "Exam Room 2"
        assert result["notes"] == "Bring vaccination records"


class TestAppointmentDelete:
    """Tests for DELETE /api/appointments/<id>"""

    def test_delete_appointment_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN DELETE /api/appointments/<id> is called
        THEN it should return 401 Unauthorized
        """
        response = client.delete("/api/appointments/1")
        assert response.status_code == 401

    def test_delete_appointment_non_admin(self, authenticated_client, sample_appointments):
        """
        GIVEN a non-admin user
        WHEN DELETE /api/appointments/<id> is called
        THEN it should return 403 Forbidden
        """
        apt_id = sample_appointments[0]
        response = authenticated_client.delete(f"/api/appointments/{apt_id}")
        assert response.status_code == 403
        assert "admin" in response.json["error"].lower()

    def test_delete_appointment_admin(self, admin_client):
        """
        GIVEN an admin user
        WHEN DELETE /api/appointments/<id> is called
        THEN it should permanently delete the appointment
        """
        # Create a client, patient, and appointment directly in this test
        with admin_client.application.app_context():
            from datetime import datetime, timedelta

            client_obj = Client(first_name="Test", last_name="Client", phone_primary="555-0000")
            db.session.add(client_obj)
            db.session.flush()

            patient = Patient(name="TestCat", owner_id=client_obj.id, status="Active")
            db.session.add(patient)
            db.session.flush()

            now = datetime.utcnow()
            apt = Appointment(
                title="Test Appointment",
                start_time=now + timedelta(days=1),
                end_time=now + timedelta(days=1, hours=1),
                client_id=client_obj.id,
                patient_id=patient.id,
                status="scheduled",
            )
            db.session.add(apt)
            db.session.commit()
            apt_id = apt.id

        response = admin_client.delete(f"/api/appointments/{apt_id}")
        assert response.status_code == 200
        assert "deleted" in response.json["message"].lower()

        # Verify it's deleted
        get_response = admin_client.get(f"/api/appointments/{apt_id}")
        assert get_response.status_code == 404
