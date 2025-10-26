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


# Initialize schema instances for reuse
client_schema = ClientSchema()
clients_schema = ClientSchema(many=True)
client_update_schema = ClientUpdateSchema()

patient_schema = PatientSchema()
patients_schema = PatientSchema(many=True)
patient_update_schema = PatientUpdateSchema()
