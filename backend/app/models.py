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
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )

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
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    patients = db.relationship(
        "Patient", back_populates="owner", lazy=True, cascade="all, delete-orphan"
    )

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
    species = db.Column(
        db.String(50), default="Cat", nullable=False
    )  # Always "Cat" - feline-only clinic
    breed = db.Column(
        db.String(100)
    )  # Cat breeds: Persian, Siamese, Maine Coon, Domestic Shorthair, etc.
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
    status = db.Column(
        db.String(20), default="Active", nullable=False
    )  # Active, Inactive, Deceased
    deceased_date = db.Column(db.Date, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

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
