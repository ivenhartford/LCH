"""
Unit tests for Document API endpoints

Tests all CRUD operations for the /api/documents endpoints including:
- POST /api/documents (upload document)
- GET /api/documents (list with pagination and filtering)
- GET /api/documents/<id> (single document metadata)
- GET /api/documents/<id>/download (download document file)
- PUT /api/documents/<id> (update metadata)
- DELETE /api/documents/<id> (soft delete/archive)
"""

import pytest
import os
import io
from datetime import datetime
from app.models import User, Client, Patient, Visit, Document, db


@pytest.fixture
def authenticated_client(app, client):
    """Create authenticated test client with logged-in user"""
    with app.app_context():
        user = User(username="testuser", role="user")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

    client.post("/api/login", json={"username": "testuser", "password": "password"})
    return client


@pytest.fixture
def sample_client(app, authenticated_client):
    """Create a sample client for testing"""
    with app.app_context():
        owner = Client(
            first_name="John", last_name="Doe", phone_primary="555-1234", email="john@example.com"
        )
        db.session.add(owner)
        db.session.commit()
        return owner.id


@pytest.fixture
def sample_patient(app, authenticated_client, sample_client):
    """Create a sample patient for testing"""
    with app.app_context():
        patient = Patient(
            name="Whiskers",
            breed="Persian",
            color="White",
            sex="Male",
            reproductive_status="Neutered",
            owner_id=sample_client,
            status="Active",
        )
        db.session.add(patient)
        db.session.commit()
        return patient.id


@pytest.fixture
def sample_visit(app, authenticated_client, sample_patient):
    """Create a sample visit for testing"""
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        visit = Visit(
            patient_id=sample_patient,
            veterinarian_id=user.id,
            visit_type="Wellness",
            chief_complaint="Annual checkup",
            status="completed",
        )
        db.session.add(visit)
        db.session.commit()
        return visit.id


@pytest.fixture
def sample_documents(app, authenticated_client, sample_patient, sample_client):
    """Create sample documents for testing"""
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()

        # Create upload folder if it doesn't exist
        upload_folder = authenticated_client.application.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)

        documents = [
            Document(
                filename="test1.pdf",
                original_filename="medical_record.pdf",
                file_path=os.path.join(upload_folder, "test1.pdf"),
                file_type="application/pdf",
                file_size=1024,
                category="medical_record",
                description="Patient medical history",
                patient_id=sample_patient,
                uploaded_by_id=user.id,
            ),
            Document(
                filename="test2.jpg",
                original_filename="xray.jpg",
                file_path=os.path.join(upload_folder, "test2.jpg"),
                file_type="image/jpeg",
                file_size=2048,
                category="imaging",
                patient_id=sample_patient,
                uploaded_by_id=user.id,
            ),
            Document(
                filename="test3.pdf",
                original_filename="consent_form.pdf",
                file_path=os.path.join(upload_folder, "test3.pdf"),
                file_type="application/pdf",
                file_size=512,
                category="consent_form",
                is_consent_form=True,
                consent_type="Surgery",
                client_id=sample_client,
                uploaded_by_id=user.id,
            ),
        ]

        # Create dummy files
        for doc in documents:
            with open(doc.file_path, "wb") as f:
                f.write(b"test content")
            db.session.add(doc)

        db.session.commit()
        return [doc.id for doc in documents]


class TestDocumentUpload:
    """Tests for POST /api/documents"""

    def test_upload_document_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN POST /api/documents is called
        THEN it should return 401 Unauthorized
        """
        data = {"file": (io.BytesIO(b"test content"), "test.pdf")}
        response = client.post("/api/documents", data=data, content_type="multipart/form-data")
        assert response.status_code == 401

    def test_upload_document_without_file(self, authenticated_client):
        """
        GIVEN no file in request
        WHEN POST /api/documents is called
        THEN it should return 400 Bad Request
        """
        response = authenticated_client.post("/api/documents", data={})
        assert response.status_code == 400
        assert b"No file provided" in response.data

    def test_upload_document_without_relationship(self, authenticated_client):
        """
        GIVEN a file without patient_id, visit_id, or client_id
        WHEN POST /api/documents is called
        THEN it should return 400 Bad Request
        """
        data = {
            "file": (io.BytesIO(b"test content"), "test.pdf"),
            "category": "general",
        }
        response = authenticated_client.post(
            "/api/documents", data=data, content_type="multipart/form-data"
        )
        assert response.status_code == 400
        assert b"linked to a patient, visit, or client" in response.data

    def test_upload_document_success(self, authenticated_client, sample_patient):
        """
        GIVEN valid file and metadata
        WHEN POST /api/documents is called
        THEN it should create document and return 201
        """
        data = {
            "file": (io.BytesIO(b"test content"), "test_document.pdf"),
            "category": "medical_record",
            "patient_id": sample_patient,
            "description": "Test medical record",
            "tags": "test,medical",
        }
        response = authenticated_client.post(
            "/api/documents", data=data, content_type="multipart/form-data"
        )
        assert response.status_code == 201
        data = response.json
        assert data["original_filename"] == "test_document.pdf"
        assert data["category"] == "medical_record"
        assert data["patient_id"] == sample_patient
        assert "test" in data["tags"]
        assert "medical" in data["tags"]

    def test_upload_consent_form(self, authenticated_client, sample_client):
        """
        GIVEN a consent form with metadata
        WHEN POST /api/documents is called
        THEN it should create consent form document
        """
        data = {
            "file": (io.BytesIO(b"consent content"), "consent.pdf"),
            "category": "consent_form",
            "client_id": sample_client,
            "is_consent_form": "true",
            "consent_type": "Anesthesia",
            "signed_date": "2025-01-01T00:00:00",
        }
        response = authenticated_client.post(
            "/api/documents", data=data, content_type="multipart/form-data"
        )
        assert response.status_code == 201
        data = response.json
        assert data["is_consent_form"] == True
        assert data["consent_type"] == "Anesthesia"
        assert data["client_id"] == sample_client


class TestDocumentList:
    """Tests for GET /api/documents"""

    def test_get_documents_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN GET /api/documents is called
        THEN it should return 401 Unauthorized
        """
        response = client.get("/api/documents")
        assert response.status_code == 401

    def test_get_documents_empty_list(self, authenticated_client):
        """
        GIVEN no documents in database
        WHEN GET /api/documents is called
        THEN it should return empty list
        """
        response = authenticated_client.get("/api/documents")
        assert response.status_code == 200
        data = response.json
        assert "documents" in data
        assert len(data["documents"]) == 0

    def test_get_documents_with_data(self, authenticated_client, sample_documents):
        """
        GIVEN documents in database
        WHEN GET /api/documents is called
        THEN it should return all documents
        """
        response = authenticated_client.get("/api/documents")
        assert response.status_code == 200
        data = response.json
        assert len(data["documents"]) == 3
        assert data["total"] == 3

    def test_get_documents_filter_by_category(self, authenticated_client, sample_documents):
        """
        GIVEN documents with different categories
        WHEN GET /api/documents?category=medical_record is called
        THEN it should return only medical record documents
        """
        response = authenticated_client.get("/api/documents?category=medical_record")
        assert response.status_code == 200
        data = response.json
        assert len(data["documents"]) == 1
        assert data["documents"][0]["category"] == "medical_record"

    def test_get_documents_filter_by_patient(
        self, authenticated_client, sample_documents, sample_patient
    ):
        """
        GIVEN documents linked to different patients
        WHEN GET /api/documents?patient_id=X is called
        THEN it should return only documents for that patient
        """
        response = authenticated_client.get(f"/api/documents?patient_id={sample_patient}")
        assert response.status_code == 200
        data = response.json
        assert len(data["documents"]) == 2  # Two documents linked to patient
        assert all(d["patient_id"] == sample_patient for d in data["documents"])

    def test_get_documents_filter_consent_forms(self, authenticated_client, sample_documents):
        """
        GIVEN documents including consent forms
        WHEN GET /api/documents?is_consent_form=true is called
        THEN it should return only consent forms
        """
        response = authenticated_client.get("/api/documents?is_consent_form=true")
        assert response.status_code == 200
        data = response.json
        assert len(data["documents"]) == 1
        assert data["documents"][0]["is_consent_form"] == True

    def test_get_documents_search(self, authenticated_client, sample_documents):
        """
        GIVEN documents with different filenames
        WHEN GET /api/documents?search=xray is called
        THEN it should return matching documents
        """
        response = authenticated_client.get("/api/documents?search=xray")
        assert response.status_code == 200
        data = response.json
        assert len(data["documents"]) >= 1
        assert any("xray" in d["original_filename"].lower() for d in data["documents"])


class TestDocumentDetail:
    """Tests for GET /api/documents/<id>"""

    def test_get_document_without_auth(self, client, sample_documents):
        """
        GIVEN an unauthenticated request
        WHEN GET /api/documents/<id> is called
        THEN it should return 401 Unauthorized
        """
        response = client.get(f"/api/documents/{sample_documents[0]}")
        assert response.status_code == 401

    def test_get_document_not_found(self, authenticated_client):
        """
        GIVEN a non-existent document ID
        WHEN GET /api/documents/<id> is called
        THEN it should return 404 Not Found
        """
        response = authenticated_client.get("/api/documents/9999")
        assert response.status_code == 404

    def test_get_document_success(self, authenticated_client, sample_documents):
        """
        GIVEN a valid document ID
        WHEN GET /api/documents/<id> is called
        THEN it should return document metadata
        """
        response = authenticated_client.get(f"/api/documents/{sample_documents[0]}")
        assert response.status_code == 200
        data = response.json
        assert data["id"] == sample_documents[0]
        assert "original_filename" in data
        assert "category" in data


class TestDocumentDownload:
    """Tests for GET /api/documents/<id>/download"""

    def test_download_document_without_auth(self, client, sample_documents):
        """
        GIVEN an unauthenticated request
        WHEN GET /api/documents/<id>/download is called
        THEN it should return 401 Unauthorized
        """
        response = client.get(f"/api/documents/{sample_documents[0]}/download")
        assert response.status_code == 401

    def test_download_document_not_found(self, authenticated_client):
        """
        GIVEN a non-existent document ID
        WHEN GET /api/documents/<id>/download is called
        THEN it should return 404 Not Found
        """
        response = authenticated_client.get("/api/documents/9999/download")
        assert response.status_code == 404

    def test_download_document_success(self, authenticated_client, sample_documents):
        """
        GIVEN a valid document ID
        WHEN GET /api/documents/<id>/download is called
        THEN it should return the file
        """
        response = authenticated_client.get(f"/api/documents/{sample_documents[0]}/download")
        assert response.status_code == 200
        assert b"test content" in response.data


class TestDocumentUpdate:
    """Tests for PUT /api/documents/<id>"""

    def test_update_document_without_auth(self, client, sample_documents):
        """
        GIVEN an unauthenticated request
        WHEN PUT /api/documents/<id> is called
        THEN it should return 401 Unauthorized
        """
        response = client.put(
            f"/api/documents/{sample_documents[0]}", json={"category": "lab_result"}
        )
        assert response.status_code == 401

    def test_update_document_not_found(self, authenticated_client):
        """
        GIVEN a non-existent document ID
        WHEN PUT /api/documents/<id> is called
        THEN it should return 404 Not Found
        """
        response = authenticated_client.put("/api/documents/9999", json={"category": "lab_result"})
        assert response.status_code == 404

    def test_update_document_success(self, authenticated_client, sample_documents):
        """
        GIVEN a valid document ID and update data
        WHEN PUT /api/documents/<id> is called
        THEN it should update document metadata
        """
        update_data = {
            "category": "lab_result",
            "description": "Updated description",
            "tags": ["new", "tags"],
            "notes": "Some notes",
        }
        response = authenticated_client.put(
            f"/api/documents/{sample_documents[0]}", json=update_data
        )
        assert response.status_code == 200
        data = response.json
        assert data["category"] == "lab_result"
        assert data["description"] == "Updated description"
        assert "new" in data["tags"]
        assert "tags" in data["tags"]


class TestDocumentDelete:
    """Tests for DELETE /api/documents/<id>"""

    def test_delete_document_without_auth(self, client, sample_documents):
        """
        GIVEN an unauthenticated request
        WHEN DELETE /api/documents/<id> is called
        THEN it should return 401 Unauthorized
        """
        response = client.delete(f"/api/documents/{sample_documents[0]}")
        assert response.status_code == 401

    def test_delete_document_not_found(self, authenticated_client):
        """
        GIVEN a non-existent document ID
        WHEN DELETE /api/documents/<id> is called
        THEN it should return 404 Not Found
        """
        response = authenticated_client.delete("/api/documents/9999")
        assert response.status_code == 404

    def test_delete_document_soft_delete(self, authenticated_client, sample_documents):
        """
        GIVEN a valid document ID
        WHEN DELETE /api/documents/<id> is called (without force)
        THEN it should archive the document
        """
        doc_id = sample_documents[0]
        response = authenticated_client.delete(f"/api/documents/{doc_id}")
        assert response.status_code == 200
        assert b"archived" in response.data

        # Verify document is archived
        with app.app_context():
            doc = Document.query.get(doc_id)
            assert doc is not None
            assert doc.is_archived == True

    def test_delete_document_hard_delete(self, authenticated_client, sample_documents):
        """
        GIVEN a valid document ID
        WHEN DELETE /api/documents/<id>?force=true is called
        THEN it should permanently delete the document
        """
        doc_id = sample_documents[2]

        # Get file path before deletion
        with app.app_context():
            doc = Document.query.get(doc_id)
            file_path = doc.file_path

        response = authenticated_client.delete(f"/api/documents/{doc_id}?force=true")
        assert response.status_code == 200
        assert b"permanently deleted" in response.data

        # Verify document is deleted from database
        with app.app_context():
            doc = Document.query.get(doc_id)
            assert doc is None

        # Verify file is deleted from disk
        assert not os.path.exists(file_path)


class TestDocumentValidation:
    """Tests for document upload validation"""

    def test_upload_invalid_file_type(self, authenticated_client, sample_patient):
        """
        GIVEN a file with invalid extension
        WHEN POST /api/documents is called
        THEN it should return 400 Bad Request
        """
        data = {
            "file": (io.BytesIO(b"test content"), "test.exe"),
            "category": "general",
            "patient_id": sample_patient,
        }
        response = authenticated_client.post(
            "/api/documents", data=data, content_type="multipart/form-data"
        )
        assert response.status_code == 400
        assert b"File type not allowed" in response.data

    def test_upload_empty_filename(self, authenticated_client, sample_patient):
        """
        GIVEN a file with empty filename
        WHEN POST /api/documents is called
        THEN it should return 400 Bad Request
        """
        data = {
            "file": (io.BytesIO(b"test content"), ""),
            "category": "general",
            "patient_id": sample_patient,
        }
        response = authenticated_client.post(
            "/api/documents", data=data, content_type="multipart/form-data"
        )
        assert response.status_code == 400
        assert b"No file selected" in response.data
