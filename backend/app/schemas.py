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
