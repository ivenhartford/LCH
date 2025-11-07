"""
Tests for Medication API endpoints
"""

import pytest
from app import db
from app.models import User, Medication


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
def sample_medications(app, authenticated_client):
    """Create sample medications for testing"""
    with app.app_context():
        medications = [
            Medication(
                drug_name="Amoxicillin",
                brand_names="Amoxi-Tabs, Biomox",
                drug_class="Antibiotic",
                controlled_substance=False,
                available_forms="Tablet, Capsule, Liquid",
                strengths="50mg, 100mg, 200mg",
                typical_dose_cats="5-10 mg/kg BID",
                dosing_frequency="BID (twice daily)",
                route_of_administration="PO",
                indications="Bacterial infections",
                is_active=True,
            ),
            Medication(
                drug_name="Gabapentin",
                brand_names="Neurontin",
                drug_class="Analgesic",
                controlled_substance=False,
                available_forms="Capsule, Tablet, Liquid",
                strengths="100mg, 300mg",
                typical_dose_cats="5-10 mg/kg BID-TID",
                is_active=True,
            ),
            Medication(
                drug_name="Buprenorphine",
                drug_class="Opioid Analgesic",
                controlled_substance=True,
                dea_schedule="Schedule III",
                is_active=False,  # Inactive medication
            ),
        ]
        db.session.add_all(medications)
        db.session.commit()
        return [med.id for med in medications]


class TestMedicationList:
    def test_get_medications_without_auth(self, client):
        """Should return 401 without authentication"""
        response = client.get("/api/medications")
        assert response.status_code == 401

    def test_get_medications_empty_list(self, authenticated_client):
        """Should return empty list when no medications"""
        response = authenticated_client.get("/api/medications")
        assert response.status_code == 200
        data = response.json
        assert "medications" in data
        assert len(data["medications"]) == 0

    def test_get_medications_with_data(self, authenticated_client, sample_medications):
        """Should return all medications"""
        response = authenticated_client.get("/api/medications")
        assert response.status_code == 200
        data = response.json
        assert len(data["medications"]) == 3
        assert data["total"] == 3

    def test_get_medications_filter_active(self, authenticated_client, sample_medications):
        """Should filter medications by active status"""
        response = authenticated_client.get("/api/medications?is_active=true")
        assert response.status_code == 200
        data = response.json
        assert len(data["medications"]) == 2  # Only active medications

    def test_get_medications_search(self, authenticated_client, sample_medications):
        """Should search medications by name"""
        response = authenticated_client.get("/api/medications?search=amox")
        assert response.status_code == 200
        data = response.json
        assert len(data["medications"]) == 1
        assert data["medications"][0]["drug_name"] == "Amoxicillin"


class TestMedicationDetail:
    def test_get_medication_not_found(self, authenticated_client):
        """Should return 404 for non-existent medication"""
        response = authenticated_client.get("/api/medications/99999")
        assert response.status_code == 404

    def test_get_medication_success(self, authenticated_client, sample_medications):
        """Should return medication details"""
        response = authenticated_client.get(f"/api/medications/{sample_medications[0]}")
        assert response.status_code == 200
        data = response.json
        assert data["drug_name"] == "Amoxicillin"
        assert data["drug_class"] == "Antibiotic"


class TestMedicationCreate:
    def test_create_medication_success(self, authenticated_client):
        """Should create a new medication"""
        medication_data = {
            "drug_name": "Meloxicam",
            "brand_names": "Metacam",
            "drug_class": "NSAID",
            "controlled_substance": False,
            "available_forms": "Liquid, Injectable",
            "strengths": "0.5mg/ml, 1.5mg/ml",
            "typical_dose_cats": "0.1 mg/kg SID",
            "indications": "Pain and inflammation",
        }
        response = authenticated_client.post("/api/medications", json=medication_data)
        assert response.status_code == 201
        data = response.json
        assert data["drug_name"] == "Meloxicam"
        assert data["drug_class"] == "NSAID"

    def test_create_medication_duplicate(self, authenticated_client, sample_medications):
        """Should reject duplicate drug name"""
        medication_data = {"drug_name": "Amoxicillin", "drug_class": "Antibiotic"}
        response = authenticated_client.post("/api/medications", json=medication_data)
        assert response.status_code == 400
        assert "already exists" in response.json["error"]

    def test_create_medication_missing_required(self, authenticated_client):
        """Should reject medication without required fields"""
        medication_data = {"drug_class": "Antibiotic"}  # Missing drug_name
        response = authenticated_client.post("/api/medications", json=medication_data)
        assert response.status_code == 400


class TestMedicationUpdate:
    def test_update_medication_success(self, authenticated_client, sample_medications):
        """Should update medication"""
        update_data = {"stock_quantity": 100, "reorder_level": 20}
        response = authenticated_client.put(
            f"/api/medications/{sample_medications[0]}", json=update_data
        )
        assert response.status_code == 200
        data = response.json
        assert data["stock_quantity"] == 100
        assert data["reorder_level"] == 20

    def test_update_medication_not_found(self, authenticated_client):
        """Should return 404 for non-existent medication"""
        update_data = {"stock_quantity": 100}
        response = authenticated_client.put("/api/medications/99999", json=update_data)
        assert response.status_code == 404


class TestMedicationDelete:
    def test_delete_medication_success(self, authenticated_client, sample_medications):
        """Should delete medication without prescriptions"""
        response = authenticated_client.delete(f"/api/medications/{sample_medications[2]}")
        assert response.status_code == 200

    def test_delete_medication_not_found(self, authenticated_client):
        """Should return 404 for non-existent medication"""
        response = authenticated_client.delete("/api/medications/99999")
        assert response.status_code == 404
