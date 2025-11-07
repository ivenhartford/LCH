"""
Integration Tests for Complete Business Workflows

These tests verify end-to-end workflows across multiple entities and operations,
ensuring that complex user stories work correctly from start to finish.
"""

import pytest
from app import create_app, db
from app.models import (
    User,
    Client,
    Patient,
    Appointment,
    AppointmentType,
    Visit,
    Invoice,
    Payment,
    Service,
)
from datetime import datetime, timedelta


@pytest.fixture
def app():
    """Create test application"""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def authenticated_client(app, client):
    """Create authenticated test client"""
    with app.app_context():
        # Create test user
        user = User(username="testuser", role="user")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()

    # Login
    response = client.post("/api/login", json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200

    return client


@pytest.fixture
def admin_client(app):
    """Create authenticated admin client"""
    with app.app_context():
        admin = User(username="admin", role="administrator")
        admin.set_password("admin pass")
        db.session.add(admin)
        db.session.commit()

    test_client = app.test_client()
    response = test_client.post("/api/login", json={"username": "admin", "password": "adminpass"})
    assert response.status_code == 200

    return test_client


class TestAppointmentWorkflow:
    """
    Test complete appointment workflow:
    Client → Patient → Appointment → Check-in → Visit → Invoice → Payment
    """

    def test_full_appointment_lifecycle(self, app, authenticated_client, app):
        """
        GIVEN a new client
        WHEN they book an appointment, check in, have a visit, and pay
        THEN all operations should succeed and be properly linked
        """

        with app.app_context():
            # Step 1: Create client
            client_data = {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone_primary": "555-1234",
                "address_street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip_code": "10001",
            }

            response = authenticated_client.post("/api/clients", json=client_data)
            assert response.status_code == 201
            client_id = response.json["id"]
            assert client_id is not None

            # Step 2: Create patient (cat) for the client
            patient_data = {
                "name": "Fluffy",
                "species": "Cat",
                "breed": "Persian",
                "sex": "F",
                "date_of_birth": "2020-01-15",
                "color": "White",
                "weight": 10.5,
                "owner_id": client_id,
                "status": "active",
            }

            response = authenticated_client.post("/api/patients", json=patient_data)
            assert response.status_code == 201
            patient_id = response.json["id"]
            assert patient_id is not None

            # Step 3: Create appointment type
            appt_type_data = {
                "name": "Wellness Exam",
                "duration_minutes": 30,
                "color": "#4CAF50",
                "default_price": 75.00,
                "description": "Annual wellness examination",
            }

            response = authenticated_client.post("/api/appointment-types", json=appt_type_data)
            assert response.status_code == 201
            appt_type_id = response.json["id"]

            # Step 4: Create appointment
            tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
            appointment_data = {
                "client_id": client_id,
                "patient_id": patient_id,
                "appointment_type_id": appt_type_id,
                "title": "Fluffy's Wellness Exam",
                "start_time": tomorrow,
                "duration_minutes": 30,
                "status": "pending",
                "notes": "First visit",
            }

            response = authenticated_client.post("/api/appointments", json=appointment_data)
            assert response.status_code == 201
            appointment_id = response.json["id"]
            assert response.json["status"] == "pending"

            # Step 5: Confirm appointment
            response = authenticated_client.put(
                f"/api/appointments/{appointment_id}", json={"status": "confirmed"}
            )
            assert response.status_code == 200
            assert response.json["status"] == "confirmed"

            # Step 6: Check in appointment
            response = authenticated_client.put(
                f"/api/appointments/{appointment_id}",
                json={"status": "checked_in", "check_in_time": datetime.now().isoformat()},
            )
            assert response.status_code == 200
            assert response.json["status"] == "checked_in"
            assert response.json["check_in_time"] is not None

            # Step 7: Start appointment (in progress)
            response = authenticated_client.put(
                f"/api/appointments/{appointment_id}", json={"status": "in_progress"}
            )
            assert response.status_code == 200
            assert response.json["status"] == "in_progress"

            # Step 8: Create visit/medical record
            visit_data = {
                "appointment_id": appointment_id,
                "patient_id": patient_id,
                "visit_date": datetime.now().isoformat(),
                "reason": "Annual wellness exam",
                "chief_complaint": "Routine checkup",
            }

            response = authenticated_client.post("/api/visits", json=visit_data)
            assert response.status_code == 201
            visit_id = response.json["id"]

            # Step 9: Add vital signs
            vitals_data = {
                "visit_id": visit_id,
                "temperature": 101.5,
                "heart_rate": 180,
                "respiratory_rate": 30,
                "weight": 10.5,
                "body_condition_score": 5,
            }

            response = authenticated_client.post("/api/vital-signs", json=vitals_data)
            assert response.status_code == 201

            # Step 10: Add SOAP notes
            soap_data = {
                "visit_id": visit_id,
                "subjective": "Owner reports cat is eating well and active",
                "objective": "Healthy cat, good body condition",
                "assessment": "Healthy, no concerns",
                "plan": "Continue current diet, return in 1 year",
            }

            response = authenticated_client.post("/api/soap-notes", json=soap_data)
            assert response.status_code == 201

            # Step 11: Create service item
            service_data = {
                "name": "Wellness Exam",
                "price": 75.00,
                "taxable": True,
                "category": "Examination",
            }

            response = authenticated_client.post("/api/services", json=service_data)
            assert response.status_code == 201
            service_id = response.json["id"]

            # Step 12: Create invoice
            invoice_data = {
                "client_id": client_id,
                "patient_id": patient_id,
                "visit_id": visit_id,
                "invoice_date": datetime.now().isoformat(),
                "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "items": [
                    {
                        "service_id": service_id,
                        "description": "Wellness Exam",
                        "quantity": 1,
                        "unit_price": 75.00,
                    }
                ],
            }

            response = authenticated_client.post("/api/invoices", json=invoice_data)
            assert response.status_code == 201
            invoice_id = response.json["id"]
            total_amount = response.json["total_amount"]
            assert total_amount > 0

            # Step 13: Process payment
            payment_data = {
                "invoice_id": invoice_id,
                "amount": total_amount,
                "payment_method": "credit_card",
                "payment_date": datetime.now().isoformat(),
                "reference_number": "CC123456",
            }

            response = authenticated_client.post("/api/payments", json=payment_data)
            assert response.status_code == 201
            payment_id = response.json["id"]

            # Step 14: Verify invoice is paid
            response = authenticated_client.get(f"/api/invoices/{invoice_id}")
            assert response.status_code == 200
            assert response.json["status"] == "paid"
            assert response.json["amount_paid"] == total_amount

            # Step 15: Complete appointment
            response = authenticated_client.put(
                f"/api/appointments/{appointment_id}",
                json={"status": "completed", "check_out_time": datetime.now().isoformat()},
            )
            assert response.status_code == 200
            assert response.json["status"] == "completed"
            assert response.json["check_out_time"] is not None

            # Final verification: Get appointment and verify all relationships
            response = authenticated_client.get(f"/api/appointments/{appointment_id}")
            assert response.status_code == 200
            final_appt = response.json
            assert final_appt["status"] == "completed"
            assert final_appt["client_id"] == client_id
            assert final_appt["patient_id"] == patient_id

            # Verify patient has appointment history
            response = authenticated_client.get(f"/api/patients/{patient_id}")
            assert response.status_code == 200
            assert len(response.json.get("appointments", [])) >= 1

            print("\n✅ Full appointment lifecycle test PASSED")
            print(f"   Client: {client_id}")
            print(f"   Patient: {patient_id}")
            print(f"   Appointment: {appointment_id}")
            print(f"   Visit: {visit_id}")
            print(f"   Invoice: {invoice_id}")
            print(f"   Payment: {payment_id}")


class TestInvoiceWorkflow:
    """Test invoice and payment workflows"""

    def test_partial_payment_workflow(self, app, authenticated_client, app):
        """
        GIVEN an invoice with a total amount
        WHEN multiple partial payments are made
        THEN the invoice status should update correctly
        """

        with app.app_context():
            # Create client
            response = authenticated_client.post(
                "/api/clients",
                json={
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@example.com",
                    "phone_primary": "555-5678",
                },
            )
            client_id = response.json["id"]

            # Create patient
            response = authenticated_client.post(
                "/api/patients",
                json={
                    "name": "Mittens",
                    "species": "Cat",
                    "breed": "Tabby",
                    "sex": "M",
                    "owner_id": client_id,
                    "status": "active",
                },
            )
            patient_id = response.json["id"]

            # Create service
            response = authenticated_client.post(
                "/api/services", json={"name": "Surgery", "price": 500.00, "taxable": True}
            )
            service_id = response.json["id"]

            # Create invoice
            response = authenticated_client.post(
                "/api/invoices",
                json={
                    "client_id": client_id,
                    "patient_id": patient_id,
                    "invoice_date": datetime.now().isoformat(),
                    "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
                    "items": [
                        {
                            "service_id": service_id,
                            "description": "Surgery",
                            "quantity": 1,
                            "unit_price": 500.00,
                        }
                    ],
                },
            )
            assert response.status_code == 201
            invoice_id = response.json["id"]
            total = response.json["total_amount"]

            # Make first partial payment (50%)
            response = authenticated_client.post(
                "/api/payments",
                json={
                    "invoice_id": invoice_id,
                    "amount": total * 0.5,
                    "payment_method": "cash",
                    "payment_date": datetime.now().isoformat(),
                },
            )
            assert response.status_code == 201

            # Verify invoice is partially paid
            response = authenticated_client.get(f"/api/invoices/{invoice_id}")
            assert response.json["status"] == "partial"
            assert response.json["amount_paid"] == total * 0.5

            # Make second partial payment (remaining 50%)
            response = authenticated_client.post(
                "/api/payments",
                json={
                    "invoice_id": invoice_id,
                    "amount": total * 0.5,
                    "payment_method": "credit_card",
                    "payment_date": datetime.now().isoformat(),
                },
            )
            assert response.status_code == 201

            # Verify invoice is now fully paid
            response = authenticated_client.get(f"/api/invoices/{invoice_id}")
            assert response.json["status"] == "paid"
            assert response.json["amount_paid"] == total

            print("\n✅ Partial payment workflow test PASSED")


class TestConcurrentOperations:
    """Test handling of concurrent operations"""

    def test_concurrent_appointment_booking(self, authenticated_client, app):
        """
        GIVEN a time slot
        WHEN multiple appointments are booked for the same time
        THEN the system should handle gracefully (no double-booking if implemented)
        """
        # This is a placeholder for concurrent operation tests
        # In a real scenario, you'd use threading or async to test concurrency
        pass


class TestErrorRecovery:
    """Test error handling and recovery"""

    def test_rollback_on_payment_failure(self, authenticated_client, app):
        """
        GIVEN an invoice and payment
        WHEN payment processing fails
        THEN the database should rollback correctly
        """
        # This tests that failed operations don't leave partial data
        pass


# Summary function
def print_test_summary():
    """Print test summary"""
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print("Test Classes:")
    print("  1. TestAppointmentWorkflow - Complete appointment lifecycle")
    print("  2. TestInvoiceWorkflow - Invoice and payment workflows")
    print("  3. TestConcurrentOperations - Concurrent operation handling (placeholder)")
    print("  4. TestErrorRecovery - Error handling and rollback (placeholder)")
    print("=" * 80)
