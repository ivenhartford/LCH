"""
Tests for Treatment Plans & Protocols API (Phase 4.2)

Tests cover:
- Protocol CRUD operations
- Protocol step management
- Apply protocol to patient
- TreatmentPlan CRUD operations
- TreatmentPlan step updates
- Cost calculations
- Progress tracking
- Status workflows
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.models import (
    Protocol,
    ProtocolStep,
    TreatmentPlan,
    TreatmentPlanStep,
    Patient,
    Client,
    User,
)


# ============================================================================
# Protocol Tests
# ============================================================================


def test_get_protocols_empty(client, auth_headers):
    """Test getting protocols when none exist"""
    response = client.get("/api/protocols", headers=auth_headers)
    assert response.status_code == 200
    assert response.json == []


def test_create_protocol_basic(client, auth_headers, test_user):
    """Test creating a basic protocol without steps"""
    data = {
        "name": "Basic Protocol",
        "description": "A simple test protocol",
        "category": "wellness",
        "is_active": True,
        "default_duration_days": 7,
        "estimated_cost": "100.00",
        "notes": "Test notes",
    }

    response = client.post("/api/protocols", json=data, headers=auth_headers)
    assert response.status_code == 201

    result = response.json
    assert result["name"] == "Basic Protocol"
    assert result["category"] == "wellness"
    assert result["is_active"] is True
    assert result["default_duration_days"] == 7
    assert float(result["estimated_cost"]) == 100.00
    assert result["created_by_id"] == test_user.id
    assert result["step_count"] == 0


def test_create_protocol_with_steps(client, auth_headers):
    """Test creating a protocol with steps"""
    data = {
        "name": "Dental Cleaning Protocol",
        "description": "Standard dental procedure",
        "category": "dental",
        "estimated_cost": "350.00",
        "steps": [
            {
                "step_number": 1,
                "title": "Pre-op exam",
                "description": "Physical examination and bloodwork",
                "day_offset": 0,
                "estimated_cost": "75.00",
            },
            {
                "step_number": 2,
                "title": "Dental cleaning",
                "description": "Anesthesia and cleaning",
                "day_offset": 1,
                "estimated_cost": "250.00",
            },
            {
                "step_number": 3,
                "title": "Post-op check",
                "description": "Follow-up examination",
                "day_offset": 3,
                "estimated_cost": "25.00",
            },
        ],
    }

    response = client.post("/api/protocols", json=data, headers=auth_headers)
    assert response.status_code == 201

    result = response.json
    assert result["name"] == "Dental Cleaning Protocol"
    assert result["step_count"] == 3
    assert len(result["steps"]) == 3

    # Verify steps
    assert result["steps"][0]["title"] == "Pre-op exam"
    assert result["steps"][0]["day_offset"] == 0
    assert float(result["steps"][0]["estimated_cost"]) == 75.00


def test_create_protocol_validation_error(client, auth_headers):
    """Test creating protocol with invalid data"""
    data = {"name": "", "category": "wellness"}  # Empty name should fail

    response = client.post("/api/protocols", json=data, headers=auth_headers)
    assert response.status_code == 400


def test_get_protocol_by_id(client, auth_headers, test_user, session):
    """Test getting a single protocol by ID"""
    # Create test protocol
    protocol = Protocol(
        name="Test Protocol",
        description="Test description",
        category="surgical",
        created_by_id=test_user.id,
    )
    session.add(protocol)
    session.flush()

    # Add steps
    step1 = ProtocolStep(protocol_id=protocol.id, step_number=1, title="Step 1", day_offset=0)
    step2 = ProtocolStep(protocol_id=protocol.id, step_number=2, title="Step 2", day_offset=1)
    session.add_all([step1, step2])
    session.commit()

    # Get protocol
    response = client.get(f"/api/protocols/{protocol.id}", headers=auth_headers)
    assert response.status_code == 200

    result = response.json
    assert result["id"] == protocol.id
    assert result["name"] == "Test Protocol"
    assert len(result["steps"]) == 2


def test_get_protocol_not_found(client, auth_headers):
    """Test getting non-existent protocol"""
    response = client.get("/api/protocols/99999", headers=auth_headers)
    assert response.status_code == 404


def test_update_protocol(client, auth_headers, test_user, session):
    """Test updating a protocol"""
    protocol = Protocol(
        name="Original Name",
        description="Original description",
        category="wellness",
        created_by_id=test_user.id,
    )
    session.add(protocol)
    session.commit()

    # Update protocol
    data = {
        "name": "Updated Name",
        "description": "Updated description",
        "category": "dental",
        "is_active": False,
    }

    response = client.put(f"/api/protocols/{protocol.id}", json=data, headers=auth_headers)
    assert response.status_code == 200

    result = response.json
    assert result["name"] == "Updated Name"
    assert result["description"] == "Updated description"
    assert result["category"] == "dental"
    assert result["is_active"] is False


def test_delete_protocol_soft(client, auth_headers, test_user, session):
    """Test soft deleting (deactivating) a protocol"""
    protocol = Protocol(name="Test Protocol", is_active=True, created_by_id=test_user.id)
    session.add(protocol)
    session.commit()

    # Soft delete (default)
    response = client.delete(f"/api/protocols/{protocol.id}", headers=auth_headers)
    assert response.status_code == 200
    assert "deactivated" in response.json["message"].lower()

    # Verify still exists but inactive
    session.refresh(protocol)
    assert protocol.is_active is False


def test_delete_protocol_hard(client, auth_headers, test_user, session):
    """Test hard deleting (permanently removing) a protocol"""
    protocol = Protocol(name="Test Protocol", created_by_id=test_user.id)
    session.add(protocol)
    session.commit()
    protocol_id = protocol.id

    # Hard delete
    response = client.delete(f"/api/protocols/{protocol_id}?permanent=true", headers=auth_headers)
    assert response.status_code == 200
    assert "permanently deleted" in response.json["message"].lower()

    # Verify actually deleted
    deleted_protocol = session.query(Protocol).filter_by(id=protocol_id).first()
    assert deleted_protocol is None


def test_filter_protocols_by_category(client, auth_headers, test_user, session):
    """Test filtering protocols by category"""
    # Create protocols with different categories
    protocol1 = Protocol(name="Dental Protocol", category="dental", created_by_id=test_user.id)
    protocol2 = Protocol(name="Surgical Protocol", category="surgical", created_by_id=test_user.id)
    protocol3 = Protocol(name="Wellness Protocol", category="wellness", created_by_id=test_user.id)
    session.add_all([protocol1, protocol2, protocol3])
    session.commit()

    # Filter by dental
    response = client.get("/api/protocols?category=dental", headers=auth_headers)
    assert response.status_code == 200
    results = response.json
    assert len(results) == 1
    assert results[0]["name"] == "Dental Protocol"


def test_filter_protocols_by_active_status(client, auth_headers, test_user, session):
    """Test filtering protocols by active status"""
    protocol1 = Protocol(name="Active Protocol", is_active=True, created_by_id=test_user.id)
    protocol2 = Protocol(name="Inactive Protocol", is_active=False, created_by_id=test_user.id)
    session.add_all([protocol1, protocol2])
    session.commit()

    # Filter by active
    response = client.get("/api/protocols?is_active=true", headers=auth_headers)
    assert response.status_code == 200
    results = response.json
    assert len(results) == 1
    assert results[0]["name"] == "Active Protocol"


def test_search_protocols(client, auth_headers, test_user, session):
    """Test searching protocols by name/description"""
    protocol1 = Protocol(
        name="Dental Cleaning", description="Teeth cleaning", created_by_id=test_user.id
    )
    protocol2 = Protocol(
        name="Surgery Protocol", description="Surgical procedure", created_by_id=test_user.id
    )
    session.add_all([protocol1, protocol2])
    session.commit()

    # Search for "dental"
    response = client.get("/api/protocols?search=dental", headers=auth_headers)
    assert response.status_code == 200
    results = response.json
    assert len(results) == 1
    assert results[0]["name"] == "Dental Cleaning"


# ============================================================================
# Apply Protocol to Patient Tests
# ============================================================================


def test_apply_protocol_to_patient(client, auth_headers, test_user, test_patient, session):
    """Test applying a protocol to create a treatment plan"""
    # Create protocol with steps
    protocol = Protocol(
        name="Spay Protocol",
        description="Standard spay procedure",
        default_duration_days=10,
        estimated_cost=Decimal("450.00"),
        created_by_id=test_user.id,
    )
    session.add(protocol)
    session.flush()

    steps = [
        ProtocolStep(
            protocol_id=protocol.id,
            step_number=1,
            title="Pre-op",
            day_offset=0,
            estimated_cost=Decimal("85.00"),
        ),
        ProtocolStep(
            protocol_id=protocol.id,
            step_number=2,
            title="Surgery",
            day_offset=1,
            estimated_cost=Decimal("325.00"),
        ),
        ProtocolStep(
            protocol_id=protocol.id,
            step_number=3,
            title="Follow-up",
            day_offset=10,
            estimated_cost=Decimal("40.00"),
        ),
    ]
    session.add_all(steps)
    session.commit()

    # Apply protocol to patient
    start_date = datetime.now().date()
    data = {"patient_id": test_patient.id, "start_date": start_date.isoformat()}

    response = client.post(f"/api/protocols/{protocol.id}/apply", json=data, headers=auth_headers)
    assert response.status_code == 201

    result = response.json
    assert result["name"] == f"Spay Protocol - {test_patient.name}"
    assert result["patient_id"] == test_patient.id
    assert result["protocol_id"] == protocol.id
    assert result["status"] == "draft"
    assert float(result["total_estimated_cost"]) == 450.00
    assert result["step_count"] == 3

    # Verify steps were copied with scheduled dates
    assert len(result["steps"]) == 3
    assert result["steps"][0]["title"] == "Pre-op"
    assert result["steps"][0]["scheduled_date"] == start_date.isoformat()
    assert result["steps"][1]["scheduled_date"] == (start_date + timedelta(days=1)).isoformat()
    assert result["steps"][2]["scheduled_date"] == (start_date + timedelta(days=10)).isoformat()

    # Verify end date calculated
    expected_end_date = start_date + timedelta(days=10)
    assert result["end_date"] == expected_end_date.isoformat()


def test_apply_protocol_missing_patient_id(client, auth_headers, test_user, session):
    """Test applying protocol without patient_id"""
    protocol = Protocol(name="Test", created_by_id=test_user.id)
    session.add(protocol)
    session.commit()

    data = {"start_date": "2025-11-10"}  # Missing patient_id

    response = client.post(f"/api/protocols/{protocol.id}/apply", json=data, headers=auth_headers)
    assert response.status_code == 400
    assert "patient_id is required" in response.json["error"]


def test_apply_protocol_invalid_patient(client, auth_headers, test_user, session):
    """Test applying protocol to non-existent patient"""
    protocol = Protocol(name="Test", created_by_id=test_user.id)
    session.add(protocol)
    session.commit()

    data = {"patient_id": 99999, "start_date": "2025-11-10"}  # Non-existent patient

    response = client.post(f"/api/protocols/{protocol.id}/apply", json=data, headers=auth_headers)
    assert response.status_code == 404


# ============================================================================
# Treatment Plan Tests
# ============================================================================


def test_get_treatment_plans_empty(client, auth_headers):
    """Test getting treatment plans when none exist"""
    response = client.get("/api/treatment-plans", headers=auth_headers)
    assert response.status_code == 200
    assert response.json == []


def test_create_treatment_plan_basic(client, auth_headers, test_user, test_patient):
    """Test creating a basic treatment plan without steps"""
    data = {
        "name": "Basic Treatment Plan",
        "description": "Simple treatment",
        "patient_id": test_patient.id,
        "status": "draft",
        "start_date": "2025-11-10",
        "notes": "Test notes",
    }

    response = client.post("/api/treatment-plans", json=data, headers=auth_headers)
    assert response.status_code == 201

    result = response.json
    assert result["name"] == "Basic Treatment Plan"
    assert result["patient_id"] == test_patient.id
    assert result["status"] == "draft"
    assert result["created_by_id"] == test_user.id
    assert result["step_count"] == 0
    assert result["progress_percentage"] == 0


def test_create_treatment_plan_with_steps(client, auth_headers, test_patient):
    """Test creating a treatment plan with steps"""
    data = {
        "name": "Complete Treatment Plan",
        "description": "Treatment with multiple steps",
        "patient_id": test_patient.id,
        "status": "active",
        "start_date": "2025-11-10",
        "steps": [
            {
                "step_number": 1,
                "title": "Initial exam",
                "description": "Physical examination",
                "status": "pending",
                "scheduled_date": "2025-11-10",
                "estimated_cost": "100.00",
            },
            {
                "step_number": 2,
                "title": "Treatment",
                "description": "Main treatment procedure",
                "status": "pending",
                "scheduled_date": "2025-11-12",
                "estimated_cost": "300.00",
            },
        ],
    }

    response = client.post("/api/treatment-plans", json=data, headers=auth_headers)
    assert response.status_code == 201

    result = response.json
    assert result["step_count"] == 2
    assert float(result["total_estimated_cost"]) == 400.00
    assert len(result["steps"]) == 2


def test_create_treatment_plan_invalid_patient(client, auth_headers):
    """Test creating treatment plan with non-existent patient"""
    data = {"name": "Test Plan", "patient_id": 99999}  # Non-existent

    response = client.post("/api/treatment-plans", json=data, headers=auth_headers)
    assert response.status_code == 400


def test_get_treatment_plan_by_id(client, auth_headers, test_user, test_patient, session):
    """Test getting a single treatment plan by ID"""
    plan = TreatmentPlan(
        name="Test Treatment Plan",
        description="Test description",
        patient_id=test_patient.id,
        status="active",
        created_by_id=test_user.id,
    )
    session.add(plan)
    session.flush()

    # Add steps
    step1 = TreatmentPlanStep(
        treatment_plan_id=plan.id, step_number=1, title="Step 1", status="pending"
    )
    step2 = TreatmentPlanStep(
        treatment_plan_id=plan.id, step_number=2, title="Step 2", status="completed"
    )
    session.add_all([step1, step2])
    session.commit()

    response = client.get(f"/api/treatment-plans/{plan.id}", headers=auth_headers)
    assert response.status_code == 200

    result = response.json
    assert result["id"] == plan.id
    assert result["name"] == "Test Treatment Plan"
    assert result["step_count"] == 2
    assert result["progress_percentage"] == 50  # 1 of 2 completed


def test_get_treatment_plan_not_found(client, auth_headers):
    """Test getting non-existent treatment plan"""
    response = client.get("/api/treatment-plans/99999", headers=auth_headers)
    assert response.status_code == 404


def test_update_treatment_plan(client, auth_headers, test_user, test_patient, session):
    """Test updating a treatment plan"""
    plan = TreatmentPlan(
        name="Original Plan",
        description="Original description",
        patient_id=test_patient.id,
        status="draft",
        created_by_id=test_user.id,
    )
    session.add(plan)
    session.commit()

    # Update plan
    data = {
        "name": "Updated Plan",
        "description": "Updated description",
        "status": "active",
        "notes": "New notes",
    }

    response = client.put(f"/api/treatment-plans/{plan.id}", json=data, headers=auth_headers)
    assert response.status_code == 200

    result = response.json
    assert result["name"] == "Updated Plan"
    assert result["description"] == "Updated description"
    assert result["status"] == "active"


def test_update_treatment_plan_to_completed_sets_date(
    client, auth_headers, test_user, test_patient, session
):
    """Test that updating status to completed sets completed_date"""
    plan = TreatmentPlan(
        name="Test Plan", patient_id=test_patient.id, status="active", created_by_id=test_user.id
    )
    session.add(plan)
    session.commit()

    # Mark as completed
    data = {"status": "completed"}

    response = client.put(f"/api/treatment-plans/{plan.id}", json=data, headers=auth_headers)
    assert response.status_code == 200

    result = response.json
    assert result["status"] == "completed"
    assert result["completed_date"] is not None


def test_delete_treatment_plan(client, auth_headers, test_user, test_patient, session):
    """Test deleting a treatment plan"""
    plan = TreatmentPlan(name="Test Plan", patient_id=test_patient.id, created_by_id=test_user.id)
    session.add(plan)
    session.commit()
    plan_id = plan.id

    response = client.delete(f"/api/treatment-plans/{plan_id}", headers=auth_headers)
    assert response.status_code == 200

    # Verify deleted
    deleted_plan = session.query(TreatmentPlan).filter_by(id=plan_id).first()
    assert deleted_plan is None


def test_filter_treatment_plans_by_patient(client, auth_headers, test_user, session):
    """Test filtering treatment plans by patient_id"""
    # Create two patients
    client1 = Client(first_name="John", last_name="Doe", email="john@test.com", phone_primary="555-0001")
    client2 = Client(first_name="Jane", last_name="Smith", email="jane@test.com", phone_primary="555-0002")
    session.add_all([client1, client2])
    session.flush()

    patient1 = Patient(name="Fluffy", species="Cat", breed="Persian", owner_id=client1.id)
    patient2 = Patient(name="Mittens", species="Cat", breed="Siamese", owner_id=client2.id)
    session.add_all([patient1, patient2])
    session.flush()

    plan1 = TreatmentPlan(name="Plan 1", patient_id=patient1.id, created_by_id=test_user.id)
    plan2 = TreatmentPlan(name="Plan 2", patient_id=patient2.id, created_by_id=test_user.id)
    session.add_all([plan1, plan2])
    session.commit()

    # Filter by patient1
    response = client.get(f"/api/treatment-plans?patient_id={patient1.id}", headers=auth_headers)
    assert response.status_code == 200
    results = response.json
    assert len(results) == 1
    assert results[0]["name"] == "Plan 1"


def test_filter_treatment_plans_by_status(client, auth_headers, test_user, test_patient, session):
    """Test filtering treatment plans by status"""
    plan1 = TreatmentPlan(
        name="Draft Plan", patient_id=test_patient.id, status="draft", created_by_id=test_user.id
    )
    plan2 = TreatmentPlan(
        name="Active Plan", patient_id=test_patient.id, status="active", created_by_id=test_user.id
    )
    session.add_all([plan1, plan2])
    session.commit()

    # Filter by active
    response = client.get("/api/treatment-plans?status=active", headers=auth_headers)
    assert response.status_code == 200
    results = response.json
    assert len(results) == 1
    assert results[0]["name"] == "Active Plan"


def test_search_treatment_plans(client, auth_headers, test_user, test_patient, session):
    """Test searching treatment plans by name/description"""
    plan1 = TreatmentPlan(
        name="Dental Care",
        description="Teeth cleaning",
        patient_id=test_patient.id,
        created_by_id=test_user.id,
    )
    plan2 = TreatmentPlan(
        name="Surgery Plan",
        description="Surgical procedure",
        patient_id=test_patient.id,
        created_by_id=test_user.id,
    )
    session.add_all([plan1, plan2])
    session.commit()

    # Search for "dental"
    response = client.get("/api/treatment-plans?search=dental", headers=auth_headers)
    assert response.status_code == 200
    results = response.json
    assert len(results) == 1
    assert results[0]["name"] == "Dental Care"


# ============================================================================
# Treatment Plan Step Update Tests
# ============================================================================


def test_update_treatment_plan_step(client, auth_headers, test_user, test_patient, session):
    """Test updating a treatment plan step"""
    plan = TreatmentPlan(name="Test Plan", patient_id=test_patient.id, created_by_id=test_user.id)
    session.add(plan)
    session.flush()

    step = TreatmentPlanStep(
        treatment_plan_id=plan.id,
        step_number=1,
        title="Original Title",
        status="pending",
        estimated_cost=Decimal("100.00"),
    )
    session.add(step)
    session.commit()

    # Update step
    data = {"title": "Updated Title", "description": "New description", "notes": "Additional notes"}

    response = client.patch(
        f"/api/treatment-plans/{plan.id}/steps/{step.id}", json=data, headers=auth_headers
    )
    assert response.status_code == 200

    result = response.json
    assert result["title"] == "Updated Title"
    assert result["description"] == "New description"
    assert result["notes"] == "Additional notes"


def test_update_step_to_completed_sets_date(client, auth_headers, test_user, test_patient, session):
    """Test that marking step as completed sets completed_date and performed_by"""
    plan = TreatmentPlan(name="Test Plan", patient_id=test_patient.id, created_by_id=test_user.id)
    session.add(plan)
    session.flush()

    step = TreatmentPlanStep(
        treatment_plan_id=plan.id, step_number=1, title="Test Step", status="pending"
    )
    session.add(step)
    session.commit()

    # Mark as completed
    data = {"status": "completed"}

    response = client.patch(
        f"/api/treatment-plans/{plan.id}/steps/{step.id}", json=data, headers=auth_headers
    )
    assert response.status_code == 200

    result = response.json
    assert result["status"] == "completed"
    assert result["completed_date"] is not None
    assert result["performed_by_id"] == test_user.id


def test_update_step_actual_cost_recalculates_total(
    client, auth_headers, test_user, test_patient, session
):
    """Test that updating actual_cost recalculates treatment plan total"""
    plan = TreatmentPlan(
        name="Test Plan",
        patient_id=test_patient.id,
        total_actual_cost=Decimal("0"),
        created_by_id=test_user.id,
    )
    session.add(plan)
    session.flush()

    step1 = TreatmentPlanStep(
        treatment_plan_id=plan.id, step_number=1, title="Step 1", actual_cost=Decimal("100.00")
    )
    step2 = TreatmentPlanStep(
        treatment_plan_id=plan.id, step_number=2, title="Step 2", actual_cost=None
    )
    session.add_all([step1, step2])
    session.commit()

    # Update step2 actual cost
    data = {"actual_cost": "150.00"}

    response = client.patch(
        f"/api/treatment-plans/{plan.id}/steps/{step2.id}", json=data, headers=auth_headers
    )
    assert response.status_code == 200

    # Get updated treatment plan
    plan_response = client.get(f"/api/treatment-plans/{plan.id}", headers=auth_headers)
    result = plan_response.json

    # Total should be 100 + 150 = 250
    assert float(result["total_actual_cost"]) == 250.00


def test_update_step_wrong_plan(client, auth_headers, test_user, test_patient, session):
    """Test updating step that doesn't belong to specified treatment plan"""
    plan1 = TreatmentPlan(name="Plan 1", patient_id=test_patient.id, created_by_id=test_user.id)
    plan2 = TreatmentPlan(name="Plan 2", patient_id=test_patient.id, created_by_id=test_user.id)
    session.add_all([plan1, plan2])
    session.flush()

    step = TreatmentPlanStep(treatment_plan_id=plan1.id, step_number=1, title="Step 1")
    session.add(step)
    session.commit()

    # Try to update step via wrong plan
    data = {"title": "Updated"}

    response = client.patch(
        f"/api/treatment-plans/{plan2.id}/steps/{step.id}", json=data, headers=auth_headers
    )
    assert response.status_code == 400
    assert "does not belong" in response.json["error"]


def test_update_step_not_found(client, auth_headers, test_user, test_patient, session):
    """Test updating non-existent step"""
    plan = TreatmentPlan(name="Test Plan", patient_id=test_patient.id, created_by_id=test_user.id)
    session.add(plan)
    session.commit()

    data = {"title": "Updated"}

    response = client.patch(
        f"/api/treatment-plans/{plan.id}/steps/99999", json=data, headers=auth_headers
    )
    assert response.status_code == 404


# ============================================================================
# Progress Calculation Tests
# ============================================================================


def test_progress_calculation_no_steps(client, auth_headers, test_user, test_patient, session):
    """Test progress calculation with no steps"""
    plan = TreatmentPlan(name="Empty Plan", patient_id=test_patient.id, created_by_id=test_user.id)
    session.add(plan)
    session.commit()

    response = client.get(f"/api/treatment-plans/{plan.id}", headers=auth_headers)
    result = response.json

    assert result["progress_percentage"] == 0


def test_progress_calculation_partial_completion(
    client, auth_headers, test_user, test_patient, session
):
    """Test progress calculation with some steps completed"""
    plan = TreatmentPlan(name="Test Plan", patient_id=test_patient.id, created_by_id=test_user.id)
    session.add(plan)
    session.flush()

    steps = [
        TreatmentPlanStep(
            treatment_plan_id=plan.id, step_number=1, title="Step 1", status="completed"
        ),
        TreatmentPlanStep(
            treatment_plan_id=plan.id, step_number=2, title="Step 2", status="completed"
        ),
        TreatmentPlanStep(
            treatment_plan_id=plan.id, step_number=3, title="Step 3", status="pending"
        ),
        TreatmentPlanStep(
            treatment_plan_id=plan.id, step_number=4, title="Step 4", status="pending"
        ),
    ]
    session.add_all(steps)
    session.commit()

    response = client.get(f"/api/treatment-plans/{plan.id}", headers=auth_headers)
    result = response.json

    # 2 of 4 completed = 50%
    assert result["progress_percentage"] == 50


def test_progress_calculation_all_completed(client, auth_headers, test_user, test_patient, session):
    """Test progress calculation with all steps completed"""
    plan = TreatmentPlan(name="Test Plan", patient_id=test_patient.id, created_by_id=test_user.id)
    session.add(plan)
    session.flush()

    steps = [
        TreatmentPlanStep(
            treatment_plan_id=plan.id, step_number=1, title="Step 1", status="completed"
        ),
        TreatmentPlanStep(
            treatment_plan_id=plan.id, step_number=2, title="Step 2", status="completed"
        ),
    ]
    session.add_all(steps)
    session.commit()

    response = client.get(f"/api/treatment-plans/{plan.id}", headers=auth_headers)
    result = response.json

    assert result["progress_percentage"] == 100


# ============================================================================
# Authentication Tests
# ============================================================================


def test_protocols_require_authentication(client):
    """Test that protocol endpoints require authentication"""
    response = client.get("/api/protocols")
    assert response.status_code == 401


def test_treatment_plans_require_authentication(client):
    """Test that treatment plan endpoints require authentication"""
    response = client.get("/api/treatment-plans")
    assert response.status_code == 401
