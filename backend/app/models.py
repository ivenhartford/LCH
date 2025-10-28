from . import db
import bcrypt
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(80), nullable=False, default="user")

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def check_password(self, password):
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))


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


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)

    def __repr__(self):
        return f"<Appointment {self.title}>"


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
        med_name = self.medication.drug_name if self.medication else 'Unknown'
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
    Service Model - Catalog of services and products for billing

    This is the master catalog of all billable items including:
    - Medical services (exams, procedures, surgeries)
    - Laboratory tests
    - Products (medications, supplies, retail items)
    """

    __tablename__ = "service"

    id = db.Column(db.Integer, primary_key=True)

    # Service Information
    code = db.Column(db.String(50), unique=True, nullable=False)  # Internal service code
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Category
    category = db.Column(
        db.String(50), nullable=False
    )  # Service, Procedure, Lab, Medication, Supply, Retail

    # Pricing
    default_price = db.Column(db.Numeric(10, 2), nullable=False)
    cost = db.Column(db.Numeric(10, 2), nullable=True)  # Cost to clinic

    # Tax
    taxable = db.Column(db.Boolean, default=True, nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), default=0.00)  # Default tax rate (e.g., 8.5 for 8.5%)

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Service {self.code} - {self.name}>"

    def to_dict(self):
        """Convert service to dictionary for API responses"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "default_price": float(self.default_price) if self.default_price else 0.0,
            "cost": float(self.cost) if self.cost else None,
            "taxable": self.taxable,
            "tax_rate": float(self.tax_rate) if self.tax_rate else 0.0,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Invoice(db.Model):
    """
    Invoice Model - Billing invoices for services rendered

    Invoices are linked to patients, clients, and optionally visits.
    """

    __tablename__ = "invoice"

    id = db.Column(db.Integer, primary_key=True)

    # Invoice Number (auto-generated)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)

    # Links
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey("visit.id"), nullable=True)

    # Invoice Details
    invoice_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.Date, nullable=True)

    # Amounts
    subtotal = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    discount_amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    balance_due = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)

    # Status
    status = db.Column(
        db.String(20), default="draft", nullable=False
    )  # draft, issued, partially_paid, paid, overdue, cancelled

    # Notes
    notes = db.Column(db.Text, nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)

    # Metadata
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    patient = db.relationship("Patient", backref="invoices")
    client = db.relationship("Client", backref="invoices")
    visit = db.relationship("Visit", backref="invoices")
    created_by = db.relationship("User")
    items = db.relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice {self.invoice_number} - {self.status}>"

    def to_dict(self, include_items=False, include_payments=False):
        """Convert invoice to dictionary for API responses"""
        data = {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "patient_id": self.patient_id,
            "patient_name": self.patient.name if self.patient else None,
            "client_id": self.client_id,
            "client_name": f"{self.client.first_name} {self.client.last_name}" if self.client else None,
            "visit_id": self.visit_id,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "subtotal": float(self.subtotal) if self.subtotal else 0.0,
            "tax_amount": float(self.tax_amount) if self.tax_amount else 0.0,
            "discount_amount": float(self.discount_amount) if self.discount_amount else 0.0,
            "total_amount": float(self.total_amount) if self.total_amount else 0.0,
            "amount_paid": float(self.amount_paid) if self.amount_paid else 0.0,
            "balance_due": float(self.balance_due) if self.balance_due else 0.0,
            "status": self.status,
            "notes": self.notes,
            "internal_notes": self.internal_notes,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by.username if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_items:
            data["items"] = [item.to_dict() for item in self.items]

        if include_payments:
            data["payments"] = [payment.to_dict() for payment in self.payments]

        return data

    def calculate_totals(self):
        """Recalculate invoice totals based on line items"""
        subtotal = sum(float(item.line_total) for item in self.items)
        tax_amount = sum(float(item.tax_amount) for item in self.items)

        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.total_amount = subtotal + tax_amount - float(self.discount_amount or 0)
        self.balance_due = float(self.total_amount) - float(self.amount_paid or 0)

        # Update status based on payment
        if self.balance_due <= 0:
            self.status = "paid"
        elif self.amount_paid > 0:
            self.status = "partially_paid"
        elif self.status == "draft":
            self.status = "issued"


class InvoiceItem(db.Model):
    """
    Invoice Item Model - Line items on invoices

    Each line item represents a service or product with quantity and price.
    """

    __tablename__ = "invoice_item"

    id = db.Column(db.Integer, primary_key=True)

    # Links
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"), nullable=True)  # Link to service catalog

    # Item Details
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1.00, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    # Tax
    taxable = db.Column(db.Boolean, default=True, nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), default=0.00)
    tax_amount = db.Column(db.Numeric(10, 2), default=0.00)

    # Totals
    line_total = db.Column(db.Numeric(10, 2), nullable=False)  # quantity * unit_price

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    invoice = db.relationship("Invoice", back_populates="items")
    service = db.relationship("Service")

    def __repr__(self):
        return f"<InvoiceItem {self.description} - ${self.line_total}>"

    def to_dict(self):
        """Convert invoice item to dictionary for API responses"""
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "service_id": self.service_id,
            "service_code": self.service.code if self.service else None,
            "description": self.description,
            "quantity": float(self.quantity) if self.quantity else 1.0,
            "unit_price": float(self.unit_price) if self.unit_price else 0.0,
            "taxable": self.taxable,
            "tax_rate": float(self.tax_rate) if self.tax_rate else 0.0,
            "tax_amount": float(self.tax_amount) if self.tax_amount else 0.0,
            "line_total": float(self.line_total) if self.line_total else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def calculate_totals(self):
        """Calculate line item totals including tax"""
        self.line_total = float(self.quantity) * float(self.unit_price)

        if self.taxable and self.tax_rate:
            self.tax_amount = (float(self.line_total) * float(self.tax_rate)) / 100
        else:
            self.tax_amount = 0.00


class Payment(db.Model):
    """
    Payment Model - Payment records for invoices

    Tracks all payments made against invoices.
    """

    __tablename__ = "payment"

    id = db.Column(db.Integer, primary_key=True)

    # Links
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)

    # Payment Details
    payment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(
        db.String(50), nullable=False
    )  # Cash, Check, Credit Card, Debit Card, Bank Transfer, Other

    # Payment Method Details
    reference_number = db.Column(db.String(100), nullable=True)  # Check number, transaction ID, etc.
    card_last_four = db.Column(db.String(4), nullable=True)  # Last 4 digits of card
    card_type = db.Column(db.String(20), nullable=True)  # Visa, Mastercard, Amex, etc.

    # Status
    status = db.Column(db.String(20), default="completed", nullable=False)  # completed, pending, failed, refunded

    # Notes
    notes = db.Column(db.Text, nullable=True)

    # Metadata
    processed_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    invoice = db.relationship("Invoice", back_populates="payments")
    client = db.relationship("Client", backref="payments")
    processed_by = db.relationship("User")

    def __repr__(self):
        return f"<Payment {self.id} - ${self.amount} - {self.payment_method}>"

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
            "card_last_four": self.card_last_four,
            "card_type": self.card_type,
            "status": self.status,
            "notes": self.notes,
            "processed_by_id": self.processed_by_id,
            "processed_by_name": self.processed_by.username if self.processed_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
