from . import db
import bcrypt
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(80), nullable=False, default="user")

    # Account lockout fields (matching portal user behavior)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)

    # PIN and session management
    pin_hash = db.Column(db.String(128), nullable=True)
    last_activity_at = db.Column(db.DateTime, nullable=True)
    session_expires_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def check_password(self, password):
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))

    def set_pin(self, pin):
        """Set PIN hash using bcrypt (4-6 digit PIN)"""
        if not pin or not pin.isdigit() or len(pin) < 4 or len(pin) > 6:
            raise ValueError("PIN must be 4-6 digits")
        self.pin_hash = bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def check_pin(self, pin):
        """Verify PIN against hash"""
        if not self.pin_hash or not pin:
            return False
        try:
            return bcrypt.checkpw(pin.encode("utf-8"), self.pin_hash.encode("utf-8"))
        except Exception:
            return False


class Client(db.Model):
    """
    Client (Pet Owner) Model

    Stores information about pet owners/clients.
    Includes contact information, communication preferences, and account details.
    """

    __tablename__ = "client"

    id = db.Column(db.Integer, primary_key=True)

    # Personal Info
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone_primary = db.Column(db.String(20), nullable=False)
    phone_secondary = db.Column(db.String(20), nullable=True)

    # Address
    address_line1 = db.Column(db.String(200), nullable=True)
    address_line2 = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)

    # Communication Preferences
    preferred_contact = db.Column(db.String(20), default="email")  # email, phone, sms
    email_reminders = db.Column(db.Boolean, default=True)
    sms_reminders = db.Column(db.Boolean, default=True)

    # Account
    account_balance = db.Column(db.Numeric(10, 2), default=0.00)
    credit_limit = db.Column(db.Numeric(10, 2), default=0.00)

    # Notes and Alerts
    notes = db.Column(db.Text, nullable=True)
    alerts = db.Column(db.Text, nullable=True)  # Important alerts (e.g., "Aggressive dog owner")

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    patients = db.relationship("Patient", back_populates="owner", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client {self.first_name} {self.last_name}>"

    def to_dict(self):
        """Convert client to dictionary for API responses"""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": f"{self.first_name} {self.last_name}",
            "email": self.email,
            "phone_primary": self.phone_primary,
            "phone_secondary": self.phone_secondary,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "preferred_contact": self.preferred_contact,
            "email_reminders": self.email_reminders,
            "sms_reminders": self.sms_reminders,
            "account_balance": float(self.account_balance) if self.account_balance else 0.0,
            "credit_limit": float(self.credit_limit) if self.credit_limit else 0.0,
            "notes": self.notes,
            "alerts": self.alerts,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Patient(db.Model):
    """
    Patient (Cat) Model

    Stores comprehensive information about cat patients at the clinic.
    NOTE: Lenox Cat Hospital is a FELINE-ONLY clinic - all patients are cats.
    """

    __tablename__ = "patient"

    id = db.Column(db.Integer, primary_key=True)

    # Basic Info
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), default="Cat", nullable=False)  # Always "Cat" - feline-only clinic
    breed = db.Column(db.String(100))  # Cat breeds: Persian, Siamese, Maine Coon, Domestic Shorthair, etc.
    color = db.Column(db.String(100))  # Fur color: Orange Tabby, Black, Calico, etc.
    markings = db.Column(db.Text)  # Special markings or patterns

    # Physical Characteristics
    sex = db.Column(db.String(20))  # Male, Female
    reproductive_status = db.Column(db.String(50))  # Intact, Spayed, Neutered
    date_of_birth = db.Column(db.Date, nullable=True)
    approximate_age = db.Column(db.String(50))  # If exact DOB unknown: "2 years", "6 months", etc.
    weight_kg = db.Column(db.Numeric(5, 2))  # Weight in kilograms

    # Identification
    microchip_number = db.Column(db.String(50), unique=True, nullable=True)

    # Insurance
    insurance_company = db.Column(db.String(100))
    insurance_policy_number = db.Column(db.String(100))

    # Owner/Client Link
    owner_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)

    # Photo
    photo_url = db.Column(db.String(500))  # Local file path or URL to cat photo

    # Medical Info (basic - detailed in medical records)
    allergies = db.Column(db.Text)  # Known allergies
    medical_notes = db.Column(db.Text)  # Important medical notes
    behavioral_notes = db.Column(db.Text)  # Temperament, behavior notes

    # Status
    status = db.Column(db.String(20), default="Active", nullable=False)  # Active, Inactive, Deceased
    deceased_date = db.Column(db.Date, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner = db.relationship("Client", back_populates="patients")

    def __repr__(self):
        return f'<Patient {self.name} ({self.breed or "Mixed"})>'

    def to_dict(self):
        """Convert patient to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "color": self.color,
            "markings": self.markings,
            "sex": self.sex,
            "reproductive_status": self.reproductive_status,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "approximate_age": self.approximate_age,
            "age_display": self._calculate_age_display(),
            "weight_kg": float(self.weight_kg) if self.weight_kg else None,
            "microchip_number": self.microchip_number,
            "insurance_company": self.insurance_company,
            "insurance_policy_number": self.insurance_policy_number,
            "owner_id": self.owner_id,
            "owner_name": f"{self.owner.first_name} {self.owner.last_name}" if self.owner else None,
            "photo_url": self.photo_url,
            "allergies": self.allergies,
            "medical_notes": self.medical_notes,
            "behavioral_notes": self.behavioral_notes,
            "status": self.status,
            "deceased_date": self.deceased_date.isoformat() if self.deceased_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def _calculate_age_display(self):
        """Calculate and return human-readable age"""
        if self.date_of_birth:
            today = datetime.utcnow().date()
            age_delta = today - self.date_of_birth
            years = age_delta.days // 365
            months = (age_delta.days % 365) // 30

            if years > 0:
                if months > 0:
                    year_str = f'{years} year{"s" if years != 1 else ""}'
                    month_str = f'{months} month{"s" if months != 1 else ""}'
                    return f"{year_str}, {month_str}"
                return f'{years} year{"s" if years != 1 else ""}'
            elif months > 0:
                return f'{months} month{"s" if months != 1 else ""}'
            else:
                weeks = age_delta.days // 7
                if weeks > 0:
                    return f'{weeks} week{"s" if weeks != 1 else ""}'
                return f'{age_delta.days} day{"s" if age_delta.days != 1 else ""}'
        elif self.approximate_age:
            return self.approximate_age
        return "Unknown"


# Keep Pet as an alias for backwards compatibility with existing code
Pet = Patient


class AppointmentType(db.Model):
    """
    AppointmentType Model - Categories of appointments (e.g., Wellness, Surgery, Emergency)

    Used for color-coding calendar, duration defaults, and pricing
    """

    __tablename__ = "appointment_type"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    default_duration_minutes = db.Column(db.Integer, default=30)  # Default appointment length
    color = db.Column(db.String(7), default="#2563eb")  # Hex color for calendar
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    appointments = db.relationship("Appointment", back_populates="appointment_type", lazy=True)

    def __repr__(self):
        return f"<AppointmentType {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "default_duration_minutes": self.default_duration_minutes,
            "color": self.color,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Appointment(db.Model):
    """
    Enhanced Appointment Model

    Tracks appointments with patient, client, type, status, assigned staff, and room information.
    Includes full appointment workflow from scheduled to completed.
    """

    __tablename__ = "appointment"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False, index=True)
    description = db.Column(db.Text)

    # Relationships to core entities
    patient_id = db.Column(
        db.Integer, db.ForeignKey("patient.id"), nullable=True
    )  # Nullable for client-only appointments
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False, index=True)

    # Appointment categorization
    appointment_type_id = db.Column(db.Integer, db.ForeignKey("appointment_type.id"), nullable=True)

    # Status workflow: scheduled, confirmed, checked_in, in_progress, completed, cancelled, no_show
    status = db.Column(db.String(20), default="scheduled", nullable=False, index=True)

    # Staff and resources
    assigned_staff_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True
    )  # Veterinarian/technician
    room = db.Column(db.String(50))  # Exam room identifier

    # Additional tracking
    check_in_time = db.Column(db.DateTime)  # When patient checked in
    actual_start_time = db.Column(db.DateTime)  # When appointment actually started
    actual_end_time = db.Column(db.DateTime)  # When appointment actually ended

    # Cancellation tracking
    cancelled_at = db.Column(db.DateTime)
    cancelled_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    cancellation_reason = db.Column(db.Text)

    # Notes and reminders
    notes = db.Column(db.Text)  # Internal staff notes
    reminder_sent = db.Column(db.Boolean, default=False)
    reminder_sent_at = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = db.relationship("Patient", backref="appointments", lazy=True)
    client = db.relationship("Client", backref="appointments", lazy=True)
    appointment_type = db.relationship("AppointmentType", back_populates="appointments", lazy=True)
    assigned_staff = db.relationship(
        "User", foreign_keys=[assigned_staff_id], backref="assigned_appointments", lazy=True
    )
    cancelled_by = db.relationship(
        "User", foreign_keys=[cancelled_by_id], backref="cancelled_appointments", lazy=True
    )
    created_by = db.relationship(
        "User", foreign_keys=[created_by_id], backref="created_appointments", lazy=True
    )

    def __repr__(self):
        return f"<Appointment {self.id}: {self.title} at {self.start_time}>"

    def to_dict(self):
        """Convert appointment to dictionary for API responses"""
        return {
            "id": self.id,
            "title": self.title,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "description": self.description,
            "patient_id": self.patient_id,
            "patient_name": self.patient.name if self.patient else None,
            "client_id": self.client_id,
            "client_name": f"{self.client.first_name} {self.client.last_name}" if self.client else None,
            "appointment_type_id": self.appointment_type_id,
            "appointment_type_name": self.appointment_type.name if self.appointment_type else None,
            "appointment_type_color": self.appointment_type.color if self.appointment_type else "#2563eb",
            "status": self.status,
            "assigned_staff_id": self.assigned_staff_id,
            "assigned_staff_name": self.assigned_staff.username if self.assigned_staff else None,
            "room": self.room,
            "check_in_time": self.check_in_time.isoformat() if self.check_in_time else None,
            "actual_start_time": self.actual_start_time.isoformat() if self.actual_start_time else None,
            "actual_end_time": self.actual_end_time.isoformat() if self.actual_end_time else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "cancellation_reason": self.cancellation_reason,
            "notes": self.notes,
            "reminder_sent": self.reminder_sent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Visit(db.Model):
    """
    Visit Model - Records of patient visits to the clinic

    A visit represents a patient coming to the clinic for medical care.
    Each visit can have associated SOAP notes, vital signs, diagnoses, and prescriptions.
    """

    __tablename__ = "visit"

    id = db.Column(db.Integer, primary_key=True)

    # Basic Info
    visit_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    visit_type = db.Column(db.String(50), nullable=False)  # Wellness, Sick, Emergency, Follow-up, Surgery, etc.
    status = db.Column(
        db.String(20), default="scheduled", nullable=False
    )  # scheduled, in_progress, completed, cancelled

    # Patient and Staff Links
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    veterinarian_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)  # Vet who saw the patient
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointment.id"), nullable=True
    )  # Link to appointment if created from one

    # Visit Details
    chief_complaint = db.Column(db.Text)  # Main reason for visit
    visit_notes = db.Column(db.Text)  # General visit notes

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    patient = db.relationship("Patient", backref="visits")
    veterinarian = db.relationship("User", backref="visits_conducted")
    soap_notes = db.relationship("SOAPNote", back_populates="visit", cascade="all, delete-orphan")
    vital_signs = db.relationship("VitalSigns", back_populates="visit", cascade="all, delete-orphan")
    diagnoses = db.relationship("Diagnosis", back_populates="visit", cascade="all, delete-orphan")
    vaccinations = db.relationship("Vaccination", back_populates="visit", cascade="all, delete-orphan")
    prescriptions = db.relationship("Prescription", back_populates="visit", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Visit {self.id} - Patient {self.patient_id} - {self.visit_date}>"

    def to_dict(self):
        """Convert visit to dictionary for API responses"""
        return {
            "id": self.id,
            "visit_date": self.visit_date.isoformat() if self.visit_date else None,
            "visit_type": self.visit_type,
            "status": self.status,
            "patient_id": self.patient_id,
            "patient_name": self.patient.name if self.patient else None,
            "veterinarian_id": self.veterinarian_id,
            "veterinarian_name": self.veterinarian.username if self.veterinarian else None,
            "appointment_id": self.appointment_id,
            "chief_complaint": self.chief_complaint,
            "visit_notes": self.visit_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class VitalSigns(db.Model):
    """
    Vital Signs Model - Records vital signs taken during a visit

    Stores temperature, weight, heart rate, respiratory rate, etc.
    """

    __tablename__ = "vital_signs"

    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("visit.id"), nullable=False)

    # Vital Signs
    temperature_c = db.Column(db.Numeric(4, 1), nullable=True)  # Temperature in Celsius
    weight_kg = db.Column(db.Numeric(5, 2), nullable=True)  # Weight in kilograms
    heart_rate = db.Column(db.Integer, nullable=True)  # Beats per minute
    respiratory_rate = db.Column(db.Integer, nullable=True)  # Breaths per minute
    blood_pressure_systolic = db.Column(db.Integer, nullable=True)  # mmHg
    blood_pressure_diastolic = db.Column(db.Integer, nullable=True)  # mmHg
    capillary_refill_time = db.Column(db.String(20), nullable=True)  # e.g., "<2 seconds"
    mucous_membrane_color = db.Column(db.String(50), nullable=True)  # Pink, Pale, Cyanotic, etc.
    body_condition_score = db.Column(db.Integer, nullable=True)  # 1-9 scale

    # Additional Info
    pain_score = db.Column(db.Integer, nullable=True)  # 0-10 scale
    notes = db.Column(db.Text, nullable=True)

    # Metadata
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    recorded_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    # Relationships
    visit = db.relationship("Visit", back_populates="vital_signs")
    recorded_by = db.relationship("User")

    def __repr__(self):
        return f"<VitalSigns Visit {self.visit_id}>"

    def to_dict(self):
        """Convert vital signs to dictionary for API responses"""
        return {
            "id": self.id,
            "visit_id": self.visit_id,
            "temperature_c": float(self.temperature_c) if self.temperature_c else None,
            "weight_kg": float(self.weight_kg) if self.weight_kg else None,
            "heart_rate": self.heart_rate,
            "respiratory_rate": self.respiratory_rate,
            "blood_pressure_systolic": self.blood_pressure_systolic,
            "blood_pressure_diastolic": self.blood_pressure_diastolic,
            "capillary_refill_time": self.capillary_refill_time,
            "mucous_membrane_color": self.mucous_membrane_color,
            "body_condition_score": self.body_condition_score,
            "pain_score": self.pain_score,
            "notes": self.notes,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "recorded_by_id": self.recorded_by_id,
            "recorded_by_name": self.recorded_by.username if self.recorded_by else None,
        }


class SOAPNote(db.Model):
    """
    SOAP Note Model - Clinical notes following SOAP format

    SOAP = Subjective, Objective, Assessment, Plan
    Standard format for medical record documentation
    """

    __tablename__ = "soap_note"

    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("visit.id"), nullable=False)

    # SOAP Components
    subjective = db.Column(db.Text, nullable=True)  # Patient history, owner's observations, symptoms
    objective = db.Column(db.Text, nullable=True)  # Physical exam findings, test results, vital signs
    assessment = db.Column(db.Text, nullable=True)  # Diagnosis, differential diagnosis
    plan = db.Column(db.Text, nullable=True)  # Treatment plan, medications, follow-up instructions

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Relationships
    visit = db.relationship("Visit", back_populates="soap_notes")
    created_by = db.relationship("User")

    def __repr__(self):
        return f"<SOAPNote Visit {self.visit_id}>"

    def to_dict(self):
        """Convert SOAP note to dictionary for API responses"""
        return {
            "id": self.id,
            "visit_id": self.visit_id,
            "subjective": self.subjective,
            "objective": self.objective,
            "assessment": self.assessment,
            "plan": self.plan,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by.username if self.created_by else None,
        }


class Diagnosis(db.Model):
    """
    Diagnosis Model - Medical diagnoses assigned during visits

    Includes ICD-10 codes for standardization
    """

    __tablename__ = "diagnosis"

    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("visit.id"), nullable=False)

    # Diagnosis Info
    diagnosis_name = db.Column(db.String(200), nullable=False)
    icd_code = db.Column(db.String(20), nullable=True)  # ICD-10 code
    diagnosis_type = db.Column(db.String(50), default="primary")  # primary, differential, rule-out
    severity = db.Column(db.String(20), nullable=True)  # mild, moderate, severe
    status = db.Column(db.String(20), default="active")  # active, resolved, chronic, ruled-out

    # Additional Details
    notes = db.Column(db.Text, nullable=True)
    onset_date = db.Column(db.Date, nullable=True)
    resolution_date = db.Column(db.Date, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Relationships
    visit = db.relationship("Visit", back_populates="diagnoses")
    created_by = db.relationship("User")

    def __repr__(self):
        return f"<Diagnosis {self.diagnosis_name} ({self.icd_code})>"

    def to_dict(self):
        """Convert diagnosis to dictionary for API responses"""
        return {
            "id": self.id,
            "visit_id": self.visit_id,
            "diagnosis_name": self.diagnosis_name,
            "icd_code": self.icd_code,
            "diagnosis_type": self.diagnosis_type,
            "severity": self.severity,
            "status": self.status,
            "notes": self.notes,
            "onset_date": self.onset_date.isoformat() if self.onset_date else None,
            "resolution_date": self.resolution_date.isoformat() if self.resolution_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by.username if self.created_by else None,
        }


class Vaccination(db.Model):
    """
    Vaccination Model - Vaccination records

    Tracks all vaccines administered to patients
    """

    __tablename__ = "vaccination"

    id = db.Column(db.Integer, primary_key=True)

    # Patient and Visit Link
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey("visit.id"), nullable=True)  # Visit when vaccine was given

    # Vaccine Info
    vaccine_name = db.Column(db.String(200), nullable=False)  # FVRCP, Rabies, FeLV, etc. (cat vaccines)
    vaccine_type = db.Column(db.String(100), nullable=True)  # Core, Non-core, Lifestyle-dependent
    manufacturer = db.Column(db.String(100), nullable=True)
    lot_number = db.Column(db.String(100), nullable=True)
    serial_number = db.Column(db.String(100), nullable=True)

    # Administration Details
    administration_date = db.Column(db.Date, nullable=False)
    expiration_date = db.Column(db.Date, nullable=True)
    next_due_date = db.Column(db.Date, nullable=True)  # When next dose/booster is due
    dosage = db.Column(db.String(50), nullable=True)
    route = db.Column(db.String(50), nullable=True)  # SC (subcutaneous), IM (intramuscular), etc.
    administration_site = db.Column(db.String(100), nullable=True)  # Right shoulder, etc.

    # Status
    status = db.Column(db.String(20), default="current")  # current, overdue, not_due, declined

    # Notes
    notes = db.Column(db.Text, nullable=True)
    adverse_reactions = db.Column(db.Text, nullable=True)

    # Metadata
    administered_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = db.relationship("Patient", backref="vaccinations")
    visit = db.relationship("Visit", back_populates="vaccinations")
    administered_by = db.relationship("User")

    def __repr__(self):
        return f"<Vaccination {self.vaccine_name} - Patient {self.patient_id}>"

    def to_dict(self):
        """Convert vaccination to dictionary for API responses"""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": self.patient.name if self.patient else None,
            "visit_id": self.visit_id,
            "vaccine_name": self.vaccine_name,
            "vaccine_type": self.vaccine_type,
            "manufacturer": self.manufacturer,
            "lot_number": self.lot_number,
            "serial_number": self.serial_number,
            "administration_date": (self.administration_date.isoformat() if self.administration_date else None),
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "next_due_date": self.next_due_date.isoformat() if self.next_due_date else None,
            "dosage": self.dosage,
            "route": self.route,
            "administration_site": self.administration_site,
            "status": self.status,
            "notes": self.notes,
            "adverse_reactions": self.adverse_reactions,
            "administered_by_id": self.administered_by_id,
            "administered_by_name": self.administered_by.username if self.administered_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Medication(db.Model):
    """
    Medication Model - Drug database for prescriptions

    Stores information about medications available for prescription.
    This is essentially the drug database/formulary.
    """

    __tablename__ = "medication"

    id = db.Column(db.Integer, primary_key=True)

    # Drug Information
    drug_name = db.Column(db.String(200), nullable=False, unique=True)  # Generic name
    brand_names = db.Column(db.Text, nullable=True)  # Comma-separated brand names
    drug_class = db.Column(db.String(100), nullable=True)  # Antibiotic, NSAID, etc.
    controlled_substance = db.Column(db.Boolean, default=False, nullable=False)
    dea_schedule = db.Column(db.String(10), nullable=True)  # Schedule II, III, IV, V

    # Forms and Strengths
    available_forms = db.Column(db.Text, nullable=True)  # Tablet, Capsule, Liquid, Injectable
    strengths = db.Column(db.Text, nullable=True)  # e.g., "5mg, 10mg, 25mg"

    # Dosing Information
    typical_dose_cats = db.Column(db.Text, nullable=True)  # Typical dosage range for cats
    dosing_frequency = db.Column(db.String(100), nullable=True)  # Once daily, BID, TID, etc.
    route_of_administration = db.Column(db.String(50), nullable=True)  # PO, IV, SC, IM

    # Clinical Information
    indications = db.Column(db.Text, nullable=True)  # What it's used for
    contraindications = db.Column(db.Text, nullable=True)  # When not to use
    side_effects = db.Column(db.Text, nullable=True)  # Common side effects
    warnings = db.Column(db.Text, nullable=True)  # Special warnings

    # Inventory (optional)
    stock_quantity = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=0)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=True)

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Active in formulary

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    prescriptions = db.relationship("Prescription", back_populates="medication")

    def __repr__(self):
        return f"<Medication {self.drug_name}>"

    def to_dict(self):
        """Convert medication to dictionary for API responses"""
        return {
            "id": self.id,
            "drug_name": self.drug_name,
            "brand_names": self.brand_names,
            "drug_class": self.drug_class,
            "controlled_substance": self.controlled_substance,
            "dea_schedule": self.dea_schedule,
            "available_forms": self.available_forms,
            "strengths": self.strengths,
            "typical_dose_cats": self.typical_dose_cats,
            "dosing_frequency": self.dosing_frequency,
            "route_of_administration": self.route_of_administration,
            "indications": self.indications,
            "contraindications": self.contraindications,
            "side_effects": self.side_effects,
            "warnings": self.warnings,
            "stock_quantity": self.stock_quantity,
            "reorder_level": self.reorder_level,
            "unit_cost": float(self.unit_cost) if self.unit_cost else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Prescription(db.Model):
    """
    Prescription Model - Medication prescriptions for patients

    Links patients, visits, and medications with specific dosing instructions.
    """

    __tablename__ = "prescription"

    id = db.Column(db.Integer, primary_key=True)

    # Links
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey("visit.id"), nullable=True)
    medication_id = db.Column(db.Integer, db.ForeignKey("medication.id"), nullable=False)

    # Prescription Details
    dosage = db.Column(db.String(100), nullable=False)  # e.g., "5mg", "0.5ml"
    dosage_form = db.Column(db.String(50), nullable=True)  # Tablet, Capsule, Liquid
    frequency = db.Column(db.String(100), nullable=False)  # Once daily, BID, TID, QID, PRN
    route = db.Column(db.String(50), nullable=True)  # PO (oral), SC, IM, IV, Topical

    # Duration and Quantity
    duration_days = db.Column(db.Integer, nullable=True)  # How many days to take
    quantity = db.Column(db.Numeric(10, 2), nullable=False)  # Number of units (tablets, ml, etc.)
    refills_allowed = db.Column(db.Integer, default=0, nullable=False)
    refills_remaining = db.Column(db.Integer, default=0, nullable=False)

    # Instructions
    instructions = db.Column(db.Text, nullable=True)  # "Give with food", "Apply to affected area"
    indication = db.Column(db.Text, nullable=True)  # Why this medication was prescribed

    # Status
    status = db.Column(db.String(20), default="active")  # active, completed, discontinued, expired
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    discontinued_date = db.Column(db.Date, nullable=True)
    discontinuation_reason = db.Column(db.Text, nullable=True)

    # Prescriber
    prescribed_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    patient = db.relationship("Patient", backref="prescriptions")
    visit = db.relationship("Visit", back_populates="prescriptions")
    medication = db.relationship("Medication", back_populates="prescriptions")
    prescribed_by = db.relationship("User")

    def __repr__(self):
        med_name = self.medication.drug_name if self.medication else "Unknown"
        return f"<Prescription {self.id} - {med_name} for Patient {self.patient_id}>"

    def to_dict(self):
        """Convert prescription to dictionary for API responses"""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": self.patient.name if self.patient else None,
            "visit_id": self.visit_id,
            "medication_id": self.medication_id,
            "medication_name": self.medication.drug_name if self.medication else None,
            "dosage": self.dosage,
            "dosage_form": self.dosage_form,
            "frequency": self.frequency,
            "route": self.route,
            "duration_days": self.duration_days,
            "quantity": float(self.quantity) if self.quantity else None,
            "refills_allowed": self.refills_allowed,
            "refills_remaining": self.refills_remaining,
            "instructions": self.instructions,
            "indication": self.indication,
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "discontinued_date": self.discontinued_date.isoformat() if self.discontinued_date else None,
            "discontinuation_reason": self.discontinuation_reason,
            "prescribed_by_id": self.prescribed_by_id,
            "prescribed_by_name": self.prescribed_by.username if self.prescribed_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Service(db.Model):
    """
    Service Model - Catalog of billable services and products

    Used for creating invoice line items. Includes both services (exams, procedures)
    and products (medications, supplies) that can be billed to clients.
    """

    __tablename__ = "service"

    id = db.Column(db.Integer, primary_key=True)

    # Service Information
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)  # Exam, Surgery, Lab, Medication, Supply, etc.
    service_type = db.Column(db.String(50), nullable=False, default="service")  # service or product

    # Pricing
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    cost = db.Column(db.Numeric(10, 2), nullable=True)  # Cost to clinic (for margin calculation)
    taxable = db.Column(db.Boolean, default=True, nullable=False)

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Service {self.id} - {self.name}>"

    def to_dict(self):
        """Convert service to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "service_type": self.service_type,
            "unit_price": float(self.unit_price) if self.unit_price else 0.0,
            "cost": float(self.cost) if self.cost else None,
            "taxable": self.taxable,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Invoice(db.Model):
    """
    Invoice Model - Billing invoices for clients

    Tracks all charges for services rendered and products sold.
    Can be linked to visits or standalone.
    """

    __tablename__ = "invoice"

    id = db.Column(db.Integer, primary_key=True)

    # Links
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("visit.id"), nullable=True)

    # Invoice Details
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.Date, nullable=True)

    # Amounts
    subtotal = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), default=0.0, nullable=False)  # Percentage
    tax_amount = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    discount_amount = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    balance_due = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)

    # Status
    status = db.Column(
        db.String(20), default="draft", nullable=False
    )  # draft, sent, partial_paid, paid, overdue, cancelled

    # Notes
    notes = db.Column(db.Text, nullable=True)

    # Metadata
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = db.relationship("Client", backref="invoices")
    patient = db.relationship("Patient")
    visit = db.relationship("Visit")
    created_by = db.relationship("User")
    items = db.relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice {self.invoice_number} - Client {self.client_id}>"

    def to_dict(self):
        """Convert invoice to dictionary for API responses"""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "client_name": f"{self.client.first_name} {self.client.last_name}" if self.client else None,
            "patient_id": self.patient_id,
            "patient_name": self.patient.name if self.patient else None,
            "visit_id": self.visit_id,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "subtotal": float(self.subtotal) if self.subtotal else 0.0,
            "tax_rate": float(self.tax_rate) if self.tax_rate else 0.0,
            "tax_amount": float(self.tax_amount) if self.tax_amount else 0.0,
            "discount_amount": float(self.discount_amount) if self.discount_amount else 0.0,
            "total_amount": float(self.total_amount) if self.total_amount else 0.0,
            "amount_paid": float(self.amount_paid) if self.amount_paid else 0.0,
            "balance_due": float(self.balance_due) if self.balance_due else 0.0,
            "status": self.status,
            "notes": self.notes,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by.username if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InvoiceItem(db.Model):
    """
    Invoice Item Model - Line items on invoices

    Individual services or products billed on an invoice.
    """

    __tablename__ = "invoice_item"

    id = db.Column(db.Integer, primary_key=True)

    # Links
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"), nullable=True)  # Optional link to service catalog

    # Item Details
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1.0, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    taxable = db.Column(db.Boolean, default=True, nullable=False)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    invoice = db.relationship("Invoice", back_populates="items")
    service = db.relationship("Service")

    def __repr__(self):
        return f"<InvoiceItem {self.id} - {self.description}>"

    def to_dict(self):
        """Convert invoice item to dictionary for API responses"""
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "service_id": self.service_id,
            "service_name": self.service.name if self.service else None,
            "description": self.description,
            "quantity": float(self.quantity) if self.quantity else 1.0,
            "unit_price": float(self.unit_price) if self.unit_price else 0.0,
            "total_price": float(self.total_price) if self.total_price else 0.0,
            "taxable": self.taxable,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Payment(db.Model):
    """
    Payment Model - Payment records for invoices

    Tracks payments made against invoices. Supports partial payments.
    """

    __tablename__ = "payment"

    id = db.Column(db.Integer, primary_key=True)

    # Links
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)

    # Payment Details
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # cash, check, credit_card, debit_card, etc.
    reference_number = db.Column(db.String(100), nullable=True)  # Check number, transaction ID, etc.

    # Notes
    notes = db.Column(db.Text, nullable=True)

    # Metadata
    processed_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    invoice = db.relationship("Invoice", back_populates="payments")
    client = db.relationship("Client")
    processed_by = db.relationship("User")

    def __repr__(self):
        return f"<Payment {self.id} - Invoice {self.invoice_id} - ${self.amount}>"

    def to_dict(self):
        """Convert payment to dictionary for API responses"""
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice.invoice_number if self.invoice else None,
            "client_id": self.client_id,
            "client_name": f"{self.client.first_name} {self.client.last_name}" if self.client else None,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "amount": float(self.amount) if self.amount else 0.0,
            "payment_method": self.payment_method,
            "reference_number": self.reference_number,
            "notes": self.notes,
            "processed_by_id": self.processed_by_id,
            "processed_by_name": self.processed_by.username if self.processed_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# PHASE 3.1: INVENTORY MANAGEMENT
# ============================================================================


class Vendor(db.Model):
    """
    Vendor Model - Suppliers of medications, supplies, and products

    Stores vendor/supplier information for inventory management.
    """

    __tablename__ = "vendor"

    id = db.Column(db.Integer, primary_key=True)

    # Company Info
    company_name = db.Column(db.String(200), nullable=False)
    contact_name = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    fax = db.Column(db.String(20), nullable=True)
    website = db.Column(db.String(200), nullable=True)

    # Address
    address_line1 = db.Column(db.String(200), nullable=True)
    address_line2 = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), default="USA")

    # Account Info
    account_number = db.Column(db.String(100), nullable=True)
    payment_terms = db.Column(db.String(100), nullable=True)  # Net 30, Net 60, etc.
    tax_id = db.Column(db.String(50), nullable=True)

    # Settings
    preferred_vendor = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Notes
    notes = db.Column(db.Text, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    products = db.relationship("Product", back_populates="vendor", lazy=True)
    purchase_orders = db.relationship("PurchaseOrder", back_populates="vendor", lazy=True)

    def __repr__(self):
        return f"<Vendor {self.id} - {self.company_name}>"

    def to_dict(self):
        """Convert vendor to dictionary for API responses"""
        return {
            "id": self.id,
            "company_name": self.company_name,
            "contact_name": self.contact_name,
            "email": self.email,
            "phone": self.phone,
            "fax": self.fax,
            "website": self.website,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
            "account_number": self.account_number,
            "payment_terms": self.payment_terms,
            "tax_id": self.tax_id,
            "preferred_vendor": self.preferred_vendor,
            "is_active": self.is_active,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Product(db.Model):
    """
    Product Model - Inventory items (medications, supplies, retail products)

    Comprehensive inventory management for all types of products.
    Links to vendors and tracks stock levels.
    """

    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)

    # Basic Info
    name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=True)  # Stock Keeping Unit
    description = db.Column(db.Text, nullable=True)

    # Categorization
    product_type = db.Column(db.String(50), nullable=False)  # medication, supply, equipment, retail
    category = db.Column(db.String(100), nullable=True)  # Surgical, Diagnostic, Food, Toys, etc.

    # Vendor Info
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendor.id"), nullable=True)
    vendor_sku = db.Column(db.String(100), nullable=True)  # Vendor's product code

    # Inventory Tracking
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    reorder_level = db.Column(db.Integer, default=0, nullable=False)  # Minimum stock before reorder
    reorder_quantity = db.Column(db.Integer, default=0, nullable=False)  # How many to order
    unit_of_measure = db.Column(db.String(50), default="each")  # each, box, case, bottle, etc.

    # Pricing
    unit_cost = db.Column(db.Numeric(10, 2), nullable=True)  # What we pay
    unit_price = db.Column(db.Numeric(10, 2), nullable=True)  # What we charge
    markup_percentage = db.Column(db.Numeric(5, 2), nullable=True)

    # Product Details
    manufacturer = db.Column(db.String(200), nullable=True)
    lot_number = db.Column(db.String(100), nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    storage_location = db.Column(db.String(100), nullable=True)  # Shelf A, Refrigerator, etc.

    # Flags
    requires_prescription = db.Column(db.Boolean, default=False)
    controlled_substance = db.Column(db.Boolean, default=False)
    taxable = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Notes
    notes = db.Column(db.Text, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vendor = db.relationship("Vendor", back_populates="products")
    transactions = db.relationship("InventoryTransaction", back_populates="product", lazy=True)

    def __repr__(self):
        return f"<Product {self.id} - {self.name} (Stock: {self.stock_quantity})>"

    @property
    def needs_reorder(self):
        """Check if product stock is below reorder level"""
        return self.stock_quantity <= self.reorder_level

    @property
    def is_out_of_stock(self):
        """Check if product is out of stock"""
        return self.stock_quantity <= 0

    @property
    def stock_value(self):
        """Calculate total value of stock on hand"""
        if self.unit_cost and self.stock_quantity:
            return float(self.unit_cost) * self.stock_quantity
        return 0.0

    def to_dict(self):
        """Convert product to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "sku": self.sku,
            "description": self.description,
            "product_type": self.product_type,
            "category": self.category,
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor.company_name if self.vendor else None,
            "vendor_sku": self.vendor_sku,
            "stock_quantity": self.stock_quantity,
            "reorder_level": self.reorder_level,
            "reorder_quantity": self.reorder_quantity,
            "unit_of_measure": self.unit_of_measure,
            "unit_cost": float(self.unit_cost) if self.unit_cost else None,
            "unit_price": float(self.unit_price) if self.unit_price else None,
            "markup_percentage": float(self.markup_percentage) if self.markup_percentage else None,
            "manufacturer": self.manufacturer,
            "lot_number": self.lot_number,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "storage_location": self.storage_location,
            "requires_prescription": self.requires_prescription,
            "controlled_substance": self.controlled_substance,
            "taxable": self.taxable,
            "is_active": self.is_active,
            "notes": self.notes,
            "needs_reorder": self.needs_reorder,
            "is_out_of_stock": self.is_out_of_stock,
            "stock_value": self.stock_value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PurchaseOrder(db.Model):
    """
    Purchase Order Model - Orders to vendors

    Tracks purchase orders for inventory replenishment.
    """

    __tablename__ = "purchase_order"

    id = db.Column(db.Integer, primary_key=True)

    # Order Info
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendor.id"), nullable=False)
    order_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    expected_delivery_date = db.Column(db.Date, nullable=True)
    actual_delivery_date = db.Column(db.Date, nullable=True)

    # Status
    status = db.Column(
        db.String(20), nullable=False, default="draft"
    )  # draft, submitted, received, partially_received, cancelled

    # Amounts
    subtotal = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    tax = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    shipping = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)

    # Notes
    notes = db.Column(db.Text, nullable=True)
    shipping_address = db.Column(db.Text, nullable=True)

    # Metadata
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    received_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vendor = db.relationship("Vendor", back_populates="purchase_orders")
    items = db.relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    received_by = db.relationship("User", foreign_keys=[received_by_id])

    def __repr__(self):
        return f"<PurchaseOrder {self.po_number} - {self.vendor.company_name if self.vendor else 'N/A'}>"

    def to_dict(self):
        """Convert purchase order to dictionary for API responses"""
        return {
            "id": self.id,
            "po_number": self.po_number,
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor.company_name if self.vendor else None,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "expected_delivery_date": self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            "actual_delivery_date": self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            "status": self.status,
            "subtotal": float(self.subtotal) if self.subtotal else 0.0,
            "tax": float(self.tax) if self.tax else 0.0,
            "shipping": float(self.shipping) if self.shipping else 0.0,
            "total_amount": float(self.total_amount) if self.total_amount else 0.0,
            "notes": self.notes,
            "shipping_address": self.shipping_address,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by.username if self.created_by else None,
            "received_by_id": self.received_by_id,
            "received_by_name": self.received_by.username if self.received_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "items": [item.to_dict() for item in self.items] if self.items else [],
        }


class PurchaseOrderItem(db.Model):
    """
    Purchase Order Item Model - Line items for purchase orders

    Individual products and quantities on a purchase order.
    """

    __tablename__ = "purchase_order_item"

    id = db.Column(db.Integer, primary_key=True)

    # Links
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

    # Order Details
    quantity_ordered = db.Column(db.Integer, nullable=False)
    quantity_received = db.Column(db.Integer, default=0, nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=False)
    total_cost = db.Column(db.Numeric(10, 2), nullable=False)

    # Notes
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    purchase_order = db.relationship("PurchaseOrder", back_populates="items")
    product = db.relationship("Product")

    def __repr__(self):
        return (
            f"<PurchaseOrderItem {self.id} - {self.product.name if self.product else 'N/A'} x{self.quantity_ordered}>"
        )

    def to_dict(self):
        """Convert purchase order item to dictionary for API responses"""
        return {
            "id": self.id,
            "purchase_order_id": self.purchase_order_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "quantity_ordered": self.quantity_ordered,
            "quantity_received": self.quantity_received,
            "unit_cost": float(self.unit_cost) if self.unit_cost else 0.0,
            "total_cost": float(self.total_cost) if self.total_cost else 0.0,
            "notes": self.notes,
        }


class InventoryTransaction(db.Model):
    """
    Inventory Transaction Model - Track all inventory movements

    Records all changes to inventory levels for audit trail.
    """

    __tablename__ = "inventory_transaction"

    id = db.Column(db.Integer, primary_key=True)

    # Links
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_order.id"), nullable=True)

    # Transaction Details
    transaction_type = db.Column(
        db.String(50), nullable=False
    )  # received, dispensed, adjustment, return, expired, damaged
    quantity = db.Column(db.Integer, nullable=False)  # Positive for increase, negative for decrease
    quantity_before = db.Column(db.Integer, nullable=False)
    quantity_after = db.Column(db.Integer, nullable=False)

    # Additional Info
    reason = db.Column(db.String(200), nullable=True)
    reference_number = db.Column(db.String(100), nullable=True)  # Invoice #, PO #, etc.
    notes = db.Column(db.Text, nullable=True)

    # Metadata
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    performed_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Relationships
    product = db.relationship("Product", back_populates="transactions")
    purchase_order = db.relationship("PurchaseOrder")
    performed_by = db.relationship("User")

    def __repr__(self):
        product_name = self.product.name if self.product else "N/A"
        return f"<InventoryTransaction {self.id} - {product_name} {self.transaction_type} {self.quantity}>"

    def to_dict(self):
        """Convert inventory transaction to dictionary for API responses"""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "purchase_order_id": self.purchase_order_id,
            "transaction_type": self.transaction_type,
            "quantity": self.quantity,
            "quantity_before": self.quantity_before,
            "quantity_after": self.quantity_after,
            "reason": self.reason,
            "reference_number": self.reference_number,
            "notes": self.notes,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "performed_by_id": self.performed_by_id,
            "performed_by_name": self.performed_by.username if self.performed_by else None,
        }


class Staff(db.Model):
    """
    Staff Model

    Extended staff information beyond basic User model.
    Includes employment details, contact info, certifications, and scheduling.
    """

    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)

    # Link to User account
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, unique=True)

    # Personal Information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)

    # Employment Details
    position = db.Column(db.String(100), nullable=False)  # Veterinarian, Vet Tech, Receptionist, etc.
    department = db.Column(db.String(100), nullable=True)  # Surgery, Front Desk, Pharmacy, etc.
    employment_type = db.Column(db.String(50), nullable=False, default="full-time")  # full-time, part-time, contract
    hire_date = db.Column(db.Date, nullable=False)
    termination_date = db.Column(db.Date, nullable=True)

    # Credentials & Certifications
    license_number = db.Column(db.String(100), nullable=True)
    license_state = db.Column(db.String(50), nullable=True)
    license_expiry = db.Column(db.Date, nullable=True)
    certifications = db.Column(db.Text, nullable=True)  # JSON or comma-separated list
    education = db.Column(db.Text, nullable=True)

    # Work Schedule
    default_schedule = db.Column(db.String(200), nullable=True)  # e.g., "Mon-Fri 9-5"
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=True)

    # Permissions & Access
    can_prescribe = db.Column(db.Boolean, default=False)
    can_perform_surgery = db.Column(db.Boolean, default=False)
    can_access_billing = db.Column(db.Boolean, default=False)

    # Notes
    notes = db.Column(db.Text, nullable=True)

    # Metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship("User", backref="staff_profile", uselist=False)
    schedules = db.relationship("Schedule", back_populates="staff_member", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Staff {self.first_name} {self.last_name} - {self.position}>"

    def to_dict(self):
        """Convert staff to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": f"{self.first_name} {self.last_name}",
            "email": self.email,
            "phone": self.phone,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "position": self.position,
            "department": self.department,
            "employment_type": self.employment_type,
            "hire_date": self.hire_date.isoformat() if self.hire_date else None,
            "termination_date": self.termination_date.isoformat() if self.termination_date else None,
            "license_number": self.license_number,
            "license_state": self.license_state,
            "license_expiry": self.license_expiry.isoformat() if self.license_expiry else None,
            "certifications": self.certifications,
            "education": self.education,
            "default_schedule": self.default_schedule,
            "hourly_rate": float(self.hourly_rate) if self.hourly_rate else None,
            "can_prescribe": self.can_prescribe,
            "can_perform_surgery": self.can_perform_surgery,
            "can_access_billing": self.can_access_billing,
            "notes": self.notes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Schedule(db.Model):
    """
    Schedule/Shift Model

    Tracks staff work schedules and shifts.
    Supports recurring schedules and one-off shifts.
    """

    __tablename__ = "schedule"

    id = db.Column(db.Integer, primary_key=True)

    # Staff Assignment
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=False)

    # Schedule Details
    shift_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    # Shift Type & Status
    shift_type = db.Column(db.String(50), nullable=False, default="regular")  # regular, on-call, overtime
    status = db.Column(db.String(50), nullable=False, default="scheduled")  # scheduled, completed, cancelled, no-show

    # Break Information
    break_minutes = db.Column(db.Integer, default=30)  # Total break time in minutes

    # Location & Role
    location = db.Column(db.String(100), nullable=True)  # Clinic location if multiple sites
    role = db.Column(db.String(100), nullable=True)  # Role for this shift if different from default

    # Time Off / Leave
    is_time_off = db.Column(db.Boolean, default=False)
    time_off_type = db.Column(db.String(50), nullable=True)  # vacation, sick, personal, unpaid
    time_off_approved = db.Column(db.Boolean, default=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    # Notes
    notes = db.Column(db.Text, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    staff_member = db.relationship("Staff", back_populates="schedules")
    approved_by = db.relationship("User", foreign_keys=[approved_by_id])

    def __repr__(self):
        staff_name = f"{self.staff_member.first_name} {self.staff_member.last_name}" if self.staff_member else "N/A"
        return f"<Schedule {staff_name} on {self.shift_date}>"

    def to_dict(self):
        """Convert schedule to dictionary for API responses"""
        return {
            "id": self.id,
            "staff_id": self.staff_id,
            "staff_name": f"{self.staff_member.first_name} {self.staff_member.last_name}" if self.staff_member else None,
            "staff_position": self.staff_member.position if self.staff_member else None,
            "shift_date": self.shift_date.isoformat() if self.shift_date else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "shift_type": self.shift_type,
            "status": self.status,
            "break_minutes": self.break_minutes,
            "location": self.location,
            "role": self.role,
            "is_time_off": self.is_time_off,
            "time_off_type": self.time_off_type,
            "time_off_approved": self.time_off_approved,
            "approved_by_id": self.approved_by_id,
            "approved_by_name": self.approved_by.username if self.approved_by else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LabTest(db.Model):
    """
    Laboratory Test Model

    Catalog of available laboratory tests that can be ordered.
    Includes test details, normal ranges, and pricing.
    """

    __tablename__ = "lab_test"

    id = db.Column(db.Integer, primary_key=True)

    # Test Information
    test_code = db.Column(db.String(50), unique=True, nullable=False)  # e.g., CBC, CHEM, T4
    test_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # Hematology, Chemistry, Serology, etc.
    description = db.Column(db.Text, nullable=True)

    # Specimen Requirements
    specimen_type = db.Column(db.String(100), nullable=True)  # Blood, Urine, Fecal, etc.
    specimen_volume = db.Column(db.String(50), nullable=True)  # e.g., "2-5 ml"
    collection_instructions = db.Column(db.Text, nullable=True)

    # Reference Range (stored as JSON string for flexibility)
    reference_range = db.Column(db.Text, nullable=True)  # JSON: {"cat": {"min": 0, "max": 10, "unit": "mg/dL"}}

    # Turnaround Time
    turnaround_time = db.Column(db.String(100), nullable=True)  # e.g., "24 hours", "2-3 days"

    # External Lab Information
    external_lab = db.Column(db.Boolean, default=False)
    external_lab_name = db.Column(db.String(200), nullable=True)
    external_lab_code = db.Column(db.String(100), nullable=True)

    # Pricing
    cost = db.Column(db.Numeric(10, 2), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=True)

    # Metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    results = db.relationship("LabResult", back_populates="test", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LabTest {self.test_code} - {self.test_name}>"

    def to_dict(self):
        """Convert lab test to dictionary for API responses"""
        return {
            "id": self.id,
            "test_code": self.test_code,
            "test_name": self.test_name,
            "category": self.category,
            "description": self.description,
            "specimen_type": self.specimen_type,
            "specimen_volume": self.specimen_volume,
            "collection_instructions": self.collection_instructions,
            "reference_range": self.reference_range,
            "turnaround_time": self.turnaround_time,
            "external_lab": self.external_lab,
            "external_lab_name": self.external_lab_name,
            "external_lab_code": self.external_lab_code,
            "cost": float(self.cost) if self.cost else None,
            "price": float(self.price) if self.price else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LabResult(db.Model):
    """
    Laboratory Result Model

    Individual test results for patients.
    Links to visits and tracks result status, values, and abnormal flags.
    """

    __tablename__ = "lab_result"

    id = db.Column(db.Integer, primary_key=True)

    # Associations
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey("visit.id"), nullable=True)
    test_id = db.Column(db.Integer, db.ForeignKey("lab_test.id"), nullable=False)

    # Order Information
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ordered_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Status Tracking
    status = db.Column(db.String(50), nullable=False, default="pending")  # pending, in_progress, completed, cancelled

    # Result Information
    result_date = db.Column(db.DateTime, nullable=True)
    result_value = db.Column(db.Text, nullable=True)  # Can be numeric, text, or JSON for complex results
    result_unit = db.Column(db.String(50), nullable=True)

    # Interpretation
    is_abnormal = db.Column(db.Boolean, default=False)
    abnormal_flag = db.Column(db.String(10), nullable=True)  # H (High), L (Low), A (Abnormal)
    interpretation = db.Column(db.Text, nullable=True)

    # External Lab Tracking
    external_reference_number = db.Column(db.String(100), nullable=True)

    # Reviewed Status
    reviewed = db.Column(db.Boolean, default=False)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    reviewed_date = db.Column(db.DateTime, nullable=True)

    # Notes
    notes = db.Column(db.Text, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    patient = db.relationship("Patient", backref="lab_results")
    visit = db.relationship("Visit", backref="lab_results")
    test = db.relationship("LabTest", back_populates="results")
    ordered_by = db.relationship("User", foreign_keys=[ordered_by_id], backref="ordered_lab_tests")
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id], backref="reviewed_lab_tests")

    def __repr__(self):
        return f"<LabResult {self.id} - {self.test.test_name if self.test else 'N/A'} - {self.status}>"

    def to_dict(self):
        """Convert lab result to dictionary for API responses"""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": f"{self.patient.name}" if self.patient else None,
            "visit_id": self.visit_id,
            "test_id": self.test_id,
            "test_code": self.test.test_code if self.test else None,
            "test_name": self.test.test_name if self.test else None,
            "test_category": self.test.category if self.test else None,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "ordered_by_id": self.ordered_by_id,
            "ordered_by_name": self.ordered_by.username if self.ordered_by else None,
            "status": self.status,
            "result_date": self.result_date.isoformat() if self.result_date else None,
            "result_value": self.result_value,
            "result_unit": self.result_unit,
            "is_abnormal": self.is_abnormal,
            "abnormal_flag": self.abnormal_flag,
            "interpretation": self.interpretation,
            "external_reference_number": self.external_reference_number,
            "reviewed": self.reviewed,
            "reviewed_by_id": self.reviewed_by_id,
            "reviewed_by_name": self.reviewed_by.username if self.reviewed_by else None,
            "reviewed_date": self.reviewed_date.isoformat() if self.reviewed_date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# NOTIFICATION & REMINDER MODELS
# ============================================================================


class NotificationTemplate(db.Model):
    """Notification Template Model - Email and SMS templates"""

    __tablename__ = "notification_template"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    # Template Type
    template_type = db.Column(
        db.String(50), nullable=False
    )  # appointment_reminder, vaccination_reminder, etc.
    channel = db.Column(
        db.String(20), nullable=False
    )  # email, sms, both

    # Template Content
    subject = db.Column(db.String(200), nullable=True)  # For email
    body = db.Column(db.Text, nullable=False)

    # Template Variables (JSON format - list of available variables)
    # Example: ["client_name", "pet_name", "appointment_date", "appointment_time"]
    variables = db.Column(db.Text, nullable=True)

    # Settings
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(
        db.Boolean, default=False
    )  # Default template for this type

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now
    )
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    # Relationships
    created_by = db.relationship("User", backref="notification_templates")

    def to_dict(self):
        """Convert to dictionary"""
        import json

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type,
            "channel": self.channel,
            "subject": self.subject,
            "body": self.body,
            "variables": (
                json.loads(self.variables) if self.variables else []
            ),
            "is_active": self.is_active,
            "is_default": self.is_default,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
            "created_by": (
                self.created_by.username if self.created_by else None
            ),
        }


class ClientCommunicationPreference(db.Model):
    """Client Communication Preference Model - How clients want to be contacted"""

    __tablename__ = "client_communication_preference"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.Integer, db.ForeignKey("client.id"), nullable=False, unique=True
    )

    # Communication Channels
    email_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=False)
    phone_enabled = db.Column(db.Boolean, default=True)

    # Notification Types
    appointment_reminders = db.Column(db.Boolean, default=True)
    vaccination_reminders = db.Column(db.Boolean, default=True)
    medication_reminders = db.Column(db.Boolean, default=True)
    marketing = db.Column(db.Boolean, default=False)
    newsletters = db.Column(db.Boolean, default=False)

    # Preferred Times
    preferred_contact_time = db.Column(
        db.String(50), nullable=True
    )  # morning, afternoon, evening
    do_not_contact_before = db.Column(db.Time, nullable=True)
    do_not_contact_after = db.Column(db.Time, nullable=True)

    # Reminder Timing
    appointment_reminder_days = db.Column(
        db.Integer, default=1
    )  # Days before appointment
    vaccination_reminder_days = db.Column(
        db.Integer, default=7
    )  # Days before due

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    client = db.relationship("Client", backref="communication_preference")

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "email_enabled": self.email_enabled,
            "sms_enabled": self.sms_enabled,
            "phone_enabled": self.phone_enabled,
            "appointment_reminders": self.appointment_reminders,
            "vaccination_reminders": self.vaccination_reminders,
            "medication_reminders": self.medication_reminders,
            "marketing": self.marketing,
            "newsletters": self.newsletters,
            "preferred_contact_time": self.preferred_contact_time,
            "do_not_contact_before": (
                self.do_not_contact_before.isoformat()
                if self.do_not_contact_before
                else None
            ),
            "do_not_contact_after": (
                self.do_not_contact_after.isoformat()
                if self.do_not_contact_after
                else None
            ),
            "appointment_reminder_days": self.appointment_reminder_days,
            "vaccination_reminder_days": self.vaccination_reminder_days,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
        }


class Reminder(db.Model):
    """Reminder Model - Tracks reminders to be sent"""

    __tablename__ = "reminder"

    id = db.Column(db.Integer, primary_key=True)

    # Related Records
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    patient_id = db.Column(
        db.Integer, db.ForeignKey("patient.id"), nullable=True
    )  # Optional
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointment.id"), nullable=True
    )  # For appointment reminders

    # Reminder Type
    reminder_type = db.Column(
        db.String(50), nullable=False
    )  # appointment, vaccination, medication, checkup, etc.

    # Scheduling
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.Time, nullable=True)
    send_at = db.Column(
        db.DateTime, nullable=False
    )  # Exact datetime to send

    # Delivery
    delivery_method = db.Column(
        db.String(20), nullable=False
    )  # email, sms, both
    status = db.Column(
        db.String(20), nullable=False, default="pending"
    )  # pending, sent, failed, cancelled

    # Template
    template_id = db.Column(
        db.Integer, db.ForeignKey("notification_template.id"), nullable=True
    )

    # Message Content (can override template)
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)

    # Delivery Tracking
    sent_at = db.Column(db.DateTime, nullable=True)
    failed_at = db.Column(db.DateTime, nullable=True)
    failure_reason = db.Column(db.Text, nullable=True)

    # Retry Logic
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)

    # Metadata
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now
    )
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    # Relationships
    client = db.relationship("Client", backref="reminders")
    patient = db.relationship("Patient", backref="reminders")
    appointment = db.relationship("Appointment", backref="reminders")
    template = db.relationship("NotificationTemplate", backref="reminders")
    created_by = db.relationship("User", backref="reminders_created")

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "client_name": self.client.name if self.client else None,
            "patient_id": self.patient_id,
            "patient_name": self.patient.name if self.patient else None,
            "appointment_id": self.appointment_id,
            "reminder_type": self.reminder_type,
            "scheduled_date": (
                self.scheduled_date.isoformat() if self.scheduled_date else None
            ),
            "scheduled_time": (
                self.scheduled_time.isoformat() if self.scheduled_time else None
            ),
            "send_at": self.send_at.isoformat() if self.send_at else None,
            "delivery_method": self.delivery_method,
            "status": self.status,
            "template_id": self.template_id,
            "template_name": self.template.name if self.template else None,
            "subject": self.subject,
            "message": self.message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "failure_reason": self.failure_reason,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "notes": self.notes,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
            "created_by": (
                self.created_by.username if self.created_by else None
            ),
        }


# ============================================================================
# CLIENT PORTAL MODELS
# ============================================================================


class ClientPortalUser(db.Model):
    """Client Portal User Model - Separate authentication for client portal"""

    __tablename__ = "client_portal_user"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.Integer, db.ForeignKey("client.id"), nullable=False, unique=True
    )

    # Authentication
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Security
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(
        db.Boolean, default=False
    )  # Email verification status
    verification_token = db.Column(db.String(100), nullable=True)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    # Login tracking
    last_login = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime, nullable=True)

    # PIN and session management
    pin_hash = db.Column(db.String(128), nullable=True)
    last_activity_at = db.Column(db.DateTime, nullable=True)
    session_expires_at = db.Column(db.DateTime, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    client = db.relationship("Client", backref="portal_user")

    def set_password(self, password):
        """Set password hash using bcrypt (standardized with staff users)"""
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def check_password(self, password):
        """Check password against hash"""
        # Support both bcrypt and legacy Werkzeug hashes for migration
        password_bytes = password.encode("utf-8")
        hash_bytes = self.password_hash.encode("utf-8")

        # Try bcrypt first (new format)
        try:
            if bcrypt.checkpw(password_bytes, hash_bytes):
                return True
        except (ValueError, AttributeError):
            pass

        # Fallback to Werkzeug for legacy hashes (migration support)
        try:
            from werkzeug.security import check_password_hash

            if check_password_hash(self.password_hash, password):
                # Auto-migrate to bcrypt on successful login
                self.set_password(password)
                db.session.commit()
                return True
        except Exception:
            pass

        return False

    def set_pin(self, pin):
        """Set PIN hash using bcrypt (4-6 digit PIN)"""
        if not pin or not pin.isdigit() or len(pin) < 4 or len(pin) > 6:
            raise ValueError("PIN must be 4-6 digits")
        self.pin_hash = bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def check_pin(self, pin):
        """Verify PIN against hash"""
        if not self.pin_hash or not pin:
            return False
        try:
            return bcrypt.checkpw(pin.encode("utf-8"), self.pin_hash.encode("utf-8"))
        except Exception:
            return False

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "last_login": (
                self.last_login.isoformat() if self.last_login else None
            ),
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
        }


class AppointmentRequest(db.Model):
    """Appointment Request Model - Online appointment requests from client portal"""

    __tablename__ = "appointment_request"

    id = db.Column(db.Integer, primary_key=True)

    # Related Records
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    patient_id = db.Column(
        db.Integer, db.ForeignKey("patient.id"), nullable=False
    )
    appointment_type_id = db.Column(
        db.Integer, db.ForeignKey("appointment_type.id"), nullable=True
    )

    # Request Details
    requested_date = db.Column(db.Date, nullable=False)
    requested_time = db.Column(
        db.String(20), nullable=True
    )  # "morning", "afternoon", "evening", or specific time
    alternate_date_1 = db.Column(db.Date, nullable=True)
    alternate_date_2 = db.Column(db.Date, nullable=True)

    # Reason
    reason = db.Column(db.Text, nullable=False)
    is_urgent = db.Column(db.Boolean, default=False)

    # Status
    status = db.Column(
        db.String(20), nullable=False, default="pending"
    )  # pending, approved, rejected, scheduled
    priority = db.Column(
        db.String(20), nullable=False, default="normal"
    )  # low, normal, high, urgent

    # Staff Response
    reviewed_by_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)
    staff_notes = db.Column(db.Text, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    # Scheduled Appointment (if approved)
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointment.id"), nullable=True
    )

    # Metadata
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    client = db.relationship("Client", backref="appointment_requests")
    patient = db.relationship("Patient", backref="appointment_requests")
    appointment_type = db.relationship("AppointmentType", backref="requests")
    reviewed_by = db.relationship("User", backref="appointment_requests_reviewed")
    appointment = db.relationship("Appointment", backref="request")

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "client_name": f"{self.client.first_name} {self.client.last_name}" if self.client else None,
            "patient_id": self.patient_id,
            "patient_name": self.patient.name if self.patient else None,
            "appointment_type_id": self.appointment_type_id,
            "appointment_type_name": (
                self.appointment_type.name if self.appointment_type else None
            ),
            "requested_date": (
                self.requested_date.isoformat() if self.requested_date else None
            ),
            "requested_time": self.requested_time,
            "alternate_date_1": (
                self.alternate_date_1.isoformat()
                if self.alternate_date_1
                else None
            ),
            "alternate_date_2": (
                self.alternate_date_2.isoformat()
                if self.alternate_date_2
                else None
            ),
            "reason": self.reason,
            "is_urgent": self.is_urgent,
            "status": self.status,
            "priority": self.priority,
            "reviewed_by_id": self.reviewed_by_id,
            "reviewed_by_name": (
                self.reviewed_by.username if self.reviewed_by else None
            ),
            "reviewed_at": (
                self.reviewed_at.isoformat() if self.reviewed_at else None
            ),
            "staff_notes": self.staff_notes,
            "rejection_reason": self.rejection_reason,
            "appointment_id": self.appointment_id,
            "notes": self.notes,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
        }


class Document(db.Model):
    """
    Document Model - Stores documents related to patients, visits, and clients

    Supports various document types including medical records, consent forms,
    lab results, images, and general documents. Documents can be linked to
    patients, visits, or clients.
    """

    __tablename__ = "document"

    id = db.Column(db.Integer, primary_key=True)

    # File Information
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(100), nullable=False)  # MIME type (e.g., application/pdf, image/jpeg)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes

    # Document Classification
    category = db.Column(
        db.String(50), nullable=False, default="general"
    )  # general, medical_record, lab_result, imaging, consent_form, vaccination_record, other
    tags = db.Column(db.Text, nullable=True)  # Comma-separated tags for additional categorization
    description = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Consent Form Fields
    is_consent_form = db.Column(db.Boolean, default=False)
    consent_type = db.Column(db.String(100), nullable=True)  # e.g., surgery, anesthesia, treatment, general
    signed_date = db.Column(db.DateTime, nullable=True)

    # Relationships (can belong to patient, visit, or client)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("visit.id"), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_archived = db.Column(db.Boolean, default=False)

    # Relationships
    patient = db.relationship("Patient", backref="documents")
    visit = db.relationship("Visit", backref="documents")
    client = db.relationship("Client", backref="documents")
    uploaded_by = db.relationship("User", backref="documents_uploaded")

    def __repr__(self):
        return f"<Document {self.id} - {self.original_filename}>"

    def to_dict(self):
        """Convert document to dictionary for API responses"""
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "file_size_mb": round(self.file_size / (1024 * 1024), 2),
            "category": self.category,
            "tags": self.tags.split(",") if self.tags else [],
            "description": self.description,
            "notes": self.notes,
            "is_consent_form": self.is_consent_form,
            "consent_type": self.consent_type,
            "signed_date": self.signed_date.isoformat() if self.signed_date else None,
            "patient_id": self.patient_id,
            "patient_name": self.patient.name if self.patient else None,
            "visit_id": self.visit_id,
            "client_id": self.client_id,
            "client_name": (
                f"{self.client.first_name} {self.client.last_name}" if self.client else None
            ),
            "uploaded_by_id": self.uploaded_by_id,
            "uploaded_by_name": self.uploaded_by.username if self.uploaded_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_archived": self.is_archived,
        }
