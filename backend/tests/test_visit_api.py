"""
Unit tests for Visit API endpoints

Tests all CRUD operations for the /api/visits endpoints including:
- GET /api/visits (list with pagination and filtering)
- GET /api/visits/<id> (single visit)
- POST /api/visits (create)
- PUT /api/visits/<id> (update)
- DELETE /api/visits/<id> (delete)
"""

import pytest
from datetime import datetime, timedelta
from app.models import User, Client, Patient, Visit, db


@pytest.fixture
def authenticated_client(client):
    """Create authenticated test client with logged-in user"""
    with client.application.app_context():
        user = User(username="testvet", role="user")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

    client.post("/api/login", json={"username": "testvet", "password": "password"})
    return client


@pytest.fixture
def sample_patient(app):
    """Create sample patient for testing visits"""
    with app.app_context():
        client_obj = Client(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone_primary="555-1234",
        )
        db.session.add(client_obj)
        db.session.flush()

        patient = Patient(name="Fluffy", species="Cat", breed="Persian", owner_id=client_obj.id)
        db.session.add(patient)
        db.session.commit()

        return patient.id


@pytest.fixture
def sample_visits(authenticated_client, sample_patient):
    """Create sample visits for testing"""
    with authenticated_client.application.app_context():
        user = User.query.filter_by(username="testvet").first()
        visits = [
            Visit(
                patient_id=sample_patient,
                visit_type="Wellness",
                status="completed",
                veterinarian_id=user.id,
                chief_complaint="Annual checkup",
                visit_date=datetime.utcnow() - timedelta(days=30),
                completed_at=datetime.utcnow() - timedelta(days=30),
            ),
            Visit(
                patient_id=sample_patient,
                visit_type="Sick",
                status="in_progress",
                veterinarian_id=user.id,
                chief_complaint="Not eating",
                visit_date=datetime.utcnow(),
            ),
            Visit(
                patient_id=sample_patient,
                visit_type="Emergency",
                status="scheduled",
                chief_complaint="Injury",
                visit_date=datetime.utcnow() + timedelta(days=1),
            ),
        ]
        for v in visits:
            db.session.add(v)
        db.session.commit()

        return [v.id for v in visits]


class TestVisitList:
    """Tests for GET /api/visits"""

    def test_get_visits_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN GET /api/visits is called
        THEN it should return 401 Unauthorized
        """
        response = client.get("/api/visits")
        assert response.status_code == 401

    def test_get_visits_empty_list(self, authenticated_client):
        """
        GIVEN no visits in database
        WHEN GET /api/visits is called
        THEN it should return empty list with pagination
        """
        response = authenticated_client.get("/api/visits")
        assert response.status_code == 200
        data = response.json
        assert "visits" in data
        assert len(data["visits"]) == 0
        assert data["total"] == 0

    def test_get_visits_with_data(self, authenticated_client, sample_visits):
        """
        GIVEN visits in database
        WHEN GET /api/visits is called
        THEN it should return all visits ordered by date descending
        """
        response = authenticated_client.get("/api/visits")
        assert response.status_code == 200
        data = response.json
        assert len(data["visits"]) == 3
        assert data["total"] == 3
        # Should be ordered by visit_date desc (future, today, past)
        assert data["visits"][0]["chief_complaint"] == "Injury"

    def test_get_visits_filter_by_patient(
        self, authenticated_client, sample_visits, sample_patient
    ):
        """
        GIVEN visits for multiple patients
        WHEN GET /api/visits?patient_id=X is called
        THEN it should return only visits for that patient
        """
        response = authenticated_client.get(f"/api/visits?patient_id={sample_patient}")
        assert response.status_code == 200
        data = response.json
        assert len(data["visits"]) == 3
        for visit in data["visits"]:
            assert visit["patient_id"] == sample_patient

    def test_get_visits_filter_by_status(self, authenticated_client, sample_visits):
        """
        GIVEN visits with different statuses
        WHEN GET /api/visits?status=completed is called
        THEN it should return only completed visits
        """
        response = authenticated_client.get("/api/visits?status=completed")
        assert response.status_code == 200
        data = response.json
        assert len(data["visits"]) == 1
        assert data["visits"][0]["status"] == "completed"

    def test_get_visits_filter_by_type(self, authenticated_client, sample_visits):
        """
        GIVEN visits with different types
        WHEN GET /api/visits?visit_type=Wellness is called
        THEN it should return only wellness visits
        """
        response = authenticated_client.get("/api/visits?visit_type=Wellness")
        assert response.status_code == 200
        data = response.json
        assert len(data["visits"]) == 1
        assert data["visits"][0]["visit_type"] == "Wellness"

    def test_get_visits_pagination(self, authenticated_client, sample_visits):
        """
        GIVEN multiple visits
        WHEN GET /api/visits?page=1&per_page=2 is called
        THEN it should return paginated results
        """
        response = authenticated_client.get("/api/visits?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json
        assert len(data["visits"]) == 2
        assert data["total"] == 3
        assert data["pages"] == 2


class TestVisitDetail:
    """Tests for GET /api/visits/<id>"""

    def test_get_visit_not_found(self, authenticated_client):
        """
        GIVEN a non-existent visit ID
        WHEN GET /api/visits/<id> is called
        THEN it should return 404
        """
        response = authenticated_client.get("/api/visits/99999")
        assert response.status_code == 404

    def test_get_visit_success(self, authenticated_client, sample_visits):
        """
        GIVEN an existing visit
        WHEN GET /api/visits/<id> is called
        THEN it should return the visit details
        """
        visit_id = sample_visits[0]
        response = authenticated_client.get(f"/api/visits/{visit_id}")
        assert response.status_code == 200
        data = response.json
        assert data["id"] == visit_id
        assert "visit_type" in data
        assert "status" in data
        assert "patient_name" in data


class TestVisitCreate:
    """Tests for POST /api/visits"""

    def test_create_visit_without_auth(self, client, sample_patient):
        """
        GIVEN an unauthenticated request
        WHEN POST /api/visits is called
        THEN it should return 401
        """
        response = client.post(
            "/api/visits",
            json={"patient_id": sample_patient, "visit_type": "Wellness"},
        )
        assert response.status_code == 401

    def test_create_visit_invalid_patient(self, authenticated_client):
        """
        GIVEN a non-existent patient ID
        WHEN POST /api/visits is called
        THEN it should return 404
        """
        response = authenticated_client.post(
            "/api/visits", json={"patient_id": 99999, "visit_type": "Wellness"}
        )
        assert response.status_code == 404
        assert "Patient not found" in response.json["error"]

    def test_create_visit_missing_required_fields(self, authenticated_client, sample_patient):
        """
        GIVEN missing required fields
        WHEN POST /api/visits is called
        THEN it should return 400
        """
        response = authenticated_client.post("/api/visits", json={"patient_id": sample_patient})
        assert response.status_code == 400

    def test_create_visit_invalid_visit_type(self, authenticated_client, sample_patient):
        """
        GIVEN an invalid visit type
        WHEN POST /api/visits is called
        THEN it should return 400
        """
        response = authenticated_client.post(
            "/api/visits",
            json={"patient_id": sample_patient, "visit_type": "InvalidType"},
        )
        assert response.status_code == 400

    def test_create_visit_success(self, authenticated_client, sample_patient):
        """
        GIVEN valid visit data
        WHEN POST /api/visits is called
        THEN it should create the visit and return 201
        """
        visit_data = {
            "patient_id": sample_patient,
            "visit_type": "Wellness",
            "status": "scheduled",
            "chief_complaint": "Routine checkup",
        }
        response = authenticated_client.post("/api/visits", json=visit_data)
        assert response.status_code == 201
        data = response.json
        assert data["patient_id"] == sample_patient
        assert data["visit_type"] == "Wellness"
        assert data["chief_complaint"] == "Routine checkup"
        assert "id" in data

    def test_create_visit_with_veterinarian(self, authenticated_client, sample_patient):
        """
        GIVEN visit data with veterinarian ID
        WHEN POST /api/visits is called
        THEN it should create the visit with the veterinarian assigned
        """
        with authenticated_client.application.app_context():
            user = User.query.filter_by(username="testvet").first()
            visit_data = {
                "patient_id": sample_patient,
                "visit_type": "Sick",
                "veterinarian_id": user.id,
            }

        response = authenticated_client.post("/api/visits", json=visit_data)
        assert response.status_code == 201
        data = response.json
        assert data["veterinarian_id"] == user.id


class TestVisitUpdate:
    """Tests for PUT /api/visits/<id>"""

    def test_update_visit_not_found(self, authenticated_client):
        """
        GIVEN a non-existent visit ID
        WHEN PUT /api/visits/<id> is called
        THEN it should return 404
        """
        response = authenticated_client.put("/api/visits/99999", json={"status": "completed"})
        assert response.status_code == 404

    def test_update_visit_status(self, authenticated_client, sample_visits):
        """
        GIVEN an existing visit
        WHEN PUT /api/visits/<id> updates the status to completed
        THEN it should update the status and set completed_at
        """
        visit_id = sample_visits[1]  # in_progress visit
        response = authenticated_client.put(f"/api/visits/{visit_id}", json={"status": "completed"})
        assert response.status_code == 200
        data = response.json
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    def test_update_visit_notes(self, authenticated_client, sample_visits):
        """
        GIVEN an existing visit
        WHEN PUT /api/visits/<id> updates visit notes
        THEN it should update the notes
        """
        visit_id = sample_visits[0]
        new_notes = "Updated visit notes with additional observations"
        response = authenticated_client.put(
            f"/api/visits/{visit_id}", json={"visit_notes": new_notes}
        )
        assert response.status_code == 200
        data = response.json
        assert data["visit_notes"] == new_notes

    def test_update_visit_partial(self, authenticated_client, sample_visits):
        """
        GIVEN an existing visit
        WHEN PUT /api/visits/<id> with partial data is called
        THEN it should update only the provided fields
        """
        visit_id = sample_visits[0]
        response = authenticated_client.put(
            f"/api/visits/{visit_id}", json={"chief_complaint": "Updated complaint"}
        )
        assert response.status_code == 200
        data = response.json
        assert data["chief_complaint"] == "Updated complaint"
        # Other fields should remain unchanged
        assert data["visit_type"] == "Wellness"


class TestVisitDelete:
    """Tests for DELETE /api/visits/<id>"""

    def test_delete_visit_not_found(self, authenticated_client):
        """
        GIVEN a non-existent visit ID
        WHEN DELETE /api/visits/<id> is called
        THEN it should return 404
        """
        response = authenticated_client.delete("/api/visits/99999")
        assert response.status_code == 404

    def test_delete_visit_success(self, authenticated_client, sample_visits):
        """
        GIVEN an existing visit
        WHEN DELETE /api/visits/<id> is called
        THEN it should delete the visit and return 200
        """
        visit_id = sample_visits[0]
        response = authenticated_client.delete(f"/api/visits/{visit_id}")
        assert response.status_code == 200
        assert "deleted" in response.json["message"].lower()

        # Verify visit is deleted
        get_response = authenticated_client.get(f"/api/visits/{visit_id}")
        assert get_response.status_code == 404
