"""
Unit tests for Client API endpoints

Tests all CRUD operations for the /api/clients endpoints including:
- GET /api/clients (list with pagination and search)
- GET /api/clients/<id> (single client)
- POST /api/clients (create)
- PUT /api/clients/<id> (update)
- DELETE /api/clients/<id> (soft and hard delete)
"""

import pytest
from app.models import User, Client, db


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
def sample_clients(authenticated_client):
    """Create sample clients for testing"""
    with authenticated_client.application.app_context():
        clients = [
            Client(
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                phone_primary="555-1234",
                city="New York",
            ),
            Client(
                first_name="Jane",
                last_name="Smith",
                email="jane.smith@example.com",
                phone_primary="555-5678",
                city="Los Angeles",
            ),
            Client(
                first_name="Bob",
                last_name="Johnson",
                email="bob.j@example.com",
                phone_primary="555-9999",
                is_active=False,  # Inactive client
            ),
        ]
        for c in clients:
            db.session.add(c)
        db.session.commit()

        return [c.id for c in clients]

    return []


class TestClientList:
    """Tests for GET /api/clients"""

    def test_get_clients_without_auth(self, client):
        """
        GIVEN an unauthenticated request
        WHEN GET /api/clients is called
        THEN it should return 401 Unauthorized
        """
        response = client.get("/api/clients")
        assert response.status_code == 401

    def test_get_clients_empty_list(self, authenticated_client):
        """
        GIVEN no clients in database
        WHEN GET /api/clients is called
        THEN it should return empty list with pagination
        """
        response = authenticated_client.get("/api/clients")
        assert response.status_code == 200
        data = response.json
        assert "clients" in data
        assert "pagination" in data
        assert len(data["clients"]) == 0
        assert data["pagination"]["total"] == 0

    def test_get_clients_with_data(self, authenticated_client, sample_clients):
        """
        GIVEN clients in database
        WHEN GET /api/clients is called
        THEN it should return active clients by default
        """
        response = authenticated_client.get("/api/clients")
        assert response.status_code == 200
        data = response.json
        assert len(data["clients"]) == 2  # Only active clients
        assert data["pagination"]["total"] == 2

    def test_get_clients_including_inactive(self, authenticated_client, sample_clients):
        """
        GIVEN clients including inactive ones
        WHEN GET /api/clients?active_only=false is called
        THEN it should return all clients
        """
        response = authenticated_client.get("/api/clients?active_only=false")
        assert response.status_code == 200
        data = response.json
        assert len(data["clients"]) == 3  # All clients
        assert data["pagination"]["total"] == 3

    def test_get_clients_with_search(self, authenticated_client, sample_clients):
        """
        GIVEN clients in database
        WHEN GET /api/clients?search=jane is called
        THEN it should return matching clients
        """
        response = authenticated_client.get("/api/clients?search=jane")
        assert response.status_code == 200
        data = response.json
        assert len(data["clients"]) == 1
        assert data["clients"][0]["first_name"] == "Jane"

    def test_get_clients_search_by_email(self, authenticated_client, sample_clients):
        """
        GIVEN clients in database
        WHEN searching by email
        THEN it should find matching client
        """
        response = authenticated_client.get("/api/clients?search=john.doe")
        assert response.status_code == 200
        data = response.json
        assert len(data["clients"]) == 1
        assert data["clients"][0]["email"] == "john.doe@example.com"

    def test_get_clients_pagination(self, authenticated_client, sample_clients):
        """
        GIVEN clients in database
        WHEN requesting with per_page parameter
        THEN it should paginate correctly
        """
        response = authenticated_client.get("/api/clients?per_page=1")
        assert response.status_code == 200
        data = response.json
        assert len(data["clients"]) == 1
        assert data["pagination"]["per_page"] == 1
        assert data["pagination"]["pages"] == 2


class TestClientDetail:
    """Tests for GET /api/clients/<id>"""

    def test_get_client_by_id(self, authenticated_client, sample_clients):
        """
        GIVEN a client exists
        WHEN GET /api/clients/<id> is called
        THEN it should return the client data
        """
        client_id = sample_clients[0]
        response = authenticated_client.get(f"/api/clients/{client_id}")
        assert response.status_code == 200
        data = response.json
        assert data["id"] == client_id
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"

    def test_get_client_not_found(self, authenticated_client):
        """
        GIVEN a client does not exist
        WHEN GET /api/clients/9999 is called
        THEN it should return 404
        """
        response = authenticated_client.get("/api/clients/9999")
        assert response.status_code == 404

    def test_get_inactive_client(self, authenticated_client, sample_clients):
        """
        GIVEN an inactive client exists
        WHEN GET /api/clients/<id> is called
        THEN it should still return the client (with warning logged)
        """
        client_id = sample_clients[2]  # Inactive client
        response = authenticated_client.get(f"/api/clients/{client_id}")
        assert response.status_code == 200
        data = response.json
        assert data["is_active"] is False


class TestClientCreate:
    """Tests for POST /api/clients"""

    def test_create_client_success(self, authenticated_client):
        """
        GIVEN valid client data
        WHEN POST /api/clients is called
        THEN it should create a new client
        """
        client_data = {
            "first_name": "Alice",
            "last_name": "Williams",
            "email": "alice@example.com",
            "phone_primary": "555-1111",
            "city": "Chicago",
        }
        response = authenticated_client.post("/api/clients", json=client_data)
        assert response.status_code == 201
        data = response.json
        assert data["first_name"] == "Alice"
        assert data["last_name"] == "Williams"
        assert "id" in data
        assert "created_at" in data

    def test_create_client_minimal_data(self, authenticated_client):
        """
        GIVEN minimal required client data
        WHEN POST /api/clients is called
        THEN it should create client with defaults
        """
        client_data = {"first_name": "Bob", "last_name": "Brown", "phone_primary": "555-2222"}
        response = authenticated_client.post("/api/clients", json=client_data)
        assert response.status_code == 201
        data = response.json
        assert data["first_name"] == "Bob"
        assert data["email"] is None
        assert data["is_active"] is True
        assert data["preferred_contact"] == "email"

    def test_create_client_missing_required_fields(self, authenticated_client):
        """
        GIVEN client data missing required fields
        WHEN POST /api/clients is called
        THEN it should return 400 validation error
        """
        client_data = {
            "first_name": "Charlie"
            # Missing last_name and phone_primary
        }
        response = authenticated_client.post("/api/clients", json=client_data)
        assert response.status_code == 400
        data = response.json
        assert "error" in data
        assert "messages" in data

    def test_create_client_invalid_email(self, authenticated_client):
        """
        GIVEN client data with invalid email
        WHEN POST /api/clients is called
        THEN it should return 400 validation error
        """
        client_data = {
            "first_name": "David",
            "last_name": "Davis",
            "phone_primary": "555-3333",
            "email": "not-an-email",
        }
        response = authenticated_client.post("/api/clients", json=client_data)
        assert response.status_code == 400

    def test_create_client_duplicate_email(self, authenticated_client, sample_clients):
        """
        GIVEN client data with duplicate email
        WHEN POST /api/clients is called
        THEN it should return 409 conflict
        """
        client_data = {
            "first_name": "Eve",
            "last_name": "Evans",
            "phone_primary": "555-4444",
            "email": "john.doe@example.com",  # Duplicate
        }
        response = authenticated_client.post("/api/clients", json=client_data)
        assert response.status_code == 409
        data = response.json
        assert "Email already exists" in data["error"]


class TestClientUpdate:
    """Tests for PUT /api/clients/<id>"""

    def test_update_client_success(self, authenticated_client, sample_clients):
        """
        GIVEN a client exists
        WHEN PUT /api/clients/<id> is called with valid data
        THEN it should update the client
        """
        client_id = sample_clients[0]
        update_data = {"city": "Boston", "notes": "Prefers morning appointments"}
        response = authenticated_client.put(f"/api/clients/{client_id}", json=update_data)
        assert response.status_code == 200
        data = response.json
        assert data["city"] == "Boston"
        assert data["notes"] == "Prefers morning appointments"
        assert data["first_name"] == "John"  # Unchanged

    def test_update_client_change_email(self, authenticated_client, sample_clients):
        """
        GIVEN a client exists
        WHEN updating email to a new unique value
        THEN it should succeed
        """
        client_id = sample_clients[0]
        update_data = {"email": "newemail@example.com"}
        response = authenticated_client.put(f"/api/clients/{client_id}", json=update_data)
        assert response.status_code == 200
        data = response.json
        assert data["email"] == "newemail@example.com"

    def test_update_client_duplicate_email(self, authenticated_client, sample_clients):
        """
        GIVEN a client exists
        WHEN updating email to another client's email
        THEN it should return 409 conflict
        """
        client_id = sample_clients[0]
        update_data = {"email": "jane.smith@example.com"}  # Belongs to another client
        response = authenticated_client.put(f"/api/clients/{client_id}", json=update_data)
        assert response.status_code == 409

    def test_update_client_not_found(self, authenticated_client):
        """
        GIVEN a client does not exist
        WHEN PUT /api/clients/9999 is called
        THEN it should return 404
        """
        update_data = {"city": "Seattle"}
        response = authenticated_client.put("/api/clients/9999", json=update_data)
        assert response.status_code == 404

    def test_update_client_validation_error(self, authenticated_client, sample_clients):
        """
        GIVEN invalid update data
        WHEN PUT /api/clients/<id> is called
        THEN it should return 400 validation error
        """
        client_id = sample_clients[0]
        update_data = {"email": "invalid-email"}
        response = authenticated_client.put(f"/api/clients/{client_id}", json=update_data)
        assert response.status_code == 400


class TestClientDelete:
    """Tests for DELETE /api/clients/<id>"""

    def test_soft_delete_client(self, authenticated_client, sample_clients):
        """
        GIVEN a client exists
        WHEN DELETE /api/clients/<id> is called
        THEN it should soft delete (deactivate) the client
        """
        client_id = sample_clients[0]
        response = authenticated_client.delete(f"/api/clients/{client_id}")
        assert response.status_code == 200
        data = response.json
        assert "deactivated" in data["message"]

        # Verify client is soft deleted
        get_response = authenticated_client.get(f"/api/clients/{client_id}")
        assert get_response.status_code == 200
        client_data = get_response.json
        assert client_data["is_active"] is False

    def test_hard_delete_client_as_user(self, authenticated_client, sample_clients):
        """
        GIVEN a regular user
        WHEN DELETE /api/clients/<id>?hard=true is called
        THEN it should return 403 forbidden
        """
        client_id = sample_clients[0]
        response = authenticated_client.delete(f"/api/clients/{client_id}?hard=true")
        assert response.status_code == 403
        data = response.json
        assert "Admin access required" in data["error"]

    def test_hard_delete_client_as_admin(self, admin_client):
        """
        GIVEN an admin user
        WHEN DELETE /api/clients/<id>?hard=true is called
        THEN it should permanently delete the client
        """
        # Create a client to delete
        with admin_client.application.app_context():
            test_client = Client(first_name="ToDelete", last_name="User", phone_primary="555-0000")
            db.session.add(test_client)
            db.session.commit()
            client_id = test_client.id

        response = admin_client.delete(f"/api/clients/{client_id}?hard=true")
        assert response.status_code == 200
        data = response.json
        assert "permanently deleted" in data["message"]

        # Verify client is gone
        get_response = admin_client.get(f"/api/clients/{client_id}")
        assert get_response.status_code == 404

    def test_delete_client_not_found(self, authenticated_client):
        """
        GIVEN a client does not exist
        WHEN DELETE /api/clients/9999 is called
        THEN it should return 404
        """
        response = authenticated_client.delete("/api/clients/9999")
        assert response.status_code == 404


class TestClientIntegration:
    """Integration tests for full client workflows"""

    def test_full_client_lifecycle(self, authenticated_client):
        """
        Test complete CRUD lifecycle:
        Create -> Read -> Update -> Soft Delete -> Read (inactive)
        """
        # Create
        create_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone_primary": "555-0000",
        }
        create_response = authenticated_client.post("/api/clients", json=create_data)
        assert create_response.status_code == 201
        client_id = create_response.json["id"]

        # Read
        get_response = authenticated_client.get(f"/api/clients/{client_id}")
        assert get_response.status_code == 200
        assert get_response.json["email"] == "test@example.com"

        # Update
        update_data = {"city": "Portland"}
        update_response = authenticated_client.put(f"/api/clients/{client_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json["city"] == "Portland"

        # Soft Delete
        delete_response = authenticated_client.delete(f"/api/clients/{client_id}")
        assert delete_response.status_code == 200

        # Read (inactive)
        final_get = authenticated_client.get(f"/api/clients/{client_id}")
        assert final_get.status_code == 200
        assert final_get.json["is_active"] is False
