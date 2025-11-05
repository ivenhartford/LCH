"""
Database Performance Optimization Migration

This script adds database indexes to improve query performance.
Run this after all Phase 1-4 migrations.

To apply:
  flask db upgrade

Indexes added for:
- Frequently queried fields
- Foreign keys
- Date/timestamp fields used in filters
- Status fields used in WHERE clauses
"""

from alembic import op


def upgrade():
    """Add performance indexes"""

    # Client indexes
    op.create_index("idx_client_email", "client", ["email"])
    op.create_index("idx_client_phone", "client", ["phone_primary"])
    op.create_index("idx_client_created_at", "client", ["created_at"])
    op.create_index("idx_client_active", "client", ["is_active"])

    # Patient indexes
    op.create_index("idx_patient_owner", "patient", ["owner_id"])
    op.create_index("idx_patient_status", "patient", ["status"])
    op.create_index("idx_patient_created_at", "patient", ["created_at"])
    op.create_index("idx_patient_breed", "patient", ["breed"])

    # Appointment indexes
    op.create_index("idx_appointment_patient", "appointment", ["patient_id"])
    op.create_index("idx_appointment_client", "appointment", ["client_id"])
    op.create_index("idx_appointment_date", "appointment", ["appointment_date"])
    op.create_index("idx_appointment_status", "appointment", ["status"])
    op.create_index("idx_appointment_type", "appointment", ["appointment_type_id"])
    op.create_index("idx_appointment_assigned", "appointment", ["assigned_to_id"])

    # Visit indexes
    op.create_index("idx_visit_patient", "visit", ["patient_id"])
    op.create_index("idx_visit_date", "visit", ["visit_date"])
    op.create_index("idx_visit_status", "visit", ["status"])

    # Invoice indexes
    op.create_index("idx_invoice_client", "invoice", ["client_id"])
    op.create_index("idx_invoice_patient", "invoice", ["patient_id"])
    op.create_index("idx_invoice_date", "invoice", ["invoice_date"])
    op.create_index("idx_invoice_status", "invoice", ["status"])

    # InvoiceItem indexes
    op.create_index("idx_invoice_item_invoice", "invoice_item", ["invoice_id"])
    op.create_index("idx_invoice_item_service", "invoice_item", ["service_id"])

    # Payment indexes
    op.create_index("idx_payment_invoice", "payment", ["invoice_id"])
    op.create_index("idx_payment_date", "payment", ["payment_date"])

    # Vaccination indexes
    op.create_index("idx_vaccination_patient", "vaccination", ["patient_id"])
    op.create_index("idx_vaccination_date", "vaccination", ["administered_date"])
    op.create_index("idx_vaccination_next_due", "vaccination", ["next_due_date"])

    # Prescription indexes
    op.create_index("idx_prescription_patient", "prescription", ["patient_id"])
    op.create_index("idx_prescription_medication", "prescription", ["medication_id"])
    op.create_index("idx_prescription_status", "prescription", ["status"])

    # Medication indexes
    op.create_index("idx_medication_active", "medication", ["is_active"])
    op.create_index("idx_medication_drug_class", "medication", ["drug_class"])

    # Product indexes (inventory)
    op.create_index("idx_product_vendor", "product", ["vendor_id"])
    op.create_index("idx_product_active", "product", ["is_active"])
    op.create_index("idx_product_category", "product", ["category"])

    # PurchaseOrder indexes
    op.create_index("idx_purchase_order_vendor", "purchase_order", ["vendor_id"])
    op.create_index("idx_purchase_order_status", "purchase_order", ["status"])
    op.create_index("idx_purchase_order_date", "purchase_order", ["order_date"])

    # Staff indexes
    op.create_index("idx_staff_user", "staff", ["user_id"])
    op.create_index("idx_staff_active", "staff", ["is_active"])

    # LabResult indexes
    op.create_index("idx_lab_result_patient", "lab_result", ["patient_id"])
    op.create_index("idx_lab_result_test", "lab_result", ["lab_test_id"])
    op.create_index("idx_lab_result_date", "lab_result", ["result_date"])
    op.create_index("idx_lab_result_status", "lab_result", ["status"])

    # Reminder indexes
    op.create_index("idx_reminder_client", "reminder", ["client_id"])
    op.create_index("idx_reminder_patient", "reminder", ["patient_id"])
    op.create_index("idx_reminder_date", "reminder", ["reminder_date"])
    op.create_index("idx_reminder_status", "reminder", ["status"])

    # Document indexes
    op.create_index("idx_document_entity", "document", ["linked_entity_type", "linked_entity_id"])
    op.create_index("idx_document_uploaded", "document", ["uploaded_at"])
    op.create_index("idx_document_category", "document", ["category"])

    # Protocol indexes
    op.create_index("idx_protocol_category", "protocol", ["category"])
    op.create_index("idx_protocol_active", "protocol", ["is_active"])
    op.create_index("idx_protocol_created_by", "protocol", ["created_by_id"])

    # ProtocolStep indexes
    op.create_index("idx_protocol_step_protocol", "protocol_step", ["protocol_id"])

    # TreatmentPlan indexes
    op.create_index("idx_treatment_plan_patient", "treatment_plan", ["patient_id"])
    op.create_index("idx_treatment_plan_protocol", "treatment_plan", ["protocol_id"])
    op.create_index("idx_treatment_plan_status", "treatment_plan", ["status"])
    op.create_index("idx_treatment_plan_start_date", "treatment_plan", ["start_date"])

    # TreatmentPlanStep indexes
    op.create_index("idx_treatment_plan_step_plan", "treatment_plan_step", ["treatment_plan_id"])
    op.create_index("idx_treatment_plan_step_status", "treatment_plan_step", ["status"])

    # AppointmentRequest indexes (client portal)
    op.create_index("idx_appointment_request_client", "appointment_request", ["client_id"])
    op.create_index("idx_appointment_request_status", "appointment_request", ["status"])
    op.create_index("idx_appointment_request_date", "appointment_request", ["requested_date"])


def downgrade():
    """Remove performance indexes"""

    # Client indexes
    op.drop_index("idx_client_email", "client")
    op.drop_index("idx_client_phone", "client")
    op.drop_index("idx_client_created_at", "client")
    op.drop_index("idx_client_active", "client")

    # Patient indexes
    op.drop_index("idx_patient_owner", "patient")
    op.drop_index("idx_patient_status", "patient")
    op.drop_index("idx_patient_created_at", "patient")
    op.drop_index("idx_patient_breed", "patient")

    # Appointment indexes
    op.drop_index("idx_appointment_patient", "appointment")
    op.drop_index("idx_appointment_client", "appointment")
    op.drop_index("idx_appointment_date", "appointment")
    op.drop_index("idx_appointment_status", "appointment")
    op.drop_index("idx_appointment_type", "appointment")
    op.drop_index("idx_appointment_assigned", "appointment")

    # Visit indexes
    op.drop_index("idx_visit_patient", "visit")
    op.drop_index("idx_visit_date", "visit")
    op.drop_index("idx_visit_status", "visit")

    # Invoice indexes
    op.drop_index("idx_invoice_client", "invoice")
    op.drop_index("idx_invoice_patient", "invoice")
    op.drop_index("idx_invoice_date", "invoice")
    op.drop_index("idx_invoice_status", "invoice")

    # InvoiceItem indexes
    op.drop_index("idx_invoice_item_invoice", "invoice_item")
    op.drop_index("idx_invoice_item_service", "invoice_item")

    # Payment indexes
    op.drop_index("idx_payment_invoice", "payment")
    op.drop_index("idx_payment_date", "payment")

    # Vaccination indexes
    op.drop_index("idx_vaccination_patient", "vaccination")
    op.drop_index("idx_vaccination_date", "vaccination")
    op.drop_index("idx_vaccination_next_due", "vaccination")

    # Prescription indexes
    op.drop_index("idx_prescription_patient", "prescription")
    op.drop_index("idx_prescription_medication", "prescription")
    op.drop_index("idx_prescription_status", "prescription")

    # Medication indexes
    op.drop_index("idx_medication_active", "medication")
    op.drop_index("idx_medication_drug_class", "medication")

    # Product indexes
    op.drop_index("idx_product_vendor", "product")
    op.drop_index("idx_product_active", "product")
    op.drop_index("idx_product_category", "product")

    # PurchaseOrder indexes
    op.drop_index("idx_purchase_order_vendor", "purchase_order")
    op.drop_index("idx_purchase_order_status", "purchase_order")
    op.drop_index("idx_purchase_order_date", "purchase_order")

    # Staff indexes
    op.drop_index("idx_staff_user", "staff")
    op.drop_index("idx_staff_active", "staff")

    # LabResult indexes
    op.drop_index("idx_lab_result_patient", "lab_result")
    op.drop_index("idx_lab_result_test", "lab_result")
    op.drop_index("idx_lab_result_date", "lab_result")
    op.drop_index("idx_lab_result_status", "lab_result")

    # Reminder indexes
    op.drop_index("idx_reminder_client", "reminder")
    op.drop_index("idx_reminder_patient", "reminder")
    op.drop_index("idx_reminder_date", "reminder")
    op.drop_index("idx_reminder_status", "reminder")

    # Document indexes
    op.drop_index("idx_document_entity", "document")
    op.drop_index("idx_document_uploaded", "document")
    op.drop_index("idx_document_category", "document")

    # Protocol indexes
    op.drop_index("idx_protocol_category", "protocol")
    op.drop_index("idx_protocol_active", "protocol")
    op.drop_index("idx_protocol_created_by", "protocol")

    # ProtocolStep indexes
    op.drop_index("idx_protocol_step_protocol", "protocol_step")

    # TreatmentPlan indexes
    op.drop_index("idx_treatment_plan_patient", "treatment_plan")
    op.drop_index("idx_treatment_plan_protocol", "treatment_plan")
    op.drop_index("idx_treatment_plan_status", "treatment_plan")
    op.drop_index("idx_treatment_plan_start_date", "treatment_plan")

    # TreatmentPlanStep indexes
    op.drop_index("idx_treatment_plan_step_plan", "treatment_plan_step")
    op.drop_index("idx_treatment_plan_step_status", "treatment_plan_step")

    # AppointmentRequest indexes
    op.drop_index("idx_appointment_request_client", "appointment_request")
    op.drop_index("idx_appointment_request_status", "appointment_request")
    op.drop_index("idx_appointment_request_date", "appointment_request")
