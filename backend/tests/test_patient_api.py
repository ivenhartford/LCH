"""
Unit tests for Patient API endpoints

Tests all CRUD operations for the /api/patients endpoints including:
- GET /api/patients (list with pagination, search, and filtering)
- GET /api/patients/<id> (single patient)
- POST /api/patients (create)
- PUT /api/patients/<id> (update)
- DELETE /api/patients/<id> (soft and hard delete)
"""

import pytest
from datetime import date
from app.models import User, Client, Patient, db


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
def sample_owner(authenticated_client):
    """Create a sample client (cat owner) for testing"""
    with authenticated_client.application.app_context():
        owner = Client(first_name="John", last_name="Doe", phone_primary="555-1234", email="john@example.com")
        db.session.add(owner)
        db.session.commit()
        return owner.id


@pytest.fixture
def sample_patients(authenticated_client, sample_owner):
    """Create sample patients for testing"""
    with authenticated_client.application.app_context():
        patients = [
            Patient(
                name="Whiskers",
                breed="Persian",
                color="White",
                sex="Male",
                reproductive_status="Neutered",
                owner_id=sample_owner,
                microchip_number="123456789",
                status="Active",
            ),
            Patient(
                name="Mittens",
                breed="Siamese",
                color="Cream",
                sex="Female",
                reproductive_status="Spayed",
                owner_id=sample_owner,
                status="Active",
            ),
            Patient(
                name="Shadow",
                breed="Domestic Shorthair",
                color="Black",
                sex="Male",
                owner_id=sample_owner,
                status="Deceased",
                deceased_date=date(2024, 1, 15),
            ),
        ]
        for p in patients:
            db.session.add(p)
        db.session.commit()

        return [p.id for p in patients]

    return []


class TestPatientList:
    """Tests for GET /api/patients"""

    def test_get_patients_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN GET /api/patients is called
        THEN it should return 401 Unauthorized
        """
        response = client.get("/api/patients")
        assert response.status_code == 401

    def test_get_patients_empty_list(self, authenticated_client):
        """
        GIVEN no patients in database
        WHEN GET /api/patients is called
        THEN it should return empty list with pagination
        """
        response = authenticated_client.get("/api/patients")
        assert response.status_code == 200
        data = response.json
        assert "patients" in data
        assert "pagination" in data
        assert len(data["patients"]) == 0
        assert data["pagination"]["total"] == 0

    def test_get_patients_with_data(self, authenticated_client, sample_patients):
        """
        GIVEN patients in database
        WHEN GET /api/patients is called
        THEN it should return active patients by default
        """
        response = authenticated_client.get("/api/patients")
        assert response.status_code == 200
        data = response.json
        assert len(data["patients"]) == 2  # Only active patients
        assert data["pagination"]["total"] == 2

    def test_get_patients_all_statuses(self, authenticated_client, sample_patients):
        """
        GIVEN patients with different statuses
        WHEN GET /api/patients?status= is called (no filter)
        THEN it should return active patients only by default
        """
        response = authenticated_client.get("/api/patients")
        assert response.status_code == 200
        data = response.json
        assert all(p["status"] == "Active" for p in data["patients"])

    def test_get_patients_filter_by_status(self, authenticated_client, sample_patients):
        """
        GIVEN patients with different statuses
        WHEN GET /api/patients?status=Deceased is called
        THEN it should return only deceased patients
        """
        response = authenticated_client.get("/api/patients?status=Deceased")
        assert response.status_code == 200
        data = response.json
        assert len(data["patients"]) == 1
        assert data["patients"][0]["name"] == "Shadow"
        assert data["patients"][0]["status"] == "Deceased"

    def test_get_patients_filter_by_owner(self, authenticated_client, sample_owner, sample_patients):
        """
        GIVEN patients linked to specific owner
        WHEN GET /api/patients?owner_id=X is called
        THEN it should return only that owner's patients
        """
        response = authenticated_client.get(f"/api/patients?owner_id={sample_owner}")
        assert response.status_code == 200
        data = response.json
        assert data["pagination"]["total"] == 2  # Active patients for this owner
        assert all(p["owner_id"] == sample_owner for p in data["patients"])

    def test_get_patients_with_search_name(self, authenticated_client, sample_patients):
        """
        GIVEN patients in database
        WHEN searching by name
        THEN it should find matching patients
        """
        response = authenticated_client.get("/api/patients?search=Whiskers")
        assert response.status_code == 200
        data = response.json
        assert len(data["patients"]) == 1
        assert data["patients"][0]["name"] == "Whiskers"

    def test_get_patients_search_by_breed(self, authenticated_client, sample_patients):
        """
        GIVEN patients in database
        WHEN searching by breed
        THEN it should find matching patients
        """
        response = authenticated_client.get("/api/patients?search=Siamese")
        assert response.status_code == 200
        data = response.json
        assert len(data["patients"]) == 1
        assert data["patients"][0]["breed"] == "Siamese"

    def test_get_patients_search_by_microchip(self, authenticated_client, sample_patients):
        """
        GIVEN patients with microchips
        WHEN searching by microchip number
        THEN it should find matching patient
        """
        response = authenticated_client.get("/api/patients?search=123456789")
        assert response.status_code == 200
        data = response.json
        assert len(data["patients"]) == 1
        assert data["patients"][0]["microchip_number"] == "123456789"

    def test_get_patients_pagination(self, authenticated_client, sample_patients):
        """
        GIVEN patients in database
        WHEN requesting with per_page parameter
        THEN it should paginate correctly
        """
        response = authenticated_client.get("/api/patients?per_page=1")
        assert response.status_code == 200
        data = response.json
        assert len(data["patients"]) == 1
        assert data["pagination"]["per_page"] == 1
        assert data["pagination"]["pages"] == 2


class TestPatientDetail:
    """Tests for GET /api/patients/<id>"""

    def test_get_patient_by_id(self, authenticated_client, sample_patients):
        """
        GIVEN a patient exists
        WHEN GET /api/patients/<id> is called
        THEN it should return the patient data
        """
        patient_id = sample_patients[0]
        response = authenticated_client.get(f"/api/patients/{patient_id}")
        assert response.status_code == 200
        data = response.json
        assert data["id"] == patient_id
        assert data["name"] == "Whiskers"
        assert data["breed"] == "Persian"
        assert data["species"] == "Cat"

    def test_get_patient_not_found(self, authenticated_client):
        """
        GIVEN a patient does not exist
        WHEN GET /api/patients/9999 is called
        THEN it should return 404
        """
        response = authenticated_client.get("/api/patients/9999")
        assert response.status_code == 404

    def test_get_deceased_patient(self, authenticated_client, sample_patients):
        """
        GIVEN a deceased patient exists
        WHEN GET /api/patients/<id> is called
        THEN it should still return the patient (with warning logged)
        """
        patient_id = sample_patients[2]  # Deceased patient
        response = authenticated_client.get(f"/api/patients/{patient_id}")
        assert response.status_code == 200
        data = response.json
        assert data["status"] == "Deceased"
        assert data["deceased_date"] is not None


class TestPatientCreate:
    """Tests for POST /api/patients"""

    def test_create_patient_success(self, authenticated_client, sample_owner):
        """
        GIVEN valid patient data
        WHEN POST /api/patients is called
        THEN it should create a new patient
        """
        patient_data = {
            "name": "Fluffy",
            "breed": "Maine Coon",
            "color": "Orange Tabby",
            "sex": "Female",
            "reproductive_status": "Spayed",
            "owner_id": sample_owner,
            "weight_kg": "4.5",
        }
        response = authenticated_client.post("/api/patients", json=patient_data)
        assert response.status_code == 201
        data = response.json
        assert data["name"] == "Fluffy"
        assert data["breed"] == "Maine Coon"
        assert data["species"] == "Cat"  # Default value
        assert "id" in data
        assert "created_at" in data

    def test_create_patient_minimal_data(self, authenticated_client, sample_owner):
        """
        GIVEN minimal required patient data
        WHEN POST /api/patients is called
        THEN it should create patient with defaults
        """
        patient_data = {"name": "Luna", "owner_id": sample_owner}
        response = authenticated_client.post("/api/patients", json=patient_data)
        assert response.status_code == 201
        data = response.json
        assert data["name"] == "Luna"
        assert data["species"] == "Cat"
        assert data["status"] == "Active"

    def test_create_patient_missing_required_fields(self, authenticated_client):
        """
        GIVEN patient data missing required fields
        WHEN POST /api/patients is called
        THEN it should return 400 validation error
        """
        patient_data = {
            "breed": "Persian"
            # Missing name and owner_id
        }
        response = authenticated_client.post("/api/patients", json=patient_data)
        assert response.status_code == 400
        data = response.json
        assert "error" in data
        assert "messages" in data

    def test_create_patient_invalid_owner(self, authenticated_client):
        """
        GIVEN patient data with non-existent owner_id
        WHEN POST /api/patients is called
        THEN it should return 404 error
        """
        patient_data = {"name": "Ghost", "owner_id": 9999}  # Non-existent owner
        response = authenticated_client.post("/api/patients", json=patient_data)
        assert response.status_code == 404
        data = response.json
        assert "Owner" in data["error"]

    def test_create_patient_duplicate_microchip(self, authenticated_client, sample_owner, sample_patients):
        """
        GIVEN patient data with duplicate microchip number
        WHEN POST /api/patients is called
        THEN it should return 409 conflict
        """
        patient_data = {
            "name": "Duplicate",
            "owner_id": sample_owner,
            "microchip_number": "123456789",  # Duplicate
        }
        response = authenticated_client.post("/api/patients", json=patient_data)
        assert response.status_code == 409
        data = response.json
        assert "Microchip" in data["error"]

    def test_create_patient_invalid_sex(self, authenticated_client, sample_owner):
        """
        GIVEN patient data with invalid sex value
        WHEN POST /api/patients is called
        THEN it should return 400 validation error
        """
        patient_data = {
            "name": "Invalid",
            "owner_id": sample_owner,
            "sex": "Unknown",  # Invalid - must be Male or Female
        }
        response = authenticated_client.post("/api/patients", json=patient_data)
        assert response.status_code == 400


class TestPatientUpdate:
    """Tests for PUT /api/patients/<id>"""

    def test_update_patient_success(self, authenticated_client, sample_patients):
        """
        GIVEN a patient exists
        WHEN PUT /api/patients/<id> is called with valid data
        THEN it should update the patient
        """
        patient_id = sample_patients[0]
        update_data = {"weight_kg": "5.2", "color": "Light Gray"}
        response = authenticated_client.put(f"/api/patients/{patient_id}", json=update_data)
        assert response.status_code == 200
        data = response.json
        assert float(data["weight_kg"]) == 5.2
        assert data["color"] == "Light Gray"
        assert data["name"] == "Whiskers"  # Unchanged

    def test_update_patient_change_status(self, authenticated_client, sample_patients):
        """
        GIVEN an active patient
        WHEN updating status to Deceased
        THEN it should update successfully
        """
        patient_id = sample_patients[0]
        update_data = {"status": "Deceased", "deceased_date": "2025-01-15"}
        response = authenticated_client.put(f"/api/patients/{patient_id}", json=update_data)
        assert response.status_code == 200
        data = response.json
        assert data["status"] == "Deceased"
        assert data["deceased_date"] is not None

    def test_update_patient_duplicate_microchip(self, authenticated_client, sample_patients):
        """
        GIVEN a patient exists
        WHEN updating microchip to another patient's microchip
        THEN it should return 409 conflict
        """
        patient_id = sample_patients[1]  # Mittens (no microchip)
        update_data = {"microchip_number": "123456789"}  # Whiskers' microchip
        response = authenticated_client.put(f"/api/patients/{patient_id}", json=update_data)
        assert response.status_code == 409

    def test_update_patient_not_found(self, authenticated_client):
        """
        GIVEN a patient does not exist
        WHEN PUT /api/patients/9999 is called
        THEN it should return 404
        """
        update_data = {"weight_kg": "4.0"}
        response = authenticated_client.put("/api/patients/9999", json=update_data)
        assert response.status_code == 404

    def test_update_patient_invalid_status(self, authenticated_client, sample_patients):
        """
        GIVEN invalid update data
        WHEN PUT /api/patients/<id> is called
        THEN it should return 400 validation error
        """
        patient_id = sample_patients[0]
        update_data = {"status": "InvalidStatus"}
        response = authenticated_client.put(f"/api/patients/{patient_id}", json=update_data)
        assert response.status_code == 400


class TestPatientDelete:
    """Tests for DELETE /api/patients/<id>"""

    def test_soft_delete_patient(self, authenticated_client, sample_patients):
        """
        GIVEN a patient exists
        WHEN DELETE /api/patients/<id> is called
        THEN it should soft delete (set to Inactive)
        """
        patient_id = sample_patients[0]
        response = authenticated_client.delete(f"/api/patients/{patient_id}")
        assert response.status_code == 200
        data = response.json
        assert "deactivated" in data["message"]

        # Verify patient is soft deleted
        get_response = authenticated_client.get(f"/api/patients/{patient_id}")
        assert get_response.status_code == 200
        patient_data = get_response.json
        assert patient_data["status"] == "Inactive"

    def test_hard_delete_patient_as_user(self, authenticated_client, sample_patients):
        """
        GIVEN a regular user
        WHEN DELETE /api/patients/<id>?hard=true is called
        THEN it should return 403 forbidden
        """
        patient_id = sample_patients[0]
        response = authenticated_client.delete(f"/api/patients/{patient_id}?hard=true")
        assert response.status_code == 403
        data = response.json
        assert "Admin access required" in data["error"]

    def test_hard_delete_patient_as_admin(self, admin_client):
        """
        GIVEN an admin user
        WHEN DELETE /api/patients/<id>?hard=true is called
        THEN it should permanently delete the patient
        """
        # Create owner and patient
        with admin_client.application.app_context():
            owner = Client(first_name="Test", last_name="Owner", phone_primary="555-0000")
            db.session.add(owner)
            db.session.commit()

            patient = Patient(name="ToDelete", owner_id=owner.id)
            db.session.add(patient)
            db.session.commit()
            patient_id = patient.id

        response = admin_client.delete(f"/api/patients/{patient_id}?hard=true")
        assert response.status_code == 200
        data = response.json
        assert "permanently deleted" in data["message"]

        # Verify patient is gone
        get_response = admin_client.get(f"/api/patients/{patient_id}")
        assert get_response.status_code == 404

    def test_delete_patient_not_found(self, authenticated_client):
        """
        GIVEN a patient does not exist
        WHEN DELETE /api/patients/9999 is called
        THEN it should return 404
        """
        response = authenticated_client.delete("/api/patients/9999")
        assert response.status_code == 404


class TestPatientIntegration:
    """Integration tests for full patient workflows"""

    def test_full_patient_lifecycle(self, authenticated_client, sample_owner):
        """
        Test complete CRUD lifecycle:
        Create -> Read -> Update -> Soft Delete -> Read (inactive)
        """
        # Create
        create_data = {
            "name": "Snowball",
            "breed": "Persian",
            "color": "White",
            "sex": "Female",
            "reproductive_status": "Spayed",
            "owner_id": sample_owner,
            "microchip_number": "ABC123XYZ",
            "weight_kg": "3.8",
        }
        create_response = authenticated_client.post("/api/patients", json=create_data)
        assert create_response.status_code == 201
        patient_id = create_response.json["id"]

        # Read
        get_response = authenticated_client.get(f"/api/patients/{patient_id}")
        assert get_response.status_code == 200
        assert get_response.json["name"] == "Snowball"
        assert get_response.json["microchip_number"] == "ABC123XYZ"

        # Update
        update_data = {"weight_kg": "4.2", "color": "Cream"}
        update_response = authenticated_client.put(f"/api/patients/{patient_id}", json=update_data)
        assert update_response.status_code == 200
        assert float(update_response.json["weight_kg"]) == 4.2
        assert update_response.json["color"] == "Cream"

        # Soft Delete
        delete_response = authenticated_client.delete(f"/api/patients/{patient_id}")
        assert delete_response.status_code == 200

        # Read (inactive)
        final_get = authenticated_client.get(f"/api/patients/{patient_id}")
        assert final_get.status_code == 200
        assert final_get.json["status"] == "Inactive"
