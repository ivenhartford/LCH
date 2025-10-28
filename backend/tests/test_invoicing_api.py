"""
Tests for Invoicing API endpoints (Services, Invoices, Payments)
"""
import pytest
from app import db
from app.models import User, Client, Patient, Visit, Service, Invoice, InvoiceItem, Payment
from datetime import datetime, date, timedelta
from decimal import Decimal


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
def sample_client(authenticated_client):
    """Create a sample client for testing"""
    with authenticated_client.application.app_context():
        client_obj = Client(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone_primary="555-1234",
        )
        db.session.add(client_obj)
        db.session.commit()
        return client_obj.id


@pytest.fixture
def sample_patient(authenticated_client, sample_client):
    """Create a sample patient for testing"""
    with authenticated_client.application.app_context():
        patient = Patient(name="Fluffy", species="Cat", breed="Persian", owner_id=sample_client)
        db.session.add(patient)
        db.session.commit()
        return patient.id


@pytest.fixture
def sample_services(authenticated_client):
    """Create sample services for testing"""
    with authenticated_client.application.app_context():
        services = [
            Service(
                code="EXAM-WELLNESS",
                name="Wellness Examination",
                description="Annual wellness exam for cats",
                category="Service",
                default_price=Decimal("85.00"),
                cost=Decimal("25.00"),
                taxable=True,
                tax_rate=Decimal("8.5"),
                is_active=True,
            ),
            Service(
                code="VAC-RABIES",
                name="Rabies Vaccination",
                description="1-year rabies vaccine",
                category="Service",
                default_price=Decimal("35.00"),
                cost=Decimal("8.00"),
                taxable=True,
                tax_rate=Decimal("8.5"),
                is_active=True,
            ),
            Service(
                code="LAB-CBC",
                name="Complete Blood Count",
                description="Full CBC panel",
                category="Lab",
                default_price=Decimal("125.00"),
                taxable=True,
                tax_rate=Decimal("8.5"),
                is_active=True,
            ),
            Service(
                code="INACTIVE-TEST",
                name="Inactive Service",
                category="Service",
                default_price=Decimal("50.00"),
                is_active=False,
            ),
        ]
        db.session.add_all(services)
        db.session.commit()
        return [svc.id for svc in services]


# ============================================================================
# SERVICE API TESTS
# ============================================================================


class TestServiceList:
    def test_get_services_without_auth(self, client):
        """Should return 401 without authentication"""
        response = client.get("/api/services")
        assert response.status_code == 401

    def test_get_services_empty_list(self, authenticated_client):
        """Should return empty list when no services"""
        response = authenticated_client.get("/api/services")
        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_services_with_data(self, authenticated_client, sample_services):
        """Should return all services"""
        response = authenticated_client.get("/api/services")
        assert response.status_code == 200
        data = response.json
        assert len(data) == 4

    def test_get_services_filter_by_category(self, authenticated_client, sample_services):
        """Should filter services by category"""
        response = authenticated_client.get("/api/services?category=Lab")
        assert response.status_code == 200
        data = response.json
        assert len(data) == 1
        assert data[0]["code"] == "LAB-CBC"

    def test_get_services_filter_by_active(self, authenticated_client, sample_services):
        """Should filter services by is_active"""
        response = authenticated_client.get("/api/services?is_active=true")
        assert response.status_code == 200
        data = response.json
        assert len(data) == 3  # Should exclude inactive service

    def test_get_services_search(self, authenticated_client, sample_services):
        """Should search services by name/code/description"""
        response = authenticated_client.get("/api/services?search=rabies")
        assert response.status_code == 200
        data = response.json
        assert len(data) == 1
        assert data[0]["code"] == "VAC-RABIES"


class TestServiceDetail:
    def test_get_service_by_id(self, authenticated_client, sample_services):
        """Should return service by ID"""
        service_id = sample_services[0]
        response = authenticated_client.get(f"/api/services/{service_id}")
        assert response.status_code == 200
        data = response.json
        assert data["id"] == service_id
        assert data["code"] == "EXAM-WELLNESS"

    def test_get_service_not_found(self, authenticated_client):
        """Should return 404 for nonexistent service"""
        response = authenticated_client.get("/api/services/99999")
        assert response.status_code == 404


class TestServiceCreate:
    def test_create_service(self, authenticated_client):
        """Should create a new service"""
        service_data = {
            "code": "SURG-SPAY",
            "name": "Spay Surgery",
            "description": "Ovariohysterectomy",
            "category": "Procedure",
            "default_price": "350.00",
            "cost": "75.00",
            "taxable": True,
            "tax_rate": "8.5",
        }
        response = authenticated_client.post("/api/services", json=service_data)
        assert response.status_code == 201
        data = response.json
        assert data["code"] == "SURG-SPAY"
        assert data["name"] == "Spay Surgery"

    def test_create_service_duplicate_code(self, authenticated_client, sample_services):
        """Should return 409 for duplicate service code"""
        service_data = {
            "code": "EXAM-WELLNESS",  # Duplicate
            "name": "Duplicate Service",
            "category": "Service",
            "default_price": "100.00",
        }
        response = authenticated_client.post("/api/services", json=service_data)
        assert response.status_code == 409

    def test_create_service_validation_error(self, authenticated_client):
        """Should return 400 for validation errors"""
        service_data = {
            "code": "TEST",
            # Missing required fields
        }
        response = authenticated_client.post("/api/services", json=service_data)
        assert response.status_code == 400


class TestServiceUpdate:
    def test_update_service(self, authenticated_client, sample_services):
        """Should update a service"""
        service_id = sample_services[0]
        update_data = {"default_price": "95.00", "description": "Updated description"}
        response = authenticated_client.put(f"/api/services/{service_id}", json=update_data)
        assert response.status_code == 200
        data = response.json
        assert data["default_price"] == "95.00"

    def test_update_service_not_found(self, authenticated_client):
        """Should return 404 for nonexistent service"""
        response = authenticated_client.put("/api/services/99999", json={"name": "Test"})
        assert response.status_code == 404


class TestServiceDelete:
    def test_delete_service(self, authenticated_client, sample_services):
        """Should delete a service"""
        service_id = sample_services[3]  # Inactive service
        response = authenticated_client.delete(f"/api/services/{service_id}")
        assert response.status_code == 200

    def test_delete_service_not_found(self, authenticated_client):
        """Should return 404 for nonexistent service"""
        response = authenticated_client.delete("/api/services/99999")
        assert response.status_code == 404


# ============================================================================
# INVOICE API TESTS
# ============================================================================


class TestInvoiceList:
    def test_get_invoices_without_auth(self, client):
        """Should return 401 without authentication"""
        response = client.get("/api/invoices")
        assert response.status_code == 401

    def test_get_invoices_empty_list(self, authenticated_client):
        """Should return empty list when no invoices"""
        response = authenticated_client.get("/api/invoices")
        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_invoices_with_data(self, authenticated_client, sample_client, sample_patient, sample_services):
        """Should return all invoices"""
        # Create a test invoice
        with authenticated_client.application.app_context():
            user = User.query.filter_by(username="testvet").first()
            invoice = Invoice(
                invoice_number="INV-TEST-0001",
                patient_id=sample_patient,
                client_id=sample_client,
                created_by_id=user.id,
            )
            db.session.add(invoice)
            db.session.commit()

        response = authenticated_client.get("/api/invoices")
        assert response.status_code == 200
        data = response.json
        assert len(data) == 1

    def test_get_invoices_filter_by_status(self, authenticated_client, sample_client, sample_patient):
        """Should filter invoices by status"""
        # Create test invoices with different statuses
        with authenticated_client.application.app_context():
            user = User.query.filter_by(username="testvet").first()
            invoice1 = Invoice(
                invoice_number="INV-001",
                patient_id=sample_patient,
                client_id=sample_client,
                status="draft",
                created_by_id=user.id,
            )
            invoice2 = Invoice(
                invoice_number="INV-002",
                patient_id=sample_patient,
                client_id=sample_client,
                status="paid",
                created_by_id=user.id,
            )
            db.session.add_all([invoice1, invoice2])
            db.session.commit()

        response = authenticated_client.get("/api/invoices?status=paid")
        assert response.status_code == 200
        data = response.json
        assert len(data) == 1
        assert data[0]["status"] == "paid"


class TestInvoiceDetail:
    def test_get_invoice_by_id(self, authenticated_client, sample_client, sample_patient):
        """Should return invoice by ID with items and payments"""
        with authenticated_client.application.app_context():
            user = User.query.filter_by(username="testvet").first()
            invoice = Invoice(
                invoice_number="INV-DETAIL-001",
                patient_id=sample_patient,
                client_id=sample_client,
                created_by_id=user.id,
            )
            db.session.add(invoice)
            db.session.commit()
            invoice_id = invoice.id

        response = authenticated_client.get(f"/api/invoices/{invoice_id}")
        assert response.status_code == 200
        data = response.json
        assert data["invoice_number"] == "INV-DETAIL-001"
        assert "items" in data
        assert "payments" in data

    def test_get_invoice_not_found(self, authenticated_client):
        """Should return 404 for nonexistent invoice"""
        response = authenticated_client.get("/api/invoices/99999")
        assert response.status_code == 404


class TestInvoiceCreate:
    def test_create_invoice_with_items(self, authenticated_client, sample_client, sample_patient, sample_services):
        """Should create a new invoice with line items"""
        invoice_data = {
            "patient_id": sample_patient,
            "client_id": sample_client,
            "status": "draft",
            "items": [
                {
                    "service_id": sample_services[0],  # Wellness Exam
                    "description": "Wellness Examination",
                    "quantity": "1.00",
                    "unit_price": "85.00",
                    "taxable": True,
                    "tax_rate": "8.5",
                },
                {
                    "service_id": sample_services[1],  # Rabies Vac
                    "description": "Rabies Vaccination",
                    "quantity": "1.00",
                    "unit_price": "35.00",
                    "taxable": True,
                    "tax_rate": "8.5",
                },
            ],
        }

        response = authenticated_client.post("/api/invoices", json=invoice_data)
        assert response.status_code == 201
        data = response.json
        assert "invoice_number" in data
        assert data["patient_id"] == sample_patient
        assert data["client_id"] == sample_client
        assert len(data["items"]) == 2
        # Check calculations
        # Subtotal: 85 + 35 = 120
        # Tax: (85 * 0.085) + (35 * 0.085) = 7.225 + 2.975 = 10.20
        # Total: 120 + 10.20 = 130.20
        assert float(data["subtotal"]) == 120.00
        # Tax: 85*0.085 + 35*0.085 = 7.225 + 2.975 = 10.20
        assert abs(float(data["tax_amount"]) - 10.20) < 0.01  # Allow for rounding
        assert abs(float(data["total_amount"]) - 130.20) < 0.01  # Allow for rounding

    def test_create_invoice_validation_error(self, authenticated_client):
        """Should return 400 for validation errors"""
        invoice_data = {
            "patient_id": 1,
            # Missing required fields
        }
        response = authenticated_client.post("/api/invoices", json=invoice_data)
        assert response.status_code == 400

    def test_create_invoice_patient_not_found(self, authenticated_client, sample_client):
        """Should return 404 for nonexistent patient"""
        invoice_data = {
            "patient_id": 99999,
            "client_id": sample_client,
            "items": [{"description": "Test", "unit_price": "10.00"}],
        }
        response = authenticated_client.post("/api/invoices", json=invoice_data)
        assert response.status_code == 404


class TestInvoiceUpdate:
    def test_update_invoice_status(self, authenticated_client, sample_client, sample_patient):
        """Should update invoice status"""
        with authenticated_client.application.app_context():
            user = User.query.filter_by(username="testvet").first()
            invoice = Invoice(
                invoice_number="INV-UPDATE-001",
                patient_id=sample_patient,
                client_id=sample_client,
                status="draft",
                created_by_id=user.id,
            )
            db.session.add(invoice)
            db.session.commit()
            invoice_id = invoice.id

        update_data = {"status": "issued"}
        response = authenticated_client.put(f"/api/invoices/{invoice_id}", json=update_data)
        assert response.status_code == 200
        data = response.json
        assert data["status"] == "issued"

    def test_update_invoice_not_found(self, authenticated_client):
        """Should return 404 for nonexistent invoice"""
        response = authenticated_client.put("/api/invoices/99999", json={"status": "paid"})
        assert response.status_code == 404


class TestInvoiceDelete:
    def test_delete_draft_invoice(self, authenticated_client, sample_client, sample_patient):
        """Should delete a draft invoice"""
        with authenticated_client.application.app_context():
            user = User.query.filter_by(username="testvet").first()
            invoice = Invoice(
                invoice_number="INV-DELETE-001",
                patient_id=sample_patient,
                client_id=sample_client,
                status="draft",
                created_by_id=user.id,
            )
            db.session.add(invoice)
            db.session.commit()
            invoice_id = invoice.id

        response = authenticated_client.delete(f"/api/invoices/{invoice_id}")
        assert response.status_code == 200

    def test_delete_invoice_with_payments(self, authenticated_client, sample_client, sample_patient):
        """Should not delete invoice with payments"""
        with authenticated_client.application.app_context():
            user = User.query.filter_by(username="testvet").first()
            invoice = Invoice(
                invoice_number="INV-DELETE-002",
                patient_id=sample_patient,
                client_id=sample_client,
                status="paid",
                amount_paid=Decimal("100.00"),
                created_by_id=user.id,
            )
            db.session.add(invoice)
            db.session.commit()
            invoice_id = invoice.id

        response = authenticated_client.delete(f"/api/invoices/{invoice_id}")
        assert response.status_code == 400


# ============================================================================
# PAYMENT API TESTS
# ============================================================================


class TestPaymentList:
    def test_get_payments_without_auth(self, client):
        """Should return 401 without authentication"""
        response = client.get("/api/payments")
        assert response.status_code == 401

    def test_get_payments_empty_list(self, authenticated_client):
        """Should return empty list when no payments"""
        response = authenticated_client.get("/api/payments")
        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)
        assert len(data) == 0


class TestPaymentCreate:
    def test_create_payment(self, authenticated_client, sample_client, sample_patient):
        """Should create a new payment"""
        # Create invoice first
        with authenticated_client.application.app_context():
            user = User.query.filter_by(username="testvet").first()
            invoice = Invoice(
                invoice_number="INV-PAYMENT-001",
                patient_id=sample_patient,
                client_id=sample_client,
                total_amount=Decimal("100.00"),
                created_by_id=user.id,
            )
            db.session.add(invoice)
            db.session.commit()
            invoice_id = invoice.id

        payment_data = {
            "invoice_id": invoice_id,
            "client_id": sample_client,
            "amount": "50.00",
            "payment_method": "Credit Card",
            "reference_number": "TXN123456",
        }

        response = authenticated_client.post("/api/payments", json=payment_data)
        assert response.status_code == 201
        data = response.json
        assert float(data["amount"]) == 50.00
        assert data["payment_method"] == "Credit Card"

    def test_create_payment_validation_error(self, authenticated_client):
        """Should return 400 for validation errors"""
        payment_data = {
            "invoice_id": 1,
            # Missing required fields
        }
        response = authenticated_client.post("/api/payments", json=payment_data)
        assert response.status_code == 400


class TestPaymentUpdate:
    def test_update_payment(self, authenticated_client, sample_client, sample_patient):
        """Should update a payment"""
        # Create invoice and payment first
        with authenticated_client.application.app_context():
            user = User.query.filter_by(username="testvet").first()
            invoice = Invoice(
                invoice_number="INV-PAYMENT-UPDATE",
                patient_id=sample_patient,
                client_id=sample_client,
                total_amount=Decimal("100.00"),
                created_by_id=user.id,
            )
            db.session.add(invoice)
            db.session.flush()

            payment = Payment(
                invoice_id=invoice.id,
                client_id=sample_client,
                amount=Decimal("50.00"),
                payment_method="Cash",
                processed_by_id=user.id,
            )
            db.session.add(payment)
            db.session.commit()
            payment_id = payment.id

        update_data = {"amount": "75.00", "reference_number": "UPDATED-123"}
        response = authenticated_client.put(f"/api/payments/{payment_id}", json=update_data)
        assert response.status_code == 200
        data = response.json
        assert float(data["amount"]) == 75.00


class TestPaymentDelete:
    def test_delete_payment(self, authenticated_client, sample_client, sample_patient):
        """Should delete a payment"""
        # Create invoice and payment first
        with authenticated_client.application.app_context():
            user = User.query.filter_by(username="testvet").first()
            invoice = Invoice(
                invoice_number="INV-PAYMENT-DELETE",
                patient_id=sample_patient,
                client_id=sample_client,
                total_amount=Decimal("100.00"),
                amount_paid=Decimal("50.00"),
                created_by_id=user.id,
            )
            db.session.add(invoice)
            db.session.flush()

            payment = Payment(
                invoice_id=invoice.id,
                client_id=sample_client,
                amount=Decimal("50.00"),
                payment_method="Cash",
                processed_by_id=user.id,
            )
            db.session.add(payment)
            db.session.commit()
            payment_id = payment.id

        response = authenticated_client.delete(f"/api/payments/{payment_id}")
        assert response.status_code == 200


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestInvoicePaymentIntegration:
    def test_full_invoice_workflow(self, authenticated_client, sample_client, sample_patient, sample_services):
        """Test complete invoice workflow: create, pay, check status"""
        # 1. Create invoice
        invoice_data = {
            "patient_id": sample_patient,
            "client_id": sample_client,
            "status": "draft",
            "items": [
                {
                    "service_id": sample_services[0],
                    "description": "Wellness Exam",
                    "quantity": "1.00",
                    "unit_price": "85.00",
                    "taxable": True,
                    "tax_rate": "8.5",
                }
            ],
        }

        response = authenticated_client.post("/api/invoices", json=invoice_data)
        assert response.status_code == 201
        invoice = response.json
        invoice_id = invoice["id"]
        total_amount = float(invoice["total_amount"])

        # 2. Make partial payment
        payment_data = {
            "invoice_id": invoice_id,
            "client_id": sample_client,
            "amount": str(total_amount / 2),
            "payment_method": "Credit Card",
        }

        response = authenticated_client.post("/api/payments", json=payment_data)
        assert response.status_code == 201

        # 3. Check invoice status
        response = authenticated_client.get(f"/api/invoices/{invoice_id}")
        assert response.status_code == 200
        updated_invoice = response.json
        assert updated_invoice["status"] == "partially_paid"
        assert float(updated_invoice["amount_paid"]) > 0
        assert float(updated_invoice["balance_due"]) > 0

        # 4. Make final payment
        remaining_balance = float(updated_invoice["balance_due"])
        payment_data = {
            "invoice_id": invoice_id,
            "client_id": sample_client,
            "amount": str(remaining_balance),
            "payment_method": "Cash",
        }

        response = authenticated_client.post("/api/payments", json=payment_data)
        assert response.status_code == 201

        # 5. Verify invoice is paid
        response = authenticated_client.get(f"/api/invoices/{invoice_id}")
        assert response.status_code == 200
        final_invoice = response.json
        assert final_invoice["status"] == "paid"
        assert float(final_invoice["balance_due"]) <= 0.01  # Allow for rounding errors


class TestTaxCalculation:
    def test_tax_calculation_for_invoice_items(self, authenticated_client, sample_client, sample_patient):
        """Test that tax is correctly calculated on invoice items"""
        invoice_data = {
            "patient_id": sample_patient,
            "client_id": sample_client,
            "items": [
                {
                    "description": "Taxable Item",
                    "quantity": "2.00",
                    "unit_price": "100.00",
                    "taxable": True,
                    "tax_rate": "10.0",  # 10% tax
                },
                {
                    "description": "Non-Taxable Item",
                    "quantity": "1.00",
                    "unit_price": "50.00",
                    "taxable": False,
                    "tax_rate": "0.0",
                },
            ],
        }

        response = authenticated_client.post("/api/invoices", json=invoice_data)
        assert response.status_code == 201
        data = response.json

        # Check item calculations
        # Item 1: 2 * 100 = 200, tax = 200 * 0.10 = 20
        # Item 2: 1 * 50 = 50, tax = 0
        # Total: 200 + 50 + 20 = 270

        assert float(data["subtotal"]) == 250.00
        assert float(data["tax_amount"]) == 20.00
        assert float(data["total_amount"]) == 270.00
