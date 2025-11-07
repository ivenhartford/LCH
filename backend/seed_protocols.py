"""
Seed script for Treatment Plans & Protocols (Phase 4.2)

This script creates sample protocols and treatment plans to demonstrate
the Phase 4.2 features.

Usage:
    python seed_protocols.py
"""

import sys
from datetime import datetime, timedelta
from decimal import Decimal

from app import create_app, db
from app.models import (
    Protocol,
    ProtocolStep,
    TreatmentPlan,
    TreatmentPlanStep,
    User,
    Patient,
    Client,
)


def seed_protocols():
    """Create sample protocols"""

    print("Creating sample protocols...")

    # Get first user for created_by
    user = User.query.first()
    if not user:
        print("Error: No users found. Please create a user first.")
        return

    protocols_data = [
        {
            "name": "Routine Dental Cleaning",
            "description": "Standard dental prophylaxis procedure for cats",
            "category": "dental",
            "is_active": True,
            "default_duration_days": 3,
            "estimated_cost": Decimal("350.00"),
            "notes": "Pre-anesthetic bloodwork required",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Pre-operative examination",
                    "description": "Physical exam and pre-anesthetic bloodwork",
                    "day_offset": 0,
                    "estimated_cost": Decimal("75.00"),
                },
                {
                    "step_number": 2,
                    "title": "Dental cleaning procedure",
                    "description": "Anesthesia, scaling, polishing, and fluoride treatment",
                    "day_offset": 1,
                    "estimated_cost": Decimal("250.00"),
                },
                {
                    "step_number": 3,
                    "title": "Post-operative check",
                    "description": "Follow-up examination 2 days after procedure",
                    "day_offset": 3,
                    "estimated_cost": Decimal("25.00"),
                },
            ],
        },
        {
            "name": "Spay Surgery Protocol",
            "description": "Ovariohysterectomy (spay) procedure for female cats",
            "category": "surgical",
            "is_active": True,
            "default_duration_days": 10,
            "estimated_cost": Decimal("450.00"),
            "notes": "Includes 10-day post-op recovery monitoring",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Pre-surgical consultation",
                    "description": "Physical exam, bloodwork, and surgical consent",
                    "day_offset": 0,
                    "estimated_cost": Decimal("85.00"),
                },
                {
                    "step_number": 2,
                    "title": "Spay surgery",
                    "description": "Ovariohysterectomy procedure under general anesthesia",
                    "day_offset": 1,
                    "estimated_cost": Decimal("325.00"),
                },
                {
                    "step_number": 3,
                    "title": "Day 3 post-op check",
                    "description": "Incision check and pain assessment",
                    "day_offset": 3,
                    "estimated_cost": Decimal("0.00"),
                    "notes": "Included in surgical package",
                },
                {
                    "step_number": 4,
                    "title": "Suture removal",
                    "description": "Remove sutures and final examination",
                    "day_offset": 10,
                    "estimated_cost": Decimal("40.00"),
                },
            ],
        },
        {
            "name": "Diabetes Management Protocol",
            "description": "Initial stabilization protocol for newly diagnosed diabetic cats",
            "category": "chronic_care",
            "is_active": True,
            "default_duration_days": 14,
            "estimated_cost": Decimal("650.00"),
            "notes": "Requires owner commitment for home glucose monitoring",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Initial diagnostic workup",
                    "description": "Complete blood panel, urinalysis, and fructosamine test",
                    "day_offset": 0,
                    "estimated_cost": Decimal("200.00"),
                },
                {
                    "step_number": 2,
                    "title": "Insulin therapy initiation",
                    "description": "Start insulin, owner training on injection technique",
                    "day_offset": 1,
                    "estimated_cost": Decimal("150.00"),
                },
                {
                    "step_number": 3,
                    "title": "Glucose curve - Day 3",
                    "description": "8-hour glucose monitoring to assess insulin response",
                    "day_offset": 3,
                    "estimated_cost": Decimal("120.00"),
                },
                {
                    "step_number": 4,
                    "title": "Recheck and adjustment",
                    "description": "Review home monitoring logs, adjust insulin dose if needed",
                    "day_offset": 7,
                    "estimated_cost": Decimal("80.00"),
                },
                {
                    "step_number": 5,
                    "title": "Follow-up glucose curve",
                    "description": "Confirm stabilization with second glucose curve",
                    "day_offset": 14,
                    "estimated_cost": Decimal("100.00"),
                },
            ],
        },
        {
            "name": "Wellness Exam Package",
            "description": "Annual wellness examination with preventive care",
            "category": "wellness",
            "is_active": True,
            "default_duration_days": 1,
            "estimated_cost": Decimal("180.00"),
            "notes": "Recommended annually for adult cats, biannually for seniors",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Physical examination",
                    "description": "Complete nose-to-tail physical exam",
                    "day_offset": 0,
                    "estimated_cost": Decimal("65.00"),
                },
                {
                    "step_number": 2,
                    "title": "Vaccinations",
                    "description": "Core vaccines (FVRCP) and rabies as needed",
                    "day_offset": 0,
                    "estimated_cost": Decimal("55.00"),
                },
                {
                    "step_number": 3,
                    "title": "Parasite prevention",
                    "description": "Flea/tick prevention and deworming",
                    "day_offset": 0,
                    "estimated_cost": Decimal("40.00"),
                },
                {
                    "step_number": 4,
                    "title": "Fecal test",
                    "description": "Fecal examination for intestinal parasites",
                    "day_offset": 0,
                    "estimated_cost": Decimal("20.00"),
                },
            ],
        },
        {
            "name": "Post-Surgery Pain Management",
            "description": "Multi-modal pain management protocol for post-operative patients",
            "category": "surgical",
            "is_active": True,
            "default_duration_days": 5,
            "estimated_cost": Decimal("120.00"),
            "notes": "Adjust medications based on pain assessment scores",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Day 0-1: Intensive pain control",
                    "description": "Injectable opioid + NSAID combination",
                    "day_offset": 0,
                    "estimated_cost": Decimal("60.00"),
                },
                {
                    "step_number": 2,
                    "title": "Day 2-3: Transition to oral medications",
                    "description": "Switch to oral pain medications, assess comfort level",
                    "day_offset": 2,
                    "estimated_cost": Decimal("35.00"),
                },
                {
                    "step_number": 3,
                    "title": "Day 4-5: Pain assessment and taper",
                    "description": "Evaluate for continued need, begin tapering if appropriate",
                    "day_offset": 4,
                    "estimated_cost": Decimal("25.00"),
                },
            ],
        },
    ]

    created_protocols = []
    for protocol_data in protocols_data:
        # Check if protocol already exists
        existing = Protocol.query.filter_by(name=protocol_data["name"]).first()
        if existing:
            print(f"  Protocol '{protocol_data['name']}' already exists, skipping...")
            created_protocols.append(existing)
            continue

        steps_data = protocol_data.pop("steps")

        protocol = Protocol(**protocol_data, created_by_id=user.id)

        db.session.add(protocol)
        db.session.flush()  # Get protocol ID

        # Add protocol steps
        for step_data in steps_data:
            step = ProtocolStep(protocol_id=protocol.id, **step_data)
            db.session.add(step)

        created_protocols.append(protocol)
        print(f"  ✓ Created protocol: {protocol.name} ({len(steps_data)} steps)")

    db.session.commit()
    print(f"\n{len(created_protocols)} protocols created successfully!")

    return created_protocols


def seed_treatment_plans():
    """Create sample treatment plans"""

    print("\nCreating sample treatment plans...")

    # Get first user for created_by
    user = User.query.first()

    # Get a few patients to demonstrate
    patients = Patient.query.limit(3).all()
    if not patients:
        print("Error: No patients found. Please create patients first.")
        return

    # Get some protocols
    protocols = Protocol.query.limit(2).all()
    if not protocols:
        print("Error: No protocols found. Run seed_protocols() first.")
        return

    treatment_plans_data = [
        {
            "patient": patients[0],
            "protocol": protocols[0] if len(protocols) > 0 else None,
            "name": f"{protocols[0].name if len(protocols) > 0 else 'Custom'} - {patients[0].name}",
            "description": "Treatment plan created from protocol",
            "status": "active",
            "start_date": datetime.now().date(),
        },
    ]

    if len(patients) > 1 and len(protocols) > 1:
        treatment_plans_data.append(
            {
                "patient": patients[1],
                "protocol": protocols[1],
                "name": f"{protocols[1].name} - {patients[1].name}",
                "description": "Scheduled treatment plan",
                "status": "draft",
                "start_date": datetime.now().date() + timedelta(days=7),
            }
        )

    if len(patients) > 2:
        # Custom treatment plan (not from protocol)
        treatment_plans_data.append(
            {
                "patient": patients[2],
                "protocol": None,
                "name": f"Custom Treatment Plan - {patients[2].name}",
                "description": "Custom multi-step treatment plan",
                "status": "active",
                "start_date": datetime.now().date() - timedelta(days=5),
                "custom_steps": [
                    {
                        "step_number": 1,
                        "title": "Initial blood work",
                        "description": "Complete blood panel to assess organ function",
                        "status": "completed",
                        "scheduled_date": datetime.now().date() - timedelta(days=5),
                        "completed_date": datetime.now().date() - timedelta(days=5),
                        "estimated_cost": Decimal("120.00"),
                        "actual_cost": Decimal("120.00"),
                    },
                    {
                        "step_number": 2,
                        "title": "Start medication",
                        "description": "Begin antibiotic therapy - 10 day course",
                        "status": "in_progress",
                        "scheduled_date": datetime.now().date() - timedelta(days=4),
                        "estimated_cost": Decimal("45.00"),
                        "actual_cost": Decimal("45.00"),
                    },
                    {
                        "step_number": 3,
                        "title": "Mid-treatment recheck",
                        "description": "Assess response to therapy",
                        "status": "pending",
                        "scheduled_date": datetime.now().date() + timedelta(days=3),
                        "estimated_cost": Decimal("60.00"),
                    },
                    {
                        "step_number": 4,
                        "title": "Final recheck",
                        "description": "Confirm resolution, repeat bloodwork if needed",
                        "status": "pending",
                        "scheduled_date": datetime.now().date() + timedelta(days=10),
                        "estimated_cost": Decimal("80.00"),
                    },
                ],
            }
        )

    created_plans = []
    for plan_data in treatment_plans_data:
        patient = plan_data.pop("patient")
        protocol = plan_data.pop("protocol", None)
        custom_steps = plan_data.pop("custom_steps", None)

        # Check if treatment plan already exists
        existing = TreatmentPlan.query.filter_by(
            name=plan_data["name"], patient_id=patient.id
        ).first()
        if existing:
            print(f"  Treatment plan '{plan_data['name']}' already exists, skipping...")
            created_plans.append(existing)
            continue

        treatment_plan = TreatmentPlan(
            **plan_data,
            patient_id=patient.id,
            protocol_id=protocol.id if protocol else None,
            created_by_id=user.id,
        )

        db.session.add(treatment_plan)
        db.session.flush()  # Get treatment plan ID

        # If from protocol, copy protocol steps
        if protocol:
            protocol_steps = protocol.steps.order_by(ProtocolStep.step_number).all()
            for proto_step in protocol_steps:
                step = TreatmentPlanStep(
                    treatment_plan_id=treatment_plan.id,
                    step_number=proto_step.step_number,
                    title=proto_step.title,
                    description=proto_step.description,
                    status="pending",
                    estimated_cost=proto_step.estimated_cost,
                    notes=proto_step.notes,
                )

                # Calculate scheduled date
                if treatment_plan.start_date:
                    step.scheduled_date = treatment_plan.start_date + timedelta(
                        days=proto_step.day_offset
                    )

                db.session.add(step)

            treatment_plan.total_estimated_cost = protocol.estimated_cost

            # Calculate end date
            if treatment_plan.start_date and protocol.default_duration_days:
                treatment_plan.end_date = treatment_plan.start_date + timedelta(
                    days=protocol.default_duration_days
                )

        # If custom steps provided
        elif custom_steps:
            total_estimated = Decimal("0")
            total_actual = Decimal("0")

            for step_data in custom_steps:
                step = TreatmentPlanStep(treatment_plan_id=treatment_plan.id, **step_data)
                db.session.add(step)

                if step.estimated_cost:
                    total_estimated += step.estimated_cost
                if step.actual_cost:
                    total_actual += step.actual_cost

            treatment_plan.total_estimated_cost = total_estimated
            treatment_plan.total_actual_cost = total_actual

        created_plans.append(treatment_plan)
        print(
            f"  ✓ Created treatment plan: {treatment_plan.name} (Status: {treatment_plan.status})"
        )

    db.session.commit()
    print(f"\n{len(created_plans)} treatment plans created successfully!")

    return created_plans


def main():
    """Main seed function"""
    app = create_app()

    with app.app_context():
        print("=" * 70)
        print("Phase 4.2: Treatment Plans & Protocols - Seed Data Script")
        print("=" * 70)
        print()

        try:
            # Seed protocols
            protocols = seed_protocols()

            # Seed treatment plans
            treatment_plans = seed_treatment_plans()

            print("\n" + "=" * 70)
            print("✓ Seed data created successfully!")
            print("=" * 70)
            print(f"\nSummary:")
            print(f"  - Protocols: {len(protocols)}")
            print(f"  - Treatment Plans: {len(treatment_plans)}")
            print()
            print("You can now:")
            print("  1. View protocols: GET /api/protocols")
            print("  2. View treatment plans: GET /api/treatment-plans")
            print("  3. Apply a protocol to a patient: POST /api/protocols/<id>/apply")
            print()

        except Exception as e:
            print(f"\n✗ Error creating seed data: {str(e)}")
            import traceback

            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
