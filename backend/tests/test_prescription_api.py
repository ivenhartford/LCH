"""
Tests for Prescription API endpoints
"""

import pytest
from datetime import date, timedelta
from app import db
from app.models import User, Client, Patient, Visit, Medication, Prescription


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
def sample_patient_and_visit(app, authenticated_client):
    """Create sample patient and visit for testing"""
    with app.app_context():
        client_obj = Client(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_primary="555-1234",
        )
        db.session.add(client_obj)
        db.session.flush()

        patient = Patient(name="Fluffy", species="Cat", breed="Persian", owner_id=client_obj.id)
        db.session.add(patient)
        db.session.flush()

        visit = Visit(
            patient_id=patient.id,
            visit_type="Wellness",
            status="completed",
            chief_complaint="Annual checkup",
        )
        db.session.add(visit)
        db.session.commit()

        return {"patient_id": patient.id, "visit_id": visit.id}


@pytest.fixture
def sample_medication(app, authenticated_client):
    """Create sample medication for testing"""
    with app.app_context():
        medication = Medication(
            drug_name="Amoxicillin",
            drug_class="Antibiotic",
            available_forms="Tablet",
            strengths="100mg",
            typical_dose_cats="10 mg/kg BID",
        )
        db.session.add(medication)
        db.session.commit()
        return medication.id


@pytest.fixture
def sample_prescriptions(app, authenticated_client, sample_patient_and_visit, sample_medication):
    """Create sample prescriptions for testing"""
    with app.app_context():
        user = User.query.filter_by(username="testvet").first()
        prescriptions = [
            Prescription(
                patient_id=sample_patient_and_visit["patient_id"],
                visit_id=sample_patient_and_visit["visit_id"],
                medication_id=sample_medication,
                dosage="100mg",
                frequency="BID",
                quantity=20,
                refills_allowed=2,
                refills_remaining=2,
                status="active",
                start_date=date.today(),
                prescribed_by_id=user.id,
            ),
            Prescription(
                patient_id=sample_patient_and_visit["patient_id"],
                medication_id=sample_medication,
                dosage="50mg",
                frequency="Once daily",
                quantity=14,
                refills_allowed=0,
                refills_remaining=0,
                status="completed",
                start_date=date.today() - timedelta(days=30),
                end_date=date.today() - timedelta(days=16),
                prescribed_by_id=user.id,
            ),
        ]
        db.session.add_all(prescriptions)
        db.session.commit()
        return [rx.id for rx in prescriptions]


class TestPrescriptionList:
    def test_get_prescriptions_without_auth(self, client):
        """Should return 401 without authentication"""
        response = client.get("/api/prescriptions")
        assert response.status_code == 401

    def test_get_prescriptions_empty_list(self, authenticated_client):
        """Should return empty list when no prescriptions"""
        response = authenticated_client.get("/api/prescriptions")
        assert response.status_code == 200
        data = response.json
        assert "prescriptions" in data
        assert len(data["prescriptions"]) == 0

    def test_get_prescriptions_with_data(self, authenticated_client, sample_prescriptions):
        """Should return all prescriptions"""
        response = authenticated_client.get("/api/prescriptions")
        assert response.status_code == 200
        data = response.json
        assert len(data["prescriptions"]) == 2

    def test_get_prescriptions_filter_by_patient(
        self, authenticated_client, sample_prescriptions, sample_patient_and_visit
    ):
        """Should filter prescriptions by patient"""
        response = authenticated_client.get(
            f"/api/prescriptions?patient_id={sample_patient_and_visit['patient_id']}"
        )
        assert response.status_code == 200
        data = response.json
        assert len(data["prescriptions"]) == 2

    def test_get_prescriptions_filter_by_status(self, authenticated_client, sample_prescriptions):
        """Should filter prescriptions by status"""
        response = authenticated_client.get("/api/prescriptions?status=active")
        assert response.status_code == 200
        data = response.json
        assert len(data["prescriptions"]) == 1
        assert data["prescriptions"][0]["status"] == "active"


class TestPrescriptionDetail:
    def test_get_prescription_not_found(self, authenticated_client):
        """Should return 404 for non-existent prescription"""
        response = authenticated_client.get("/api/prescriptions/99999")
        assert response.status_code == 404

    def test_get_prescription_success(self, authenticated_client, sample_prescriptions):
        """Should return prescription details"""
        response = authenticated_client.get(f"/api/prescriptions/{sample_prescriptions[0]}")
        assert response.status_code == 200
        data = response.json
        assert data["dosage"] == "100mg"
        assert data["frequency"] == "BID"


class TestPrescriptionCreate:
    def test_create_prescription_success(
        self, authenticated_client, sample_patient_and_visit, sample_medication
    ):
        """Should create a new prescription"""
        prescription_data = {
            "patient_id": sample_patient_and_visit["patient_id"],
            "visit_id": sample_patient_and_visit["visit_id"],
            "medication_id": sample_medication,
            "dosage": "200mg",
            "frequency": "BID",
            "quantity": 30,
            "refills_allowed": 1,
            "start_date": date.today().isoformat(),
            "instructions": "Give with food",
        }
        response = authenticated_client.post("/api/prescriptions", json=prescription_data)
        assert response.status_code == 201
        data = response.json
        assert data["dosage"] == "200mg"
        assert data["prescribed_by_name"] == "testvet"

    def test_create_prescription_invalid_patient(self, authenticated_client, sample_medication):
        """Should reject prescription for non-existent patient"""
        prescription_data = {
            "patient_id": 99999,
            "medication_id": sample_medication,
            "dosage": "100mg",
            "frequency": "BID",
            "quantity": 10,
            "start_date": date.today().isoformat(),
        }
        response = authenticated_client.post("/api/prescriptions", json=prescription_data)
        assert response.status_code == 404
        assert "Patient not found" in response.json["error"]

    def test_create_prescription_invalid_medication(
        self, authenticated_client, sample_patient_and_visit
    ):
        """Should reject prescription for non-existent medication"""
        prescription_data = {
            "patient_id": sample_patient_and_visit["patient_id"],
            "medication_id": 99999,
            "dosage": "100mg",
            "frequency": "BID",
            "quantity": 10,
            "start_date": date.today().isoformat(),
        }
        response = authenticated_client.post("/api/prescriptions", json=prescription_data)
        assert response.status_code == 404
        assert "Medication not found" in response.json["error"]

    def test_create_prescription_missing_required(
        self, authenticated_client, sample_patient_and_visit, sample_medication
    ):
        """Should reject prescription without required fields"""
        prescription_data = {
            "patient_id": sample_patient_and_visit["patient_id"],
            "medication_id": sample_medication,
            # Missing dosage, frequency, quantity, start_date
        }
        response = authenticated_client.post("/api/prescriptions", json=prescription_data)
        assert response.status_code == 400


class TestPrescriptionUpdate:
    def test_update_prescription_success(self, authenticated_client, sample_prescriptions):
        """Should update prescription"""
        update_data = {
            "status": "discontinued",
            "discontinuation_reason": "Patient switched to different medication",
        }
        response = authenticated_client.put(
            f"/api/prescriptions/{sample_prescriptions[0]}", json=update_data
        )
        assert response.status_code == 200
        data = response.json
        assert data["status"] == "discontinued"
        assert data["discontinuation_reason"] == "Patient switched to different medication"

    def test_update_prescription_refills(self, authenticated_client, sample_prescriptions):
        """Should update refills remaining"""
        update_data = {"refills_remaining": 1}
        response = authenticated_client.put(
            f"/api/prescriptions/{sample_prescriptions[0]}", json=update_data
        )
        assert response.status_code == 200
        data = response.json
        assert data["refills_remaining"] == 1

    def test_update_prescription_not_found(self, authenticated_client):
        """Should return 404 for non-existent prescription"""
        update_data = {"status": "completed"}
        response = authenticated_client.put("/api/prescriptions/99999", json=update_data)
        assert response.status_code == 404


class TestPrescriptionDelete:
    def test_delete_prescription_success(self, authenticated_client, sample_prescriptions):
        """Should delete prescription"""
        response = authenticated_client.delete(f"/api/prescriptions/{sample_prescriptions[1]}")
        assert response.status_code == 200

    def test_delete_prescription_not_found(self, authenticated_client):
        """Should return 404 for non-existent prescription"""
        response = authenticated_client.delete("/api/prescriptions/99999")
        assert response.status_code == 404
