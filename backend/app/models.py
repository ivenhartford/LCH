from . import db
import bcrypt
from flask_login import UserMixin
from datetime import datetime
from decimal import Decimal

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(80), nullable=False, default='user')

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


class Client(db.Model):
    """
    Client (Pet Owner) Model

    Stores information about pet owners/clients.
    Includes contact information, communication preferences, and account details.
    """
    __tablename__ = 'client'

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
    preferred_contact = db.Column(db.String(20), default='email')  # email, phone, sms
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

    # Relationships (will be added later when Patient model is enhanced)
    # patients = db.relationship('Patient', back_populates='owner', lazy=True)
    # appointments = db.relationship('Appointment', back_populates='client', lazy=True)
    # invoices = db.relationship('Invoice', back_populates='client', lazy=True)

    def __repr__(self):
        return f'<Client {self.first_name} {self.last_name}>'

    def to_dict(self):
        """Convert client to dictionary for API responses"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f'{self.first_name} {self.last_name}',
            'email': self.email,
            'phone_primary': self.phone_primary,
            'phone_secondary': self.phone_secondary,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'preferred_contact': self.preferred_contact,
            'email_reminders': self.email_reminders,
            'sms_reminders': self.sms_reminders,
            'account_balance': float(self.account_balance) if self.account_balance else 0.0,
            'credit_limit': float(self.credit_limit) if self.credit_limit else 0.0,
            'notes': self.notes,
            'alerts': self.alerts,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    breed = db.Column(db.String(100))
    owner = db.Column(db.String(100))

    def __repr__(self):
        return f'<Pet {self.name}>'

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)

    def __repr__(self):
        return f'<Appointment {self.title}>'
