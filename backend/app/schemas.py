"""
Marshmallow schemas for API request/response validation and serialization
"""

from datetime import datetime
from marshmallow import Schema, fields, validate


class ClientSchema(Schema):
    """Schema for Client model validation and serialization"""

    id = fields.Int(dump_only=True)

    # Personal Info
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(allow_none=True, validate=validate.Length(max=120))
    phone_primary = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    phone_secondary = fields.Str(allow_none=True, validate=validate.Length(max=20))

    # Address
    address_line1 = fields.Str(allow_none=True, validate=validate.Length(max=200))
    address_line2 = fields.Str(allow_none=True, validate=validate.Length(max=200))
    city = fields.Str(allow_none=True, validate=validate.Length(max=100))
    state = fields.Str(allow_none=True, validate=validate.Length(max=50))
    zip_code = fields.Str(allow_none=True, validate=validate.Length(max=20))

    # Communication Preferences
    preferred_contact = fields.Str(
        allow_none=True, validate=validate.OneOf(["email", "phone", "sms"]), load_default="email"
    )
    email_reminders = fields.Bool(load_default=True)
    sms_reminders = fields.Bool(load_default=True)

    # Account
    account_balance = fields.Decimal(as_string=True, allow_none=True)
    credit_limit = fields.Decimal(as_string=True, allow_none=True)

    # Notes and Alerts
    notes = fields.Str(allow_none=True)
    alerts = fields.Str(allow_none=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    is_active = fields.Bool(load_default=True)


class ClientUpdateSchema(Schema):
    """Schema for updating existing client (all fields optional)"""

    # Personal Info
    first_name = fields.Str(validate=validate.Length(min=1, max=100))
    last_name = fields.Str(validate=validate.Length(min=1, max=100))
    email = fields.Email(allow_none=True, validate=validate.Length(max=120))
    phone_primary = fields.Str(validate=validate.Length(min=1, max=20))
    phone_secondary = fields.Str(allow_none=True, validate=validate.Length(max=20))

    # Address
    address_line1 = fields.Str(allow_none=True, validate=validate.Length(max=200))
    address_line2 = fields.Str(allow_none=True, validate=validate.Length(max=200))
    city = fields.Str(allow_none=True, validate=validate.Length(max=100))
    state = fields.Str(allow_none=True, validate=validate.Length(max=50))
    zip_code = fields.Str(allow_none=True, validate=validate.Length(max=20))

    # Communication Preferences
    preferred_contact = fields.Str(allow_none=True, validate=validate.OneOf(["email", "phone", "sms"]))
    email_reminders = fields.Bool()
    sms_reminders = fields.Bool()

    # Account
    account_balance = fields.Decimal(as_string=True, allow_none=True)
    credit_limit = fields.Decimal(as_string=True, allow_none=True)

    # Notes and Alerts
    notes = fields.Str(allow_none=True)
    alerts = fields.Str(allow_none=True)

    # Status
    is_active = fields.Bool()


class PatientSchema(Schema):
    """Schema for Patient (Cat) model validation and serialization"""

    id = fields.Int(dump_only=True)

    # Basic Info
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    species = fields.Str(load_default="Cat", validate=validate.Length(max=50))
    breed = fields.Str(allow_none=True, validate=validate.Length(max=100))
    color = fields.Str(allow_none=True, validate=validate.Length(max=100))
    markings = fields.Str(allow_none=True)

    # Physical Characteristics
    sex = fields.Str(allow_none=True, validate=validate.OneOf(["Male", "Female"]))
    reproductive_status = fields.Str(allow_none=True, validate=validate.OneOf(["Intact", "Spayed", "Neutered"]))
    date_of_birth = fields.Date(allow_none=True)
    approximate_age = fields.Str(allow_none=True, validate=validate.Length(max=50))
    weight_kg = fields.Decimal(as_string=True, allow_none=True, places=2)

    # Identification
    microchip_number = fields.Str(allow_none=True, validate=validate.Length(max=50))

    # Insurance
    insurance_company = fields.Str(allow_none=True, validate=validate.Length(max=100))
    insurance_policy_number = fields.Str(allow_none=True, validate=validate.Length(max=100))

    # Owner/Client Link
    owner_id = fields.Int(required=True)
    owner_name = fields.Str(dump_only=True)  # For display purposes

    # Photo
    photo_url = fields.Str(allow_none=True, validate=validate.Length(max=500))

    # Medical Info
    allergies = fields.Str(allow_none=True)
    medical_notes = fields.Str(allow_none=True)
    behavioral_notes = fields.Str(allow_none=True)

    # Status
    status = fields.Str(load_default="Active", validate=validate.OneOf(["Active", "Inactive", "Deceased"]))
    deceased_date = fields.Date(allow_none=True)

    # Calculated field
    age_display = fields.Str(dump_only=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class PatientUpdateSchema(Schema):
    """Schema for updating existing patient (all fields optional)"""

    # Basic Info
    name = fields.Str(validate=validate.Length(min=1, max=100))
    species = fields.Str(validate=validate.Length(max=50))
    breed = fields.Str(allow_none=True, validate=validate.Length(max=100))
    color = fields.Str(allow_none=True, validate=validate.Length(max=100))
    markings = fields.Str(allow_none=True)

    # Physical Characteristics
    sex = fields.Str(allow_none=True, validate=validate.OneOf(["Male", "Female"]))
    reproductive_status = fields.Str(allow_none=True, validate=validate.OneOf(["Intact", "Spayed", "Neutered"]))
    date_of_birth = fields.Date(allow_none=True)
    approximate_age = fields.Str(allow_none=True, validate=validate.Length(max=50))
    weight_kg = fields.Decimal(as_string=True, allow_none=True, places=2)

    # Identification
    microchip_number = fields.Str(allow_none=True, validate=validate.Length(max=50))

    # Insurance
    insurance_company = fields.Str(allow_none=True, validate=validate.Length(max=100))
    insurance_policy_number = fields.Str(allow_none=True, validate=validate.Length(max=100))

    # Owner/Client Link
    owner_id = fields.Int()

    # Photo
    photo_url = fields.Str(allow_none=True, validate=validate.Length(max=500))

    # Medical Info
    allergies = fields.Str(allow_none=True)
    medical_notes = fields.Str(allow_none=True)
    behavioral_notes = fields.Str(allow_none=True)

    # Status
    status = fields.Str(validate=validate.OneOf(["Active", "Inactive", "Deceased"]))
    deceased_date = fields.Date(allow_none=True)


class VisitSchema(Schema):
    """Schema for Visit model validation and serialization"""

    id = fields.Int(dump_only=True)

    # Basic Info
    visit_date = fields.DateTime(load_default=lambda: datetime.utcnow())
    visit_type = fields.Str(
        required=True,
        validate=validate.OneOf(["Wellness", "Sick", "Emergency", "Follow-up", "Surgery", "Dental", "Other"]),
    )
    status = fields.Str(
        load_default="scheduled",
        validate=validate.OneOf(["scheduled", "in_progress", "completed", "cancelled"]),
    )

    # Links
    patient_id = fields.Int(required=True)
    patient_name = fields.Str(dump_only=True)
    veterinarian_id = fields.Int(allow_none=True)
    veterinarian_name = fields.Str(dump_only=True)
    appointment_id = fields.Int(allow_none=True)

    # Details
    chief_complaint = fields.Str(allow_none=True)
    visit_notes = fields.Str(allow_none=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    completed_at = fields.DateTime(allow_none=True)


class VitalSignsSchema(Schema):
    """Schema for Vital Signs validation and serialization"""

    id = fields.Int(dump_only=True)
    visit_id = fields.Int(required=True)

    # Vital Signs
    temperature_c = fields.Decimal(as_string=True, allow_none=True, places=1)
    weight_kg = fields.Decimal(as_string=True, allow_none=True, places=2)
    heart_rate = fields.Int(allow_none=True)
    respiratory_rate = fields.Int(allow_none=True)
    blood_pressure_systolic = fields.Int(allow_none=True)
    blood_pressure_diastolic = fields.Int(allow_none=True)
    capillary_refill_time = fields.Str(allow_none=True, validate=validate.Length(max=20))
    mucous_membrane_color = fields.Str(allow_none=True, validate=validate.Length(max=50))
    body_condition_score = fields.Int(allow_none=True, validate=validate.Range(min=1, max=9))  # 1-9 scale

    # Additional Info
    pain_score = fields.Int(allow_none=True, validate=validate.Range(min=0, max=10))  # 0-10 scale
    notes = fields.Str(allow_none=True)

    # Metadata
    recorded_at = fields.DateTime(load_default=lambda: datetime.utcnow())
    recorded_by_id = fields.Int(dump_only=True)  # Auto-populated from current_user
    recorded_by_name = fields.Method("get_recorded_by_name")

    def get_recorded_by_name(self, obj):
        """Get the name of the user who recorded the vital signs"""
        return obj.recorded_by.username if obj.recorded_by else None


class SOAPNoteSchema(Schema):
    """Schema for SOAP Note validation and serialization"""

    id = fields.Int(dump_only=True)
    visit_id = fields.Int(required=True)

    # SOAP Components
    subjective = fields.Str(allow_none=True)
    objective = fields.Str(allow_none=True)
    assessment = fields.Str(allow_none=True)
    plan = fields.Str(allow_none=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    created_by_id = fields.Int(dump_only=True)  # Auto-populated from current_user
    created_by_name = fields.Str(dump_only=True)


class DiagnosisSchema(Schema):
    """Schema for Diagnosis validation and serialization"""

    id = fields.Int(dump_only=True)
    visit_id = fields.Int(required=True)

    # Diagnosis Info
    diagnosis_name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    icd_code = fields.Str(allow_none=True, validate=validate.Length(max=20))
    diagnosis_type = fields.Str(
        load_default="primary", validate=validate.OneOf(["primary", "differential", "rule-out"])
    )
    severity = fields.Str(allow_none=True, validate=validate.OneOf(["mild", "moderate", "severe"]))
    status = fields.Str(
        load_default="active",
        validate=validate.OneOf(["active", "resolved", "chronic", "ruled-out"]),
    )

    # Additional Details
    notes = fields.Str(allow_none=True)
    onset_date = fields.Date(allow_none=True)
    resolution_date = fields.Date(allow_none=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)
    created_by_id = fields.Int(dump_only=True)  # Auto-populated from current_user
    created_by_name = fields.Str(dump_only=True)


class VaccinationSchema(Schema):
    """Schema for Vaccination validation and serialization"""

    id = fields.Int(dump_only=True)

    # Links
    patient_id = fields.Int(required=True)
    patient_name = fields.Str(dump_only=True)
    visit_id = fields.Int(allow_none=True)

    # Vaccine Info
    vaccine_name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    vaccine_type = fields.Str(allow_none=True, validate=validate.OneOf(["Core", "Non-core", "Lifestyle-dependent"]))
    manufacturer = fields.Str(allow_none=True, validate=validate.Length(max=100))
    lot_number = fields.Str(allow_none=True, validate=validate.Length(max=100))
    serial_number = fields.Str(allow_none=True, validate=validate.Length(max=100))

    # Administration Details
    administration_date = fields.Date(required=True)
    expiration_date = fields.Date(allow_none=True)
    next_due_date = fields.Date(allow_none=True)
    dosage = fields.Str(allow_none=True, validate=validate.Length(max=50))
    route = fields.Str(allow_none=True, validate=validate.OneOf(["SC", "IM", "IV", "PO", "Intranasal", "Other"]))
    administration_site = fields.Str(allow_none=True, validate=validate.Length(max=100))

    # Status
    status = fields.Str(
        load_default="current",
        validate=validate.OneOf(["current", "overdue", "not_due", "declined"]),
    )

    # Notes
    notes = fields.Str(allow_none=True)
    adverse_reactions = fields.Str(allow_none=True)

    # Metadata
    administered_by_id = fields.Int(allow_none=True)
    administered_by_name = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


# Initialize schema instances for reuse
client_schema = ClientSchema()
clients_schema = ClientSchema(many=True)
client_update_schema = ClientUpdateSchema()

patient_schema = PatientSchema()
patients_schema = PatientSchema(many=True)
patient_update_schema = PatientUpdateSchema()

visit_schema = VisitSchema()
visits_schema = VisitSchema(many=True)

vital_signs_schema = VitalSignsSchema()
vital_signs_list_schema = VitalSignsSchema(many=True)

soap_note_schema = SOAPNoteSchema()
soap_notes_schema = SOAPNoteSchema(many=True)

diagnosis_schema = DiagnosisSchema()
diagnoses_schema = DiagnosisSchema(many=True)

vaccination_schema = VaccinationSchema()
vaccinations_schema = VaccinationSchema(many=True)


class MedicationSchema(Schema):
    """Schema for Medication (drug database) validation and serialization"""

    id = fields.Int(dump_only=True)

    # Drug Information
    drug_name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    brand_names = fields.Str(allow_none=True)
    drug_class = fields.Str(allow_none=True, validate=validate.Length(max=100))
    controlled_substance = fields.Bool(load_default=False)
    dea_schedule = fields.Str(allow_none=True, validate=validate.Length(max=10))

    # Forms and Strengths
    available_forms = fields.Str(allow_none=True)
    strengths = fields.Str(allow_none=True)

    # Dosing Information
    typical_dose_cats = fields.Str(allow_none=True)
    dosing_frequency = fields.Str(allow_none=True, validate=validate.Length(max=100))
    route_of_administration = fields.Str(allow_none=True, validate=validate.Length(max=50))

    # Clinical Information
    indications = fields.Str(allow_none=True)
    contraindications = fields.Str(allow_none=True)
    side_effects = fields.Str(allow_none=True)
    warnings = fields.Str(allow_none=True)

    # Inventory
    stock_quantity = fields.Int(load_default=0)
    reorder_level = fields.Int(load_default=0)
    unit_cost = fields.Decimal(as_string=True, allow_none=True, places=2)

    # Status
    is_active = fields.Bool(load_default=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class PrescriptionSchema(Schema):
    """Schema for Prescription validation and serialization"""

    id = fields.Int(dump_only=True)

    # Links
    patient_id = fields.Int(required=True)
    patient_name = fields.Str(dump_only=True)
    visit_id = fields.Int(allow_none=True)
    medication_id = fields.Int(required=True)
    medication_name = fields.Str(dump_only=True)

    # Prescription Details
    dosage = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    dosage_form = fields.Str(allow_none=True, validate=validate.Length(max=50))
    frequency = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    route = fields.Str(allow_none=True, validate=validate.Length(max=50))

    # Duration and Quantity
    duration_days = fields.Int(allow_none=True)
    quantity = fields.Decimal(as_string=True, required=True, places=2)
    refills_allowed = fields.Int(load_default=0)
    refills_remaining = fields.Int(load_default=0)

    # Instructions
    instructions = fields.Str(allow_none=True)
    indication = fields.Str(allow_none=True)

    # Status
    status = fields.Str(
        load_default="active", validate=validate.OneOf(["active", "completed", "discontinued", "expired"])
    )
    start_date = fields.Date(required=True)
    end_date = fields.Date(allow_none=True)
    discontinued_date = fields.Date(allow_none=True)
    discontinuation_reason = fields.Str(allow_none=True)

    # Prescriber
    prescribed_by_id = fields.Int(dump_only=True)  # Auto-populated from current_user
    prescribed_by_name = fields.Str(dump_only=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


# Initialize schema instances for reuse
medication_schema = MedicationSchema()
medications_schema = MedicationSchema(many=True)

prescription_schema = PrescriptionSchema()
prescriptions_schema = PrescriptionSchema(many=True)


class ServiceSchema(Schema):
    """Schema for Service (billing catalog) validation and serialization"""

    id = fields.Int(dump_only=True)

    # Service Information
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(allow_none=True)
    category = fields.Str(allow_none=True, validate=validate.Length(max=100))
    service_type = fields.Str(load_default="service", validate=validate.OneOf(["service", "product"]))

    # Pricing
    unit_price = fields.Decimal(as_string=True, required=True, places=2)
    cost = fields.Decimal(as_string=True, allow_none=True, places=2)
    taxable = fields.Bool(load_default=True)

    # Status
    is_active = fields.Bool(load_default=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class InvoiceItemSchema(Schema):
    """Schema for InvoiceItem validation and serialization"""

    id = fields.Int(dump_only=True)

    # Links
    invoice_id = fields.Int(dump_only=True)
    service_id = fields.Int(allow_none=True)
    service_name = fields.Str(dump_only=True)

    # Item Details
    description = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    quantity = fields.Decimal(as_string=True, load_default="1.0", places=2)
    unit_price = fields.Decimal(as_string=True, required=True, places=2)
    total_price = fields.Decimal(as_string=True, required=True, places=2)
    taxable = fields.Bool(load_default=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)


class InvoiceSchema(Schema):
    """Schema for Invoice validation and serialization"""

    id = fields.Int(dump_only=True)

    # Links
    client_id = fields.Int(required=True)
    client_name = fields.Str(dump_only=True)
    patient_id = fields.Int(allow_none=True)
    patient_name = fields.Str(dump_only=True)
    visit_id = fields.Int(allow_none=True)

    # Invoice Details
    invoice_number = fields.Str(dump_only=True)  # Auto-generated
    invoice_date = fields.Date(required=True)
    due_date = fields.Date(allow_none=True)

    # Amounts
    subtotal = fields.Decimal(as_string=True, load_default="0.0", places=2)
    tax_rate = fields.Decimal(as_string=True, load_default="0.0", places=2)
    tax_amount = fields.Decimal(as_string=True, load_default="0.0", places=2)
    discount_amount = fields.Decimal(as_string=True, load_default="0.0", places=2)
    total_amount = fields.Decimal(as_string=True, load_default="0.0", places=2)
    amount_paid = fields.Decimal(as_string=True, dump_only=True, places=2)
    balance_due = fields.Decimal(as_string=True, dump_only=True, places=2)

    # Status
    status = fields.Str(
        load_default="draft",
        validate=validate.OneOf(["draft", "sent", "partial_paid", "paid", "overdue", "cancelled"]),
    )

    # Notes
    notes = fields.Str(allow_none=True)

    # Line items (nested)
    items = fields.Nested(InvoiceItemSchema, many=True, load_default=[])

    # Metadata
    created_by_id = fields.Int(dump_only=True)
    created_by_name = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class PaymentSchema(Schema):
    """Schema for Payment validation and serialization"""

    id = fields.Int(dump_only=True)

    # Links
    invoice_id = fields.Int(required=True)
    invoice_number = fields.Str(dump_only=True)
    client_id = fields.Int(required=True)
    client_name = fields.Str(dump_only=True)

    # Payment Details
    payment_date = fields.DateTime(required=True)
    amount = fields.Decimal(as_string=True, required=True, places=2)
    payment_method = fields.Str(
        required=True,
        validate=validate.OneOf(["cash", "check", "credit_card", "debit_card", "bank_transfer", "other"]),
    )
    reference_number = fields.Str(allow_none=True, validate=validate.Length(max=100))

    # Notes
    notes = fields.Str(allow_none=True)

    # Metadata
    processed_by_id = fields.Int(dump_only=True)
    processed_by_name = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


# Initialize schema instances
service_schema = ServiceSchema()
services_schema = ServiceSchema(many=True)

invoice_schema = InvoiceSchema()
invoices_schema = InvoiceSchema(many=True)

invoice_item_schema = InvoiceItemSchema()
invoice_items_schema = InvoiceItemSchema(many=True)

payment_schema = PaymentSchema()
payments_schema = PaymentSchema(many=True)


# ============================================================================
# PHASE 1.5: APPOINTMENT SCHEMAS
# ============================================================================


class AppointmentTypeSchema(Schema):
    """Schema for AppointmentType validation and serialization"""

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True)
    default_duration_minutes = fields.Int(load_default=30, validate=validate.Range(min=5, max=480))
    color = fields.Str(load_default="#2563eb", validate=validate.Regexp(r"^#[0-9A-Fa-f]{6}$"))
    is_active = fields.Bool(load_default=True)
    created_at = fields.DateTime(dump_only=True)


class AppointmentSchema(Schema):
    """Schema for Appointment validation and serialization"""

    id = fields.Int(dump_only=True)

    # Basic Info
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)
    description = fields.Str(allow_none=True)

    # Relationships
    patient_id = fields.Int(allow_none=True)
    patient_name = fields.Str(dump_only=True)
    client_id = fields.Int(required=True)
    client_name = fields.Str(dump_only=True)
    appointment_type_id = fields.Int(allow_none=True)
    appointment_type_name = fields.Str(dump_only=True)
    appointment_type_color = fields.Str(dump_only=True)

    # Staff and Resources
    assigned_staff_id = fields.Int(allow_none=True)
    assigned_staff_name = fields.Str(dump_only=True)
    room = fields.Str(allow_none=True, validate=validate.Length(max=50))

    # Status
    status = fields.Str(
        load_default="scheduled",
        validate=validate.OneOf(
            ["scheduled", "confirmed", "checked_in", "in_progress", "completed", "cancelled", "no_show"]
        ),
    )

    # Workflow Timestamps
    check_in_time = fields.DateTime(allow_none=True)
    actual_start_time = fields.DateTime(allow_none=True)
    actual_end_time = fields.DateTime(allow_none=True)

    # Cancellation
    cancelled_at = fields.DateTime(allow_none=True)
    cancelled_by_id = fields.Int(allow_none=True)
    cancellation_reason = fields.Str(allow_none=True)

    # Notes and Reminders
    notes = fields.Str(allow_none=True)
    reminder_sent = fields.Bool(dump_only=True)
    reminder_sent_at = fields.DateTime(allow_none=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)
    created_by_id = fields.Int(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


# Initialize appointment schema instances
appointment_type_schema = AppointmentTypeSchema()
appointment_types_schema = AppointmentTypeSchema(many=True)

appointment_schema = AppointmentSchema()
appointments_schema = AppointmentSchema(many=True)


# ============================================================================
# PHASE 3.1: INVENTORY MANAGEMENT SCHEMAS
# ============================================================================


class VendorSchema(Schema):
    """Schema for Vendor model"""

    # Primary Key
    id = fields.Int(dump_only=True)

    # Company Info
    company_name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    contact_name = fields.Str(allow_none=True, validate=validate.Length(max=200))
    email = fields.Email(allow_none=True)
    phone = fields.Str(allow_none=True, validate=validate.Length(max=20))
    fax = fields.Str(allow_none=True, validate=validate.Length(max=20))
    website = fields.Str(allow_none=True, validate=validate.Length(max=200))

    # Address
    address_line1 = fields.Str(allow_none=True, validate=validate.Length(max=200))
    address_line2 = fields.Str(allow_none=True, validate=validate.Length(max=200))
    city = fields.Str(allow_none=True, validate=validate.Length(max=100))
    state = fields.Str(allow_none=True, validate=validate.Length(max=50))
    zip_code = fields.Str(allow_none=True, validate=validate.Length(max=20))
    country = fields.Str(allow_none=True, validate=validate.Length(max=100))

    # Account Info
    account_number = fields.Str(allow_none=True, validate=validate.Length(max=100))
    payment_terms = fields.Str(allow_none=True, validate=validate.Length(max=100))
    tax_id = fields.Str(allow_none=True, validate=validate.Length(max=50))

    # Settings
    preferred_vendor = fields.Bool(load_default=False)
    is_active = fields.Bool(load_default=True)

    # Notes
    notes = fields.Str(allow_none=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ProductSchema(Schema):
    """Schema for Product model"""

    # Primary Key
    id = fields.Int(dump_only=True)

    # Basic Info
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    sku = fields.Str(allow_none=True, validate=validate.Length(max=100))
    description = fields.Str(allow_none=True)

    # Categorization
    product_type = fields.Str(
        required=True,
        validate=validate.OneOf(["medication", "supply", "equipment", "retail"]),
    )
    category = fields.Str(allow_none=True, validate=validate.Length(max=100))

    # Vendor Info
    vendor_id = fields.Int(allow_none=True)
    vendor_name = fields.Str(dump_only=True)
    vendor_sku = fields.Str(allow_none=True, validate=validate.Length(max=100))

    # Inventory Tracking
    stock_quantity = fields.Int(load_default=0)
    reorder_level = fields.Int(load_default=0)
    reorder_quantity = fields.Int(load_default=0)
    unit_of_measure = fields.Str(load_default="each", validate=validate.Length(max=50))

    # Pricing
    unit_cost = fields.Decimal(as_string=True, allow_none=True, places=2)
    unit_price = fields.Decimal(as_string=True, allow_none=True, places=2)
    markup_percentage = fields.Decimal(as_string=True, allow_none=True, places=2)

    # Product Details
    manufacturer = fields.Str(allow_none=True, validate=validate.Length(max=200))
    lot_number = fields.Str(allow_none=True, validate=validate.Length(max=100))
    expiration_date = fields.Date(allow_none=True)
    storage_location = fields.Str(allow_none=True, validate=validate.Length(max=100))

    # Flags
    requires_prescription = fields.Bool(load_default=False)
    controlled_substance = fields.Bool(load_default=False)
    taxable = fields.Bool(load_default=True)
    is_active = fields.Bool(load_default=True)

    # Notes
    notes = fields.Str(allow_none=True)

    # Computed Properties
    needs_reorder = fields.Bool(dump_only=True)
    is_out_of_stock = fields.Bool(dump_only=True)
    stock_value = fields.Float(dump_only=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class PurchaseOrderItemSchema(Schema):
    """Schema for Purchase Order Item model"""

    # Primary Key
    id = fields.Int(dump_only=True)

    # Links
    purchase_order_id = fields.Int(dump_only=True)
    product_id = fields.Int(required=True)
    product_name = fields.Str(dump_only=True)

    # Order Details
    quantity_ordered = fields.Int(required=True, validate=validate.Range(min=1))
    quantity_received = fields.Int(load_default=0)
    unit_cost = fields.Decimal(as_string=True, required=True, places=2)
    total_cost = fields.Decimal(as_string=True, required=True, places=2)

    # Notes
    notes = fields.Str(allow_none=True)


class PurchaseOrderSchema(Schema):
    """Schema for Purchase Order model"""

    # Primary Key
    id = fields.Int(dump_only=True)

    # Order Info
    po_number = fields.Str(dump_only=True)
    vendor_id = fields.Int(required=True)
    vendor_name = fields.Str(dump_only=True)
    order_date = fields.Date(required=True)
    expected_delivery_date = fields.Date(allow_none=True)
    actual_delivery_date = fields.Date(allow_none=True)

    # Status
    status = fields.Str(
        load_default="draft",
        validate=validate.OneOf(["draft", "submitted", "received", "partially_received", "cancelled"]),
    )

    # Amounts
    subtotal = fields.Decimal(as_string=True, load_default="0.0", places=2)
    tax = fields.Decimal(as_string=True, load_default="0.0", places=2)
    shipping = fields.Decimal(as_string=True, load_default="0.0", places=2)
    total_amount = fields.Decimal(as_string=True, load_default="0.0", places=2)

    # Notes
    notes = fields.Str(allow_none=True)
    shipping_address = fields.Str(allow_none=True)

    # Metadata
    created_by_id = fields.Int(dump_only=True)
    created_by_name = fields.Str(dump_only=True)
    received_by_id = fields.Int(dump_only=True)
    received_by_name = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Nested Items
    items = fields.List(fields.Nested(PurchaseOrderItemSchema), allow_none=True)


class InventoryTransactionSchema(Schema):
    """Schema for Inventory Transaction model"""

    # Primary Key
    id = fields.Int(dump_only=True)

    # Links
    product_id = fields.Int(required=True)
    product_name = fields.Str(dump_only=True)
    purchase_order_id = fields.Int(allow_none=True)

    # Transaction Details
    transaction_type = fields.Str(
        required=True,
        validate=validate.OneOf(["received", "dispensed", "adjustment", "return", "expired", "damaged"]),
    )
    quantity = fields.Int(required=True)
    quantity_before = fields.Int(required=True)
    quantity_after = fields.Int(required=True)

    # Additional Info
    reason = fields.Str(allow_none=True, validate=validate.Length(max=200))
    reference_number = fields.Str(allow_none=True, validate=validate.Length(max=100))
    notes = fields.Str(allow_none=True)

    # Metadata
    transaction_date = fields.DateTime(required=True)
    performed_by_id = fields.Int(dump_only=True)
    performed_by_name = fields.Str(dump_only=True)


# Initialize inventory schema instances
vendor_schema = VendorSchema()
vendors_schema = VendorSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

purchase_order_schema = PurchaseOrderSchema()
purchase_orders_schema = PurchaseOrderSchema(many=True)

purchase_order_item_schema = PurchaseOrderItemSchema()
purchase_order_items_schema = PurchaseOrderItemSchema(many=True)

inventory_transaction_schema = InventoryTransactionSchema()
inventory_transactions_schema = InventoryTransactionSchema(many=True)


# ============================================================================
# STAFF & SCHEDULING SCHEMAS
# ============================================================================


class StaffSchema(Schema):
    """Schema for Staff model validation"""

    # IDs
    id = fields.Int(dump_only=True)
    user_id = fields.Int(allow_none=True)

    # Personal Information
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    full_name = fields.Str(dump_only=True)
    email = fields.Email(required=True)
    phone = fields.Str(allow_none=True, validate=validate.Length(max=20))
    emergency_contact_name = fields.Str(allow_none=True, validate=validate.Length(max=100))
    emergency_contact_phone = fields.Str(allow_none=True, validate=validate.Length(max=20))

    # Employment Details
    position = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    department = fields.Str(allow_none=True, validate=validate.Length(max=100))
    employment_type = fields.Str(
        required=True,
        validate=validate.OneOf(["full-time", "part-time", "contract", "intern"]),
    )
    hire_date = fields.Date(required=True)
    termination_date = fields.Date(allow_none=True)

    # Credentials & Certifications
    license_number = fields.Str(allow_none=True, validate=validate.Length(max=100))
    license_state = fields.Str(allow_none=True, validate=validate.Length(max=50))
    license_expiry = fields.Date(allow_none=True)
    certifications = fields.Str(allow_none=True)
    education = fields.Str(allow_none=True)

    # Work Schedule
    default_schedule = fields.Str(allow_none=True, validate=validate.Length(max=200))
    hourly_rate = fields.Decimal(allow_none=True, as_string=True, places=2)

    # Permissions & Access
    can_prescribe = fields.Bool(load_default=False)
    can_perform_surgery = fields.Bool(load_default=False)
    can_access_billing = fields.Bool(load_default=False)

    # Notes
    notes = fields.Str(allow_none=True)

    # Metadata
    is_active = fields.Bool(load_default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ScheduleSchema(Schema):
    """Schema for Schedule/Shift model validation"""

    # IDs
    id = fields.Int(dump_only=True)
    staff_id = fields.Int(required=True)
    staff_name = fields.Str(dump_only=True)
    staff_position = fields.Str(dump_only=True)

    # Schedule Details
    shift_date = fields.Date(required=True)
    start_time = fields.Time(required=True)
    end_time = fields.Time(required=True)

    # Shift Type & Status
    shift_type = fields.Str(
        required=True,
        validate=validate.OneOf(["regular", "on-call", "overtime", "training"]),
    )
    status = fields.Str(
        required=True,
        validate=validate.OneOf(["scheduled", "completed", "cancelled", "no-show"]),
    )

    # Break Information
    break_minutes = fields.Int(load_default=30, validate=validate.Range(min=0, max=480))

    # Location & Role
    location = fields.Str(allow_none=True, validate=validate.Length(max=100))
    role = fields.Str(allow_none=True, validate=validate.Length(max=100))

    # Time Off / Leave
    is_time_off = fields.Bool(load_default=False)
    time_off_type = fields.Str(
        allow_none=True,
        validate=validate.OneOf(["vacation", "sick", "personal", "unpaid", "bereavement"]),
    )
    time_off_approved = fields.Bool(load_default=False)
    approved_by_id = fields.Int(allow_none=True)
    approved_by_name = fields.Str(dump_only=True)

    # Notes
    notes = fields.Str(allow_none=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Note: End time validation is handled in the API endpoint to ensure
    # both start_time and end_time are available for comparison


# Initialize staff schema instances
staff_schema = StaffSchema()
staffs_schema = StaffSchema(many=True)

schedule_schema = ScheduleSchema()
schedules_schema = ScheduleSchema(many=True)


# ============================================================================
# LABORATORY SCHEMAS
# ============================================================================


class LabTestSchema(Schema):
    """Schema for LabTest model validation"""

    # IDs
    id = fields.Int(dump_only=True)

    # Test Information
    test_code = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    test_name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    category = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True)

    # Specimen Requirements
    specimen_type = fields.Str(allow_none=True, validate=validate.Length(max=100))
    specimen_volume = fields.Str(allow_none=True, validate=validate.Length(max=50))
    collection_instructions = fields.Str(allow_none=True)

    # Reference Range
    reference_range = fields.Str(allow_none=True)

    # Turnaround Time
    turnaround_time = fields.Str(allow_none=True, validate=validate.Length(max=100))

    # External Lab Information
    external_lab = fields.Bool(load_default=False)
    external_lab_name = fields.Str(allow_none=True, validate=validate.Length(max=200))
    external_lab_code = fields.Str(allow_none=True, validate=validate.Length(max=100))

    # Pricing
    cost = fields.Decimal(allow_none=True, as_string=True, places=2)
    price = fields.Decimal(allow_none=True, as_string=True, places=2)

    # Metadata
    is_active = fields.Bool(load_default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class LabResultSchema(Schema):
    """Schema for LabResult model validation"""

    # IDs
    id = fields.Int(dump_only=True)

    # Associations
    patient_id = fields.Int(required=True)
    patient_name = fields.Str(dump_only=True)
    visit_id = fields.Int(allow_none=True)
    test_id = fields.Int(required=True)
    test_code = fields.Str(dump_only=True)
    test_name = fields.Str(dump_only=True)
    test_category = fields.Str(dump_only=True)

    # Order Information
    order_date = fields.DateTime(required=True)
    ordered_by_id = fields.Int(dump_only=True)
    ordered_by_name = fields.Str(dump_only=True)

    # Status Tracking
    status = fields.Str(
        required=True,
        validate=validate.OneOf(["pending", "in_progress", "completed", "cancelled"]),
    )

    # Result Information
    result_date = fields.DateTime(allow_none=True)
    result_value = fields.Str(allow_none=True)
    result_unit = fields.Str(allow_none=True, validate=validate.Length(max=50))

    # Interpretation
    is_abnormal = fields.Bool(load_default=False)
    abnormal_flag = fields.Str(
        allow_none=True, validate=validate.OneOf(["H", "L", "A", ""])
    )
    interpretation = fields.Str(allow_none=True)

    # External Lab Tracking
    external_reference_number = fields.Str(allow_none=True, validate=validate.Length(max=100))

    # Reviewed Status
    reviewed = fields.Bool(load_default=False)
    reviewed_by_id = fields.Int(allow_none=True, dump_only=True)
    reviewed_by_name = fields.Str(dump_only=True)
    reviewed_date = fields.DateTime(allow_none=True, dump_only=True)

    # Notes
    notes = fields.Str(allow_none=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


# Initialize lab schema instances
lab_test_schema = LabTestSchema()
lab_tests_schema = LabTestSchema(many=True)

lab_result_schema = LabResultSchema()
lab_results_schema = LabResultSchema(many=True)
