"""
Unit tests for Medical Records API endpoints

Tests CRUD operations for:
- Vital Signs API
- SOAP Note API
- Diagnosis API
- Vaccination API
"""

import pytest
from datetime import datetime, date, timedelta
from app.models import User, Client, Patient, Visit, VitalSigns, SOAPNote, Diagnosis, Vaccination, db


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
def sample_patient_and_visit(authenticated_client):
    """Create sample patient and visit for testing medical records"""
    with authenticated_client.application.app_context():
        # Create client
        client_obj = Client(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone_primary="555-1234",
        )
        db.session.add(client_obj)
        db.session.flush()

        # Create patient
        patient = Patient(name="Fluffy", species="Cat", breed="Persian", owner_id=client_obj.id)
        db.session.add(patient)
        db.session.flush()

        # Create visit
        user = User.query.filter_by(username="testvet").first()
        visit = Visit(
            patient_id=patient.id,
            visit_type="Wellness",
            status="in_progress",
            veterinarian_id=user.id,
            chief_complaint="Annual checkup",
        )
        db.session.add(visit)
        db.session.commit()

        return {"patient_id": patient.id, "visit_id": visit.id, "user_id": user.id}


# ============================================================================
# VITAL SIGNS TESTS
# ============================================================================


class TestVitalSignsList:
    """Tests for GET /api/vital-signs"""

    def test_get_vital_signs_without_auth(self, client):
        """Should return 401 for unauthenticated request"""
        response = client.get("/api/vital-signs")
        assert response.status_code == 401

    def test_get_vital_signs_empty_list(self, authenticated_client):
        """Should return empty list when no vital signs exist"""
        response = authenticated_client.get("/api/vital-signs")
        assert response.status_code == 200
        assert len(response.json) == 0

    def test_get_vital_signs_filter_by_visit(self, authenticated_client, sample_patient_and_visit):
        """Should filter vital signs by visit_id"""
        visit_id = sample_patient_and_visit["visit_id"]

        # Create vital signs for this visit
        with authenticated_client.application.app_context():
            vs = VitalSigns(
                visit_id=visit_id,
                temperature_c=38.5,
                weight_kg=4.2,
                heart_rate=140,
                respiratory_rate=30,
            )
            db.session.add(vs)
            db.session.commit()

        response = authenticated_client.get(f"/api/vital-signs?visit_id={visit_id}")
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]["visit_id"] == visit_id


class TestVitalSignsCreate:
    """Tests for POST /api/vital-signs"""

    def test_create_vital_signs_invalid_visit(self, authenticated_client):
        """Should return 404 for non-existent visit"""
        vs_data = {
            "visit_id": 99999,
            "temperature_c": "38.5",
            "weight_kg": "4.2",
        }
        response = authenticated_client.post("/api/vital-signs", json=vs_data)
        assert response.status_code == 404

    def test_create_vital_signs_success(self, authenticated_client, sample_patient_and_visit):
        """Should create vital signs with valid data"""
        vs_data = {
            "visit_id": sample_patient_and_visit["visit_id"],
            "temperature_c": "38.5",
            "weight_kg": "4.2",
            "heart_rate": 140,
            "respiratory_rate": 30,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "body_condition_score": 5,
            "pain_score": 2,
            "mucous_membrane_color": "Pink",
            "capillary_refill_time": "<2 seconds",
            "notes": "All vitals within normal range",
        }
        response = authenticated_client.post("/api/vital-signs", json=vs_data)
        assert response.status_code == 201
        data = response.json
        assert data["temperature_c"] == "38.5"
        assert data["heart_rate"] == 140
        assert data["recorded_by_name"] == "testvet"

    def test_create_vital_signs_invalid_body_condition(self, authenticated_client, sample_patient_and_visit):
        """Should reject body_condition_score outside 1-9 range"""
        vs_data = {
            "visit_id": sample_patient_and_visit["visit_id"],
            "body_condition_score": 15,  # Invalid: > 9
        }
        response = authenticated_client.post("/api/vital-signs", json=vs_data)
        assert response.status_code == 400

    def test_create_vital_signs_invalid_pain_score(self, authenticated_client, sample_patient_and_visit):
        """Should reject pain_score outside 0-10 range"""
        vs_data = {
            "visit_id": sample_patient_and_visit["visit_id"],
            "pain_score": 15,  # Invalid: > 10
        }
        response = authenticated_client.post("/api/vital-signs", json=vs_data)
        assert response.status_code == 400


class TestVitalSignsUpdate:
    """Tests for PUT /api/vital-signs/<id>"""

    def test_update_vital_signs_success(self, authenticated_client, sample_patient_and_visit):
        """Should update vital signs with partial data"""
        # Create vital signs
        visit_id = sample_patient_and_visit["visit_id"]
        create_response = authenticated_client.post(
            "/api/vital-signs",
            json={"visit_id": visit_id, "temperature_c": "38.0"},
        )
        vs_id = create_response.json["id"]

        # Update vital signs
        update_response = authenticated_client.put(
            f"/api/vital-signs/{vs_id}",
            json={"temperature_c": "39.0", "notes": "Temperature elevated"},
        )
        assert update_response.status_code == 200
        assert update_response.json["temperature_c"] == "39.0"
        assert update_response.json["notes"] == "Temperature elevated"


# ============================================================================
# SOAP NOTE TESTS
# ============================================================================


class TestSOAPNotesList:
    """Tests for GET /api/soap-notes"""

    def test_get_soap_notes_without_auth(self, client):
        """Should return 401 for unauthenticated request"""
        response = client.get("/api/soap-notes")
        assert response.status_code == 401

    def test_get_soap_notes_filter_by_visit(self, authenticated_client, sample_patient_and_visit):
        """Should filter SOAP notes by visit_id"""
        visit_id = sample_patient_and_visit["visit_id"]
        user_id = sample_patient_and_visit["user_id"]

        # Create SOAP note
        with authenticated_client.application.app_context():
            soap = SOAPNote(
                visit_id=visit_id,
                subjective="Owner reports cat is lethargic",
                objective="Temp 39.0C, heart rate 150 bpm",
                assessment="Possible URI",
                plan="Antibiotics, recheck in 1 week",
                created_by_id=user_id,
            )
            db.session.add(soap)
            db.session.commit()

        response = authenticated_client.get(f"/api/soap-notes?visit_id={visit_id}")
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]["subjective"] == "Owner reports cat is lethargic"


class TestSOAPNotesCreate:
    """Tests for POST /api/soap-notes"""

    def test_create_soap_note_invalid_visit(self, authenticated_client):
        """Should return 404 for non-existent visit"""
        soap_data = {
            "visit_id": 99999,
            "subjective": "Test",
        }
        response = authenticated_client.post("/api/soap-notes", json=soap_data)
        assert response.status_code == 404

    def test_create_soap_note_success(self, authenticated_client, sample_patient_and_visit):
        """Should create SOAP note with valid data"""
        soap_data = {
            "visit_id": sample_patient_and_visit["visit_id"],
            "subjective": "Owner reports decreased appetite for 2 days",
            "objective": "BCS 4/9, temp 38.8C, mild dehydration",
            "assessment": "Gastroenteritis, mild dehydration",
            "plan": "Maropitant 1mg/kg SQ, fluids SQ, bland diet",
        }
        response = authenticated_client.post("/api/soap-notes", json=soap_data)
        assert response.status_code == 201
        data = response.json
        assert data["subjective"] == soap_data["subjective"]
        assert data["created_by_name"] == "testvet"
        assert "created_at" in data


class TestSOAPNotesUpdate:
    """Tests for PUT /api/soap-notes/<id>"""

    def test_update_soap_note_success(self, authenticated_client, sample_patient_and_visit):
        """Should update SOAP note"""
        # Create SOAP note
        create_response = authenticated_client.post(
            "/api/soap-notes",
            json={
                "visit_id": sample_patient_and_visit["visit_id"],
                "subjective": "Initial subjective",
            },
        )
        soap_id = create_response.json["id"]

        # Update SOAP note
        update_response = authenticated_client.put(
            f"/api/soap-notes/{soap_id}",
            json={
                "subjective": "Updated subjective findings",
                "assessment": "New assessment added",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json["subjective"] == "Updated subjective findings"
        assert update_response.json["assessment"] == "New assessment added"


# ============================================================================
# DIAGNOSIS TESTS
# ============================================================================


class TestDiagnosisList:
    """Tests for GET /api/diagnoses"""

    def test_get_diagnoses_without_auth(self, client):
        """Should return 401 for unauthenticated request"""
        response = client.get("/api/diagnoses")
        assert response.status_code == 401

    def test_get_diagnoses_filter_by_status(self, authenticated_client, sample_patient_and_visit):
        """Should filter diagnoses by status"""
        visit_id = sample_patient_and_visit["visit_id"]
        user_id = sample_patient_and_visit["user_id"]

        # Create diagnoses with different statuses
        with authenticated_client.application.app_context():
            diag1 = Diagnosis(
                visit_id=visit_id,
                diagnosis_name="Upper Respiratory Infection",
                icd_code="J06.9",
                status="active",
                created_by_id=user_id,
            )
            diag2 = Diagnosis(
                visit_id=visit_id,
                diagnosis_name="Ear Infection",
                status="resolved",
                created_by_id=user_id,
            )
            db.session.add_all([diag1, diag2])
            db.session.commit()

        response = authenticated_client.get("/api/diagnoses?status=active")
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]["status"] == "active"


class TestDiagnosisCreate:
    """Tests for POST /api/diagnoses"""

    def test_create_diagnosis_missing_required(self, authenticated_client):
        """Should return 400 when diagnosis_name is missing"""
        response = authenticated_client.post("/api/diagnoses", json={"visit_id": 1})
        assert response.status_code == 400

    def test_create_diagnosis_invalid_type(self, authenticated_client, sample_patient_and_visit):
        """Should reject invalid diagnosis_type"""
        diag_data = {
            "visit_id": sample_patient_and_visit["visit_id"],
            "diagnosis_name": "Test Diagnosis",
            "diagnosis_type": "invalid_type",
        }
        response = authenticated_client.post("/api/diagnoses", json=diag_data)
        assert response.status_code == 400

    def test_create_diagnosis_success(self, authenticated_client, sample_patient_and_visit):
        """Should create diagnosis with valid data"""
        diag_data = {
            "visit_id": sample_patient_and_visit["visit_id"],
            "diagnosis_name": "Feline Upper Respiratory Infection",
            "icd_code": "J06.9",
            "diagnosis_type": "primary",
            "severity": "moderate",
            "status": "active",
            "notes": "Classic URI symptoms, began 3 days ago",
        }
        response = authenticated_client.post("/api/diagnoses", json=diag_data)
        assert response.status_code == 201
        data = response.json
        assert data["diagnosis_name"] == diag_data["diagnosis_name"]
        assert data["icd_code"] == "J06.9"
        assert data["severity"] == "moderate"
        assert data["created_by_name"] == "testvet"

    def test_create_diagnosis_with_dates(self, authenticated_client, sample_patient_and_visit):
        """Should create diagnosis with onset and resolution dates"""
        diag_data = {
            "visit_id": sample_patient_and_visit["visit_id"],
            "diagnosis_name": "Healed Wound",
            "onset_date": "2025-10-01",
            "resolution_date": "2025-10-20",
            "status": "resolved",
        }
        response = authenticated_client.post("/api/diagnoses", json=diag_data)
        assert response.status_code == 201
        assert response.json["onset_date"] == "2025-10-01"
        assert response.json["resolution_date"] == "2025-10-20"


class TestDiagnosisUpdate:
    """Tests for PUT /api/diagnoses/<id>"""

    def test_update_diagnosis_status(self, authenticated_client, sample_patient_and_visit):
        """Should update diagnosis status"""
        # Create diagnosis
        create_response = authenticated_client.post(
            "/api/diagnoses",
            json={
                "visit_id": sample_patient_and_visit["visit_id"],
                "diagnosis_name": "Test Diagnosis",
                "status": "active",
            },
        )
        diag_id = create_response.json["id"]

        # Update status to resolved
        update_response = authenticated_client.put(
            f"/api/diagnoses/{diag_id}",
            json={"status": "resolved", "resolution_date": "2025-10-27"},
        )
        assert update_response.status_code == 200
        assert update_response.json["status"] == "resolved"
        assert update_response.json["resolution_date"] == "2025-10-27"


# ============================================================================
# VACCINATION TESTS
# ============================================================================


class TestVaccinationList:
    """Tests for GET /api/vaccinations"""

    def test_get_vaccinations_without_auth(self, client):
        """Should return 401 for unauthenticated request"""
        response = client.get("/api/vaccinations")
        assert response.status_code == 401

    def test_get_vaccinations_filter_by_patient(self, authenticated_client, sample_patient_and_visit):
        """Should filter vaccinations by patient_id"""
        patient_id = sample_patient_and_visit["patient_id"]
        user_id = sample_patient_and_visit["user_id"]

        # Create vaccination
        with authenticated_client.application.app_context():
            vacc = Vaccination(
                patient_id=patient_id,
                vaccine_name="FVRCP",
                vaccine_type="Core",
                administration_date=date.today(),
                next_due_date=date.today() + timedelta(days=365),
                administered_by_id=user_id,
            )
            db.session.add(vacc)
            db.session.commit()

        response = authenticated_client.get(f"/api/vaccinations?patient_id={patient_id}")
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]["vaccine_name"] == "FVRCP"


class TestVaccinationCreate:
    """Tests for POST /api/vaccinations"""

    def test_create_vaccination_missing_required(self, authenticated_client, sample_patient_and_visit):
        """Should return 400 when required fields are missing"""
        response = authenticated_client.post(
            "/api/vaccinations",
            json={"patient_id": sample_patient_and_visit["patient_id"]},
        )
        assert response.status_code == 400

    def test_create_vaccination_invalid_route(self, authenticated_client, sample_patient_and_visit):
        """Should reject invalid administration route"""
        vacc_data = {
            "patient_id": sample_patient_and_visit["patient_id"],
            "vaccine_name": "Rabies",
            "administration_date": "2025-10-27",
            "route": "InvalidRoute",
        }
        response = authenticated_client.post("/api/vaccinations", json=vacc_data)
        assert response.status_code == 400

    def test_create_vaccination_success(self, authenticated_client, sample_patient_and_visit):
        """Should create vaccination with valid data"""
        vacc_data = {
            "patient_id": sample_patient_and_visit["patient_id"],
            "vaccine_name": "FVRCP",
            "vaccine_type": "Core",
            "manufacturer": "Zoetis",
            "lot_number": "LOT12345",
            "serial_number": "SN789",
            "administration_date": "2025-10-27",
            "expiration_date": "2026-10-27",
            "next_due_date": "2026-10-27",
            "dosage": "1ml",
            "route": "SC",
            "administration_site": "Right shoulder",
            "status": "current",
            "notes": "No adverse reactions noted",
        }
        response = authenticated_client.post("/api/vaccinations", json=vacc_data)
        assert response.status_code == 201
        data = response.json
        assert data["vaccine_name"] == "FVRCP"
        assert data["vaccine_type"] == "Core"
        assert data["lot_number"] == "LOT12345"
        assert data["route"] == "SC"
        assert data["administered_by_name"] == "testvet"

    def test_create_vaccination_with_visit(self, authenticated_client, sample_patient_and_visit):
        """Should create vaccination linked to a visit"""
        vacc_data = {
            "patient_id": sample_patient_and_visit["patient_id"],
            "visit_id": sample_patient_and_visit["visit_id"],
            "vaccine_name": "Rabies",
            "administration_date": "2025-10-27",
        }
        response = authenticated_client.post("/api/vaccinations", json=vacc_data)
        assert response.status_code == 201
        assert response.json["visit_id"] == sample_patient_and_visit["visit_id"]


class TestVaccinationUpdate:
    """Tests for PUT /api/vaccinations/<id>"""

    def test_update_vaccination_status(self, authenticated_client, sample_patient_and_visit):
        """Should update vaccination status"""
        # Create vaccination
        create_response = authenticated_client.post(
            "/api/vaccinations",
            json={
                "patient_id": sample_patient_and_visit["patient_id"],
                "vaccine_name": "FVRCP",
                "administration_date": "2024-10-27",
                "next_due_date": "2025-10-27",
                "status": "current",
            },
        )
        vacc_id = create_response.json["id"]

        # Update status to overdue
        update_response = authenticated_client.put(
            f"/api/vaccinations/{vacc_id}",
            json={"status": "overdue"},
        )
        assert update_response.status_code == 200
        assert update_response.json["status"] == "overdue"

    def test_update_vaccination_adverse_reaction(self, authenticated_client, sample_patient_and_visit):
        """Should record adverse reactions"""
        # Create vaccination
        create_response = authenticated_client.post(
            "/api/vaccinations",
            json={
                "patient_id": sample_patient_and_visit["patient_id"],
                "vaccine_name": "Rabies",
                "administration_date": "2025-10-27",
            },
        )
        vacc_id = create_response.json["id"]

        # Add adverse reaction note
        update_response = authenticated_client.put(
            f"/api/vaccinations/{vacc_id}",
            json={"adverse_reactions": "Mild swelling at injection site, resolved in 24h"},
        )
        assert update_response.status_code == 200
        assert "swelling" in update_response.json["adverse_reactions"]


class TestVaccinationDelete:
    """Tests for DELETE /api/vaccinations/<id>"""

    def test_delete_vaccination_success(self, authenticated_client, sample_patient_and_visit):
        """Should delete vaccination"""
        # Create vaccination
        create_response = authenticated_client.post(
            "/api/vaccinations",
            json={
                "patient_id": sample_patient_and_visit["patient_id"],
                "vaccine_name": "FeLV",
                "administration_date": "2025-10-27",
            },
        )
        vacc_id = create_response.json["id"]

        # Delete vaccination
        delete_response = authenticated_client.delete(f"/api/vaccinations/{vacc_id}")
        assert delete_response.status_code == 200

        # Verify deletion
        get_response = authenticated_client.get(f"/api/vaccinations/{vacc_id}")
        assert get_response.status_code == 404
