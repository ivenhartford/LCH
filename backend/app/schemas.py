"""
Marshmallow schemas for API request/response validation and serialization
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import datetime


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
        allow_none=True,
        validate=validate.OneOf(['email', 'phone', 'sms']),
        load_default='email'
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
    preferred_contact = fields.Str(
        allow_none=True,
        validate=validate.OneOf(['email', 'phone', 'sms'])
    )
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
    species = fields.Str(load_default='Cat', validate=validate.Length(max=50))
    breed = fields.Str(allow_none=True, validate=validate.Length(max=100))
    color = fields.Str(allow_none=True, validate=validate.Length(max=100))
    markings = fields.Str(allow_none=True)

    # Physical Characteristics
    sex = fields.Str(
        allow_none=True,
        validate=validate.OneOf(['Male', 'Female'])
    )
    reproductive_status = fields.Str(
        allow_none=True,
        validate=validate.OneOf(['Intact', 'Spayed', 'Neutered'])
    )
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
    status = fields.Str(
        load_default='Active',
        validate=validate.OneOf(['Active', 'Inactive', 'Deceased'])
    )
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
    sex = fields.Str(allow_none=True, validate=validate.OneOf(['Male', 'Female']))
    reproductive_status = fields.Str(
        allow_none=True,
        validate=validate.OneOf(['Intact', 'Spayed', 'Neutered'])
    )
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
    status = fields.Str(validate=validate.OneOf(['Active', 'Inactive', 'Deceased']))
    deceased_date = fields.Date(allow_none=True)


class AppointmentTypeSchema(Schema):
    """Schema for AppointmentType model validation and serialization"""

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True)
    default_duration_minutes = fields.Int(load_default=30, validate=validate.Range(min=5, max=480))
    color = fields.Str(
        load_default='#2563eb',
        validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$', error='Must be a valid hex color (e.g., #2563eb)')
    )
    is_active = fields.Bool(load_default=True)
    created_at = fields.DateTime(dump_only=True)


class AppointmentTypeUpdateSchema(Schema):
    """Schema for updating existing appointment type (all fields optional)"""

    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True)
    default_duration_minutes = fields.Int(validate=validate.Range(min=5, max=480))
    color = fields.Str(
        validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$', error='Must be a valid hex color (e.g., #2563eb)')
    )
    is_active = fields.Bool()


class AppointmentSchema(Schema):
    """Schema for Appointment model validation and serialization"""

    id = fields.Int(dump_only=True)

    # Basic Info
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)
    description = fields.Str(allow_none=True)

    # Relationships
    patient_id = fields.Int(allow_none=True)  # Nullable for client-only appointments
    patient_name = fields.Str(dump_only=True)
    client_id = fields.Int(required=True)
    client_name = fields.Str(dump_only=True)
    appointment_type_id = fields.Int(allow_none=True)
    appointment_type_name = fields.Str(dump_only=True)
    appointment_type_color = fields.Str(dump_only=True)

    # Status workflow
    status = fields.Str(
        load_default='scheduled',
        validate=validate.OneOf([
            'scheduled', 'confirmed', 'checked_in',
            'in_progress', 'completed', 'cancelled', 'no_show'
        ])
    )

    # Staff and resources
    assigned_staff_id = fields.Int(allow_none=True)
    assigned_staff_name = fields.Str(dump_only=True)
    room = fields.Str(allow_none=True, validate=validate.Length(max=50))

    # Timing tracking
    check_in_time = fields.DateTime(allow_none=True)
    actual_start_time = fields.DateTime(allow_none=True)
    actual_end_time = fields.DateTime(allow_none=True)

    # Cancellation tracking
    cancelled_at = fields.DateTime(dump_only=True)
    cancelled_by_name = fields.Str(dump_only=True)
    cancellation_reason = fields.Str(allow_none=True)

    # Notes and reminders
    notes = fields.Str(allow_none=True)
    reminder_sent = fields.Bool(dump_only=True)
    reminder_sent_at = fields.DateTime(dump_only=True)

    # Metadata
    created_at = fields.DateTime(dump_only=True)
    created_by_name = fields.Str(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates('end_time')
    def validate_end_time(self, value):
        """Ensure end_time is after start_time"""
        if 'start_time' in self.context and value <= self.context['start_time']:
            raise ValidationError('End time must be after start time')


class AppointmentUpdateSchema(Schema):
    """Schema for updating existing appointment (all fields optional)"""

    # Basic Info
    title = fields.Str(validate=validate.Length(min=1, max=200))
    start_time = fields.DateTime()
    end_time = fields.DateTime()
    description = fields.Str(allow_none=True)

    # Relationships
    patient_id = fields.Int(allow_none=True)
    client_id = fields.Int()
    appointment_type_id = fields.Int(allow_none=True)

    # Status workflow
    status = fields.Str(
        validate=validate.OneOf([
            'scheduled', 'confirmed', 'checked_in',
            'in_progress', 'completed', 'cancelled', 'no_show'
        ])
    )

    # Staff and resources
    assigned_staff_id = fields.Int(allow_none=True)
    room = fields.Str(allow_none=True, validate=validate.Length(max=50))

    # Timing tracking
    check_in_time = fields.DateTime(allow_none=True)
    actual_start_time = fields.DateTime(allow_none=True)
    actual_end_time = fields.DateTime(allow_none=True)

    # Cancellation tracking
    cancellation_reason = fields.Str(allow_none=True)

    # Notes
    notes = fields.Str(allow_none=True)


# Initialize schema instances for reuse
client_schema = ClientSchema()
clients_schema = ClientSchema(many=True)
client_update_schema = ClientUpdateSchema()

patient_schema = PatientSchema()
patients_schema = PatientSchema(many=True)
patient_update_schema = PatientUpdateSchema()

appointment_type_schema = AppointmentTypeSchema()
appointment_types_schema = AppointmentTypeSchema(many=True)
appointment_type_update_schema = AppointmentTypeUpdateSchema()

appointment_schema = AppointmentSchema()
appointments_schema = AppointmentSchema(many=True)
appointment_update_schema = AppointmentUpdateSchema()
