"""
Unit tests for Client Portal API endpoints

Tests all client portal operations including:
- POST /api/portal/register (registration)
- POST /api/portal/login (login)
- GET /api/portal/dashboard/<client_id> (dashboard data)
- GET /api/portal/patients/<client_id> (patient list)
- GET /api/portal/patients/<client_id>/<patient_id> (patient details)
- GET /api/portal/appointments/<client_id> (appointment history)
- GET /api/portal/invoices/<client_id> (invoice history)
- GET /api/portal/invoices/<client_id>/<invoice_id> (invoice details)
- POST /api/portal/appointment-requests (create request)
- GET /api/portal/appointment-requests/<client_id> (list requests)
- GET /api/portal/appointment-requests/<client_id>/<request_id> (request details)
- POST /api/portal/appointment-requests/<client_id>/<request_id>/cancel (cancel request)
- GET /api/appointment-requests (staff view)
- GET /api/appointment-requests/<request_id> (staff view details)
- PUT /api/appointment-requests/<request_id>/review (staff review)
"""

import pytest
from datetime import datetime, timedelta, date
from app.models import (
    User,
    Client,
    Patient,
    Appointment,
    AppointmentType,
    Invoice,
    InvoiceItem,
    ClientPortalUser,
    AppointmentRequest,
    db,
)


@pytest.fixture
def sample_client(app):
    """Create a sample client for testing"""
    with app.app_context():
        client = Client(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone_primary="555-1234",
            city="New York",
        )
        db.session.add(client)
        db.session.commit()
        return client.id


@pytest.fixture
def sample_patient(app, sample_client):
    """Create a sample patient for testing"""
    with app.app_context():
        patient = Patient(name="Fluffy", species="Cat", breed="Persian", owner_id=sample_client)
        db.session.add(patient)
        db.session.commit()
        return patient.id


@pytest.fixture
def sample_appointment_type(app):
    """Create a sample appointment type"""
    with app.app_context():
        apt_type = AppointmentType(name="Wellness Exam", default_duration_minutes=30, is_active=True)
        db.session.add(apt_type)
        db.session.commit()
        return apt_type.id


@pytest.fixture
def sample_appointment(app, sample_client, sample_patient, sample_appointment_type):
    """Create a sample appointment"""
    with app.app_context():
        appointment = Appointment(
            title="Wellness Exam for Fluffy",
            start_time=datetime.utcnow() + timedelta(days=7),
            end_time=datetime.utcnow() + timedelta(days=7, minutes=30),
            client_id=sample_client,
            patient_id=sample_patient,
            appointment_type_id=sample_appointment_type,
            status="scheduled",
            created_at=datetime.utcnow(),
        )
        db.session.add(appointment)
        db.session.commit()
        return appointment.id


@pytest.fixture
def sample_invoice(app, sample_client, sample_patient):
    """Create a sample invoice"""
    with app.app_context():
        # First get a user to create the invoice
        user = User.query.first()
        if not user:
            user = User(username="testuser", role="user")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()

        invoice = Invoice(
            invoice_number="INV-001",
            client_id=sample_client,
            patient_id=sample_patient,
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=100.00,
            tax_amount=8.00,
            tax_rate=0.08,
            discount_amount=0.00,
            total_amount=108.00,
            amount_paid=0.00,
            balance_due=108.00,
            status="unpaid",
            created_by_id=user.id,
        )
        db.session.add(invoice)
        db.session.commit()
        return invoice.id


@pytest.fixture
def portal_user(app, sample_client):
    """Create a portal user"""
    with app.app_context():
        portal_user = ClientPortalUser(
            client_id=sample_client,
            username="johndoe",
            email="johndoe@example.com",
            is_verified=True,  # Set verified to allow login
        )
        portal_user.set_password("Password123!")
        db.session.add(portal_user)
        db.session.commit()
        return portal_user.id


@pytest.fixture
def authenticated_staff(app, client):
    """Create authenticated staff client"""
    with app.app_context():
        user = User(username="staff", role="user")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

    client.post("/api/login", json={"username": "staff", "password": "password"})
    return client


@pytest.fixture
def authenticated_portal_client(app, client, sample_client, portal_user):
    """Create authenticated portal client with JWT token"""
    # Login to get JWT token
    response = client.post("/api/portal/login", json={"username": "johndoe", "password": "Password123!"})
    assert response.status_code == 200
    token = response.get_json()["token"]

    # Create a new client instance with the auth header
    class AuthenticatedClient:
        def __init__(self, base_client, token, client_id):
            self.base_client = base_client
            self.token = token
            self.client_id = client_id

        def get(self, *args, **kwargs):
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
            return self.base_client.get(*args, **kwargs)

        def post(self, *args, **kwargs):
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
            return self.base_client.post(*args, **kwargs)

        def put(self, *args, **kwargs):
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
            return self.base_client.put(*args, **kwargs)

        def delete(self, *args, **kwargs):
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
            return self.base_client.delete(*args, **kwargs)

    return AuthenticatedClient(client, token, sample_client)


class TestPortalRegistration:
    """Tests for POST /api/portal/register"""

    def test_successful_registration(self, client, sample_client):
        """Test successful portal user registration"""
        response = client.post(
            "/api/portal/register",
            json={
                "client_id": sample_client,
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "Password123!",
                "password_confirm": "Password123!",
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert "Registration successful" in data["message"]
        assert data["user"]["username"] == "newuser"

    def test_registration_password_mismatch(self, app, client, sample_client):
        """Test registration with mismatched passwords"""
        response = client.post(
            "/api/portal/register",
            json={
                "client_id": sample_client,
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "Password123!",
                "password_confirm": "Different456!",
            },
        )

        assert response.status_code == 400
        assert "Passwords do not match" in response.get_json()["error"]

    def test_registration_duplicate_username(self, app, client, sample_client, portal_user):
        """Test registration with duplicate username"""
        # Create a second client
        with app.app_context():
            client2 = Client(
                first_name="Jane",
                last_name="Smith",
                email="jane@example.com",
                phone_primary="555-5678",
            )
            db.session.add(client2)
            db.session.commit()
            client2_id = client2.id

        response = client.post(
            "/api/portal/register",
            json={
                "client_id": client2_id,  # Different client
                "username": "johndoe",  # Same username as portal_user
                "email": "different@example.com",
                "password": "Password123!",
                "password_confirm": "Password123!",
            },
        )

        assert response.status_code == 400
        assert "Username already taken" in response.get_json()["error"]

    def test_registration_duplicate_client(self, client, sample_client, portal_user):
        """Test registration for client that already has portal account"""
        response = client.post(
            "/api/portal/register",
            json={
                "client_id": sample_client,  # Same client as portal_user
                "username": "different",
                "email": "different@example.com",
                "password": "Password123!",
                "password_confirm": "Password123!",
            },
        )

        assert response.status_code == 400
        assert "Portal account already exists" in response.get_json()["error"]


class TestPortalLogin:
    """Tests for POST /api/portal/login"""

    def test_successful_login(self, client, portal_user):
        """Test successful portal login"""
        response = client.post("/api/portal/login", json={"username": "johndoe", "password": "Password123!"})

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Login successful"
        assert data["user"]["username"] == "johndoe"

    def test_login_with_email(self, client, portal_user):
        """Test login using email instead of username"""
        response = client.post(
            "/api/portal/login", json={"username": "johndoe@example.com", "password": "Password123!"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["email"] == "johndoe@example.com"

    def test_login_invalid_credentials(self, client, portal_user):
        """Test login with invalid credentials"""
        response = client.post("/api/portal/login", json={"username": "johndoe", "password": "wrongpassword"})

        assert response.status_code == 401
        assert "Invalid username/email or password" in response.get_json()["error"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post("/api/portal/login", json={"username": "nonexistent", "password": "password"})

        assert response.status_code == 401


class TestPortalDashboard:
    """Tests for GET /api/portal/dashboard/<client_id>"""

    def test_dashboard_data(self, authenticated_portal_client, sample_patient, sample_appointment, sample_invoice):
        """Test fetching dashboard data"""
        response = authenticated_portal_client.get(f"/api/portal/dashboard/{authenticated_portal_client.client_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert "client" in data
        assert "patients" in data
        assert "upcoming_appointments" in data
        assert "recent_invoices" in data
        assert "pending_requests" in data
        assert "account_balance" in data

        # Check that data is populated
        assert len(data["patients"]) > 0
        assert len(data["upcoming_appointments"]) > 0
        assert len(data["recent_invoices"]) > 0

    def test_dashboard_nonexistent_client(self, authenticated_portal_client):
        """Test dashboard for non-existent client"""
        response = authenticated_portal_client.get("/api/portal/dashboard/99999")

        assert response.status_code == 404


class TestPortalPatients:
    """Tests for portal patient endpoints"""

    def test_get_patients(self, authenticated_portal_client, sample_patient):
        """Test fetching client's patients"""
        response = authenticated_portal_client.get(f"/api/portal/patients/{authenticated_portal_client.client_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
        assert data[0]["name"] == "Fluffy"

    def test_get_patient_detail(self, app, authenticated_portal_client, sample_patient):
        """Test fetching specific patient details"""
        response = authenticated_portal_client.get(
            f"/api/portal/patients/{authenticated_portal_client.client_id}/{sample_patient}"
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Fluffy"
        assert data["breed"] == "Persian"

    def test_get_patient_wrong_client(self, app, authenticated_portal_client, sample_patient):
        """Test fetching patient with wrong client_id"""
        # Create a different client
        with app.app_context():
            client2 = Client(
                first_name="Jane",
                last_name="Smith",
                email="jane2@example.com",
                phone_primary="555-9999",
            )
            db.session.add(client2)
            db.session.commit()
            client2_id = client2.id

        response = authenticated_portal_client.get(f"/api/portal/patients/{client2_id}/{sample_patient}")

        assert response.status_code == 404


class TestPortalAppointments:
    """Tests for portal appointment endpoints"""

    def test_get_appointments(self, authenticated_portal_client, sample_appointment):
        """Test fetching client's appointments"""
        response = authenticated_portal_client.get(f"/api/portal/appointments/{authenticated_portal_client.client_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
        assert "Fluffy" in data[0]["title"]


class TestPortalInvoices:
    """Tests for portal invoice endpoints"""

    def test_get_invoices(self, authenticated_portal_client, sample_invoice):
        """Test fetching client's invoices"""
        response = authenticated_portal_client.get(f"/api/portal/invoices/{authenticated_portal_client.client_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
        assert data[0]["invoice_number"] == "INV-001"

    def test_get_invoice_detail(self, app, authenticated_portal_client, sample_invoice):
        """Test fetching specific invoice details"""
        response = authenticated_portal_client.get(
            f"/api/portal/invoices/{authenticated_portal_client.client_id}/{sample_invoice}"
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["invoice"]["invoice_number"] == "INV-001"
        assert "items" in data

    def test_get_invoice_wrong_client(self, app, authenticated_portal_client, sample_invoice):
        """Test fetching invoice with wrong client_id"""
        # Create a different client
        with app.app_context():
            client2 = Client(
                first_name="Jane",
                last_name="Smith",
                email="jane3@example.com",
                phone_primary="555-8888",
            )
            db.session.add(client2)
            db.session.commit()
            client2_id = client2.id

        response = authenticated_portal_client.get(f"/api/portal/invoices/{client2_id}/{sample_invoice}")

        assert response.status_code == 404


class TestAppointmentRequests:
    """Tests for appointment request endpoints"""

    def test_create_appointment_request(self, authenticated_portal_client, sample_patient, sample_appointment_type):
        """Test creating an appointment request"""
        response = authenticated_portal_client.post(
            "/api/portal/appointment-requests",
            json={
                "client_id": authenticated_portal_client.client_id,
                "patient_id": sample_patient,
                "appointment_type_id": sample_appointment_type,
                "requested_date": (date.today() + timedelta(days=7)).isoformat(),
                "requested_time": "morning",
                "reason": "Annual checkup",
                "is_urgent": False,
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "pending"
        assert data["priority"] == "normal"
        assert data["reason"] == "Annual checkup"

    def test_create_urgent_request(self, authenticated_portal_client, sample_patient):
        """Test creating an urgent appointment request"""
        response = authenticated_portal_client.post(
            "/api/portal/appointment-requests",
            json={
                "client_id": authenticated_portal_client.client_id,
                "patient_id": sample_patient,
                "requested_date": date.today().isoformat(),
                "reason": "Cat is injured",
                "is_urgent": True,
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["priority"] == "urgent"
        assert data["is_urgent"] is True

    def test_create_request_invalid_patient(self, app, authenticated_portal_client):
        """Test creating request with invalid patient"""
        response = authenticated_portal_client.post(
            "/api/portal/appointment-requests",
            json={
                "client_id": authenticated_portal_client.client_id,
                "patient_id": 99999,
                "requested_date": date.today().isoformat(),
                "reason": "Test",
            },
        )

        assert response.status_code == 404

    def test_get_client_requests(self, app, authenticated_portal_client, sample_patient):
        """Test fetching client's appointment requests"""
        # Create a request first
        with app.app_context():
            req = AppointmentRequest(
                client_id=authenticated_portal_client.client_id,
                patient_id=sample_patient,
                requested_date=date.today() + timedelta(days=7),
                reason="Test request",
                status="pending",
                priority="normal",
            )
            db.session.add(req)
            db.session.commit()

        response = authenticated_portal_client.get(
            f"/api/portal/appointment-requests/{authenticated_portal_client.client_id}"
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
        assert data[0]["reason"] == "Test request"

    def test_cancel_request(self, app, authenticated_portal_client, sample_patient):
        """Test canceling a pending appointment request"""
        # Create a request first
        with app.app_context():
            req = AppointmentRequest(
                client_id=authenticated_portal_client.client_id,
                patient_id=sample_patient,
                requested_date=date.today() + timedelta(days=7),
                reason="Test request",
                status="pending",
                priority="normal",
            )
            db.session.add(req)
            db.session.commit()
            request_id = req.id

        response = authenticated_portal_client.post(
            f"/api/portal/appointment-requests/{authenticated_portal_client.client_id}/{request_id}/cancel"
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "cancelled"

    def test_cancel_nonpending_request(self, app, authenticated_portal_client, sample_patient):
        """Test canceling a non-pending request (should fail)"""
        # Create an approved request
        with app.app_context():
            req = AppointmentRequest(
                client_id=authenticated_portal_client.client_id,
                patient_id=sample_patient,
                requested_date=date.today() + timedelta(days=7),
                reason="Test request",
                status="approved",
                priority="normal",
            )
            db.session.add(req)
            db.session.commit()
            request_id = req.id

        response = authenticated_portal_client.post(
            f"/api/portal/appointment-requests/{authenticated_portal_client.client_id}/{request_id}/cancel"
        )

        assert response.status_code == 400
        assert "only cancel pending" in response.get_json()["error"].lower()


class TestStaffAppointmentRequests:
    """Tests for staff-side appointment request management"""

    def test_get_all_requests(self, authenticated_staff, sample_client, sample_patient):
        """Test staff fetching all appointment requests"""
        # Create a request
        with authenticated_staff.application.app_context():
            req = AppointmentRequest(
                client_id=sample_client,
                patient_id=sample_patient,
                requested_date=date.today() + timedelta(days=7),
                reason="Test request",
                status="pending",
                priority="high",
            )
            db.session.add(req)
            db.session.commit()

        response = authenticated_staff.get("/api/appointment-requests")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0

    def test_get_requests_by_status(self, authenticated_staff, sample_client, sample_patient):
        """Test filtering requests by status"""
        # Create requests with different statuses
        with authenticated_staff.application.app_context():
            for status in ["pending", "approved", "rejected"]:
                req = AppointmentRequest(
                    client_id=sample_client,
                    patient_id=sample_patient,
                    requested_date=date.today() + timedelta(days=7),
                    reason=f"Test {status}",
                    status=status,
                    priority="normal",
                )
                db.session.add(req)
            db.session.commit()

        response = authenticated_staff.get("/api/appointment-requests?status=pending")

        assert response.status_code == 200
        data = response.get_json()
        assert all(req["status"] == "pending" for req in data)

    def test_review_request_approve(self, authenticated_staff, sample_client, sample_patient):
        """Test staff approving an appointment request"""
        # Create a request
        with authenticated_staff.application.app_context():
            req = AppointmentRequest(
                client_id=sample_client,
                patient_id=sample_patient,
                requested_date=date.today() + timedelta(days=7),
                reason="Test request",
                status="pending",
                priority="normal",
            )
            db.session.add(req)
            db.session.commit()
            request_id = req.id

        response = authenticated_staff.put(
            f"/api/appointment-requests/{request_id}/review",
            json={
                "status": "approved",
                "priority": "high",
                "staff_notes": "Approved for next week",
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "approved"
        assert data["priority"] == "high"
        assert data["staff_notes"] == "Approved for next week"
        assert data["reviewed_by_id"] is not None
        assert data["reviewed_at"] is not None

    def test_review_request_reject(self, authenticated_staff, sample_client, sample_patient):
        """Test staff rejecting an appointment request"""
        # Create a request
        with authenticated_staff.application.app_context():
            req = AppointmentRequest(
                client_id=sample_client,
                patient_id=sample_patient,
                requested_date=date.today() + timedelta(days=7),
                reason="Test request",
                status="pending",
                priority="normal",
            )
            db.session.add(req)
            db.session.commit()
            request_id = req.id

        response = authenticated_staff.put(
            f"/api/appointment-requests/{request_id}/review",
            json={"status": "rejected", "rejection_reason": "No availability"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "rejected"
        assert data["rejection_reason"] == "No availability"
