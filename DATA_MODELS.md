# Lenox Cat Hospital - Data Model Architecture

## Overview
This document defines the complete database schema for the **feline-only** veterinary practice management system. Lenox Cat Hospital exclusively treats cats, and all patient records are for feline patients. Models are organized by domain and show relationships between entities.

> **Important:** All patients are cats. The Patient model defaults species to 'Cat' and is designed specifically for feline medical records.

---

## Phase 1 Models

### User (Authentication & Staff)
**Purpose:** Authentication and staff management

```python
class User(db.Model):
    # Existing fields
    id = Integer, PK
    username = String(100), unique, not null
    password_hash = String(128)
    role = String(80), not null, default='user'

    # New fields to add
    email = String(120), unique
    first_name = String(100)
    last_name = String(100)
    is_active = Boolean, default=True
    created_at = DateTime, default=now
    last_login = DateTime

    # Relationships
    appointments_assigned = relationship('Appointment', back_populates='assigned_to')
```

**Roles:**
- administrator (full access)
- veterinarian (doctor)
- technician (vet tech)
- receptionist (front desk)
- user (basic)

---

### Client (Pet Owner)
**Purpose:** Store client/pet owner information

```python
class Client(db.Model):
    id = Integer, PK

    # Personal Info
    first_name = String(100), not null
    last_name = String(100), not null
    email = String(120), unique, nullable
    phone_primary = String(20), not null
    phone_secondary = String(20)

    # Address
    address_line1 = String(200)
    address_line2 = String(200)
    city = String(100)
    state = String(50)
    zip_code = String(20)

    # Communication Preferences
    preferred_contact = String(20)  # email, phone, sms
    email_reminders = Boolean, default=True
    sms_reminders = Boolean, default=True

    # Account
    account_balance = Decimal(10, 2), default=0.00
    credit_limit = Decimal(10, 2), default=0.00

    # Metadata
    notes = Text
    alerts = Text  # Important alerts (e.g., "Aggressive dog owner")
    created_at = DateTime, default=now
    updated_at = DateTime, onupdate=now
    is_active = Boolean, default=True

    # Relationships
    patients = relationship('Patient', back_populates='owner')
    appointments = relationship('Appointment', back_populates='client')
    invoices = relationship('Invoice', back_populates='client')
```

**Indexes:**
- idx_client_email
- idx_client_phone
- idx_client_name (last_name, first_name)

---

### Patient (Cat)
**Purpose:** Store patient (cat) information for feline-only clinic

```python
class Patient(db.Model):
    id = Integer, PK

    # Basic Info
    name = String(100), not null
    species = String(50), default='Cat', not null  # Always 'Cat' - feline-only clinic
    breed = String(100)  # Cat breeds: Persian, Siamese, Maine Coon, Domestic Shorthair, etc.
    color = String(100)
    markings = Text

    # Physical
    sex = String(20)  # Male, Female
    reproductive_status = String(50)  # Intact, Neutered, Spayed
    date_of_birth = Date
    approximate_age = String(50)  # If DOB unknown
    weight_kg = Decimal(5, 2)

    # Identification
    microchip_number = String(50), unique, nullable
    license_number = String(50)

    # Insurance
    insurance_company = String(100)
    insurance_policy_number = String(100)

    # Status
    status = String(20), default='Active'  # Active, Inactive, Deceased
    deceased_date = Date

    # Links
    owner_id = Integer, FK(Client.id), not null
    photo_url = String(500)

    # Metadata
    notes = Text
    behavioral_notes = Text
    created_at = DateTime, default=now
    updated_at = DateTime, onupdate=now

    # Relationships
    owner = relationship('Client', back_populates='patients')
    appointments = relationship('Appointment', back_populates='patient')
    medical_records = relationship('Visit', back_populates='patient')
    allergies = relationship('Allergy', back_populates='patient')
    medications = relationship('CurrentMedication', back_populates='patient')
```

**Indexes:**
- idx_patient_owner
- idx_patient_microchip
- idx_patient_status

---

### Appointment (Enhanced)
**Purpose:** Schedule appointments

```python
class Appointment(db.Model):
    id = Integer, PK

    # Existing fields (modified)
    title = String(100), not null
    start_time = DateTime, not null  # renamed from start
    end_time = DateTime, not null    # renamed from end
    description = Text

    # New fields
    appointment_type = String(50), not null  # Wellness, Surgery, Emergency, Follow-up, Grooming
    status = String(50), default='Scheduled'  # Scheduled, Confirmed, Checked-In, In-Progress, Completed, Cancelled, No-Show

    # Links
    patient_id = Integer, FK(Patient.id), not null
    client_id = Integer, FK(Client.id), not null
    assigned_to_id = Integer, FK(User.id)  # Veterinarian/technician

    # Details
    room = String(50)
    duration_minutes = Integer
    check_in_time = DateTime
    check_out_time = DateTime

    # Reminders
    reminder_sent = Boolean, default=False
    reminder_sent_at = DateTime
    confirmation_status = String(50)  # Pending, Confirmed, Declined

    # Metadata
    cancellation_reason = Text
    created_at = DateTime, default=now
    updated_at = DateTime, onupdate=now
    created_by_id = Integer, FK(User.id)

    # Relationships
    patient = relationship('Patient', back_populates='appointments')
    client = relationship('Client', back_populates='appointments')
    assigned_to = relationship('User', foreign_keys=[assigned_to_id])
    created_by = relationship('User', foreign_keys=[created_by_id])
    visit = relationship('Visit', back_populates='appointment', uselist=False)
```

**Indexes:**
- idx_appointment_datetime (start_time, end_time)
- idx_appointment_patient
- idx_appointment_client
- idx_appointment_status

---

### AppointmentType
**Purpose:** Define appointment types for scheduling

```python
class AppointmentType(db.Model):
    id = Integer, PK
    name = String(100), not null, unique
    duration_minutes = Integer, not null
    color = String(7)  # Hex color for calendar
    description = Text
    is_active = Boolean, default=True

    # Pricing (optional)
    default_price = Decimal(10, 2)
```

---

## Phase 2 Models (Medical Records & Billing)

### Visit
**Purpose:** Medical visit record

```python
class Visit(db.Model):
    id = Integer, PK

    # Links
    patient_id = Integer, FK(Patient.id), not null
    appointment_id = Integer, FK(Appointment.id), nullable  # May not have appointment
    veterinarian_id = Integer, FK(User.id), not null

    # Visit Info
    visit_date = DateTime, not null, default=now
    visit_type = String(50)  # Wellness, Sick, Surgery, Emergency, Follow-up
    chief_complaint = Text

    # Status
    status = String(50), default='In-Progress'  # In-Progress, Completed, Cancelled

    # Metadata
    created_at = DateTime, default=now
    updated_at = DateTime, onupdate=now

    # Relationships
    patient = relationship('Patient', back_populates='medical_records')
    appointment = relationship('Appointment', back_populates='visit')
    veterinarian = relationship('User')
    soap_note = relationship('SOAPNote', back_populates='visit', uselist=False)
    vital_signs = relationship('VitalSigns', back_populates='visit')
    diagnoses = relationship('Diagnosis', back_populates='visit')
    prescriptions = relationship('Prescription', back_populates='visit')
    invoice = relationship('Invoice', back_populates='visit', uselist=False)
```

**Indexes:**
- idx_visit_patient
- idx_visit_date

---

### SOAPNote
**Purpose:** SOAP format medical notes

```python
class SOAPNote(db.Model):
    id = Integer, PK
    visit_id = Integer, FK(Visit.id), not null, unique

    # SOAP Components
    subjective = Text  # What client reports
    objective = Text   # Physical exam findings
    assessment = Text  # Doctor's assessment/diagnoses
    plan = Text        # Treatment plan

    # Metadata
    created_at = DateTime, default=now
    updated_at = DateTime, onupdate=now
    signed_by_id = Integer, FK(User.id)
    signed_at = DateTime

    # Relationships
    visit = relationship('Visit', back_populates='soap_note')
    signed_by = relationship('User')
```

---

### VitalSigns
**Purpose:** Record vital signs during visit

```python
class VitalSigns(db.Model):
    id = Integer, PK
    visit_id = Integer, FK(Visit.id), not null

    # Vitals
    temperature_celsius = Decimal(4, 1)  # e.g., 38.5
    weight_kg = Decimal(5, 2)
    heart_rate_bpm = Integer
    respiratory_rate_bpm = Integer
    blood_pressure_systolic = Integer
    blood_pressure_diastolic = Integer

    # Calculated
    body_condition_score = Integer  # 1-9 scale
    pain_score = Integer  # 0-10 scale

    # Metadata
    recorded_at = DateTime, default=now
    recorded_by_id = Integer, FK(User.id)

    # Relationships
    visit = relationship('Visit', back_populates='vital_signs')
    recorded_by = relationship('User')
```

---

### Diagnosis
**Purpose:** Record diagnoses

```python
class Diagnosis(db.Model):
    id = Integer, PK
    visit_id = Integer, FK(Visit.id), not null

    # Diagnosis Info
    diagnosis_code = String(20)  # ICD-10 code
    diagnosis_name = String(200), not null
    description = Text
    is_primary = Boolean, default=False

    # Status
    status = String(50)  # Active, Resolved, Chronic
    onset_date = Date
    resolved_date = Date

    # Metadata
    created_at = DateTime, default=now

    # Relationships
    visit = relationship('Visit', back_populates='diagnoses')
```

---

### Allergy
**Purpose:** Track patient allergies

```python
class Allergy(db.Model):
    id = Integer, PK
    patient_id = Integer, FK(Patient.id), not null

    allergen = String(200), not null
    reaction = Text
    severity = String(50)  # Mild, Moderate, Severe, Life-threatening

    diagnosed_date = Date
    notes = Text

    created_at = DateTime, default=now

    # Relationships
    patient = relationship('Patient', back_populates='allergies')
```

---

### Vaccination
**Purpose:** Track vaccination history

```python
class Vaccination(db.Model):
    id = Integer, PK
    patient_id = Integer, FK(Patient.id), not null

    # Vaccine Info
    vaccine_name = String(200), not null
    vaccine_type = String(100)  # Rabies, FVRCP, FeLV, etc.
    manufacturer = String(100)
    lot_number = String(100)

    # Administration
    administered_date = Date, not null
    expiration_date = Date
    next_due_date = Date
    administered_by_id = Integer, FK(User.id)

    # Metadata
    notes = Text
    site = String(100)  # Injection site

    # Relationships
    patient = relationship('Patient')
    administered_by = relationship('User')
```

**Indexes:**
- idx_vaccination_patient
- idx_vaccination_next_due

---

### Medication (Drug Database)
**Purpose:** Medication catalog

```python
class Medication(db.Model):
    id = Integer, PK

    # Drug Info
    name = String(200), not null
    generic_name = String(200)
    form = String(100)  # Tablet, Liquid, Injection, Topical
    strength = String(100)  # e.g., "10mg", "50mg/ml"

    # Classification
    category = String(100)  # Antibiotic, Analgesic, Antiparasitic, etc.
    is_controlled = Boolean, default=False
    dea_schedule = String(10)  # I, II, III, IV, V

    # Inventory Link
    product_id = Integer, FK(Product.id), nullable

    # Administration
    route = String(100)  # Oral, Injectable, Topical
    dosage_guidelines = Text

    # Metadata
    is_active = Boolean, default=True
    notes = Text
```

---

### Prescription
**Purpose:** Prescriptions written during visits

```python
class Prescription(db.Model):
    id = Integer, PK

    # Links
    patient_id = Integer, FK(Patient.id), not null
    visit_id = Integer, FK(Visit.id)
    medication_id = Integer, FK(Medication.id), not null
    prescribed_by_id = Integer, FK(User.id), not null

    # Prescription Details
    dosage = String(200), not null  # e.g., "10mg"
    frequency = String(200), not null  # e.g., "Twice daily"
    duration = String(100)  # e.g., "10 days"
    quantity = Decimal(10, 2), not null
    refills_allowed = Integer, default=0
    refills_used = Integer, default=0

    # Instructions
    instructions = Text

    # Dates
    prescribed_date = Date, not null, default=now
    start_date = Date
    end_date = Date

    # Status
    status = String(50), default='Active'  # Active, Completed, Cancelled

    # Metadata
    created_at = DateTime, default=now

    # Relationships
    patient = relationship('Patient')
    visit = relationship('Visit', back_populates='prescriptions')
    medication = relationship('Medication')
    prescribed_by = relationship('User')
```

---

### CurrentMedication
**Purpose:** Track current medications patient is on

```python
class CurrentMedication(db.Model):
    id = Integer, PK
    patient_id = Integer, FK(Patient.id), not null

    medication_name = String(200), not null
    dosage = String(200)
    frequency = String(200)
    started_date = Date
    notes = Text

    # Relationships
    patient = relationship('Patient', back_populates='medications')
```

---

### Invoice
**Purpose:** Billing and invoicing

```python
class Invoice(db.Model):
    id = Integer, PK
    invoice_number = String(50), unique, not null

    # Links
    client_id = Integer, FK(Client.id), not null
    patient_id = Integer, FK(Patient.id)
    visit_id = Integer, FK(Visit.id), nullable

    # Financial
    subtotal = Decimal(10, 2), not null
    tax_rate = Decimal(5, 2), default=0.00
    tax_amount = Decimal(10, 2), default=0.00
    discount_amount = Decimal(10, 2), default=0.00
    total_amount = Decimal(10, 2), not null
    amount_paid = Decimal(10, 2), default=0.00
    balance_due = Decimal(10, 2), not null

    # Status
    status = String(50), default='Draft'  # Draft, Sent, Paid, Partial, Overdue, Cancelled

    # Dates
    invoice_date = Date, not null, default=now
    due_date = Date
    paid_date = Date

    # Metadata
    notes = Text
    created_at = DateTime, default=now
    updated_at = DateTime, onupdate=now
    created_by_id = Integer, FK(User.id)

    # Relationships
    client = relationship('Client', back_populates='invoices')
    patient = relationship('Patient')
    visit = relationship('Visit', back_populates='invoice')
    items = relationship('InvoiceItem', back_populates='invoice', cascade='all, delete-orphan')
    payments = relationship('Payment', back_populates='invoice')
    created_by = relationship('User')
```

**Indexes:**
- idx_invoice_number
- idx_invoice_client
- idx_invoice_status

---

### InvoiceItem
**Purpose:** Line items on invoice

```python
class InvoiceItem(db.Model):
    id = Integer, PK
    invoice_id = Integer, FK(Invoice.id), not null

    # Item Details
    item_type = String(50), not null  # Service, Product, Medication
    description = String(500), not null
    quantity = Decimal(10, 2), not null, default=1
    unit_price = Decimal(10, 2), not null
    line_total = Decimal(10, 2), not null

    # Optional Links
    product_id = Integer, FK(Product.id), nullable
    service_id = Integer, FK(Service.id), nullable

    # Metadata
    created_at = DateTime, default=now

    # Relationships
    invoice = relationship('Invoice', back_populates='items')
    product = relationship('Product')
    service = relationship('Service')
```

---

### Service
**Purpose:** Service catalog for billing

```python
class Service(db.Model):
    id = Integer, PK

    name = String(200), not null, unique
    description = Text
    category = String(100)  # Exam, Surgery, Diagnostic, etc.
    default_price = Decimal(10, 2), not null
    duration_minutes = Integer

    is_active = Boolean, default=True
    created_at = DateTime, default=now
```

---

### Payment
**Purpose:** Record payments made

```python
class Payment(db.Model):
    id = Integer, PK

    # Links
    invoice_id = Integer, FK(Invoice.id), not null
    client_id = Integer, FK(Client.id), not null

    # Payment Details
    payment_date = DateTime, not null, default=now
    amount = Decimal(10, 2), not null
    payment_method = String(50), not null  # Cash, Check, Credit Card, Debit Card, CareCredit

    # Card/Check Details
    reference_number = String(100)  # Check number, transaction ID
    card_last_four = String(4)
    card_type = String(50)  # Visa, Mastercard, etc.

    # Status
    status = String(50), default='Completed'  # Pending, Completed, Failed, Refunded

    # Metadata
    notes = Text
    processed_by_id = Integer, FK(User.id)
    created_at = DateTime, default=now

    # Relationships
    invoice = relationship('Invoice', back_populates='payments')
    client = relationship('Client')
    processed_by = relationship('User')
```

**Indexes:**
- idx_payment_invoice
- idx_payment_client
- idx_payment_date

---

## Phase 3 Models (Inventory & Staff)

### Product
**Purpose:** Inventory items (medications, supplies, retail)

```python
class Product(db.Model):
    id = Integer, PK

    # Product Info
    sku = String(100), unique
    name = String(200), not null
    description = Text
    category = String(100)  # Medication, Supply, Retail, Vaccine

    # Pricing
    cost_price = Decimal(10, 2)
    retail_price = Decimal(10, 2), not null
    markup_percentage = Decimal(5, 2)

    # Inventory
    current_stock = Integer, default=0
    reorder_level = Integer, default=0
    reorder_quantity = Integer, default=0

    # Details
    manufacturer = String(200)
    vendor_id = Integer, FK(Vendor.id)
    unit_of_measure = String(50)  # Each, Box, Bottle, etc.

    # Expiration Tracking
    tracks_expiration = Boolean, default=False
    tracks_lot_number = Boolean, default=False

    # Status
    is_active = Boolean, default=True
    created_at = DateTime, default=now
    updated_at = DateTime, onupdate=now

    # Relationships
    vendor = relationship('Vendor')
    inventory_transactions = relationship('InventoryTransaction', back_populates='product')
```

**Indexes:**
- idx_product_sku
- idx_product_category

---

### Vendor
**Purpose:** Supplier information

```python
class Vendor(db.Model):
    id = Integer, PK

    name = String(200), not null
    contact_person = String(100)
    email = String(120)
    phone = String(20)
    website = String(200)

    # Address
    address_line1 = String(200)
    address_line2 = String(200)
    city = String(100)
    state = String(50)
    zip_code = String(20)

    # Account
    account_number = String(100)
    payment_terms = String(100)

    is_active = Boolean, default=True
    notes = Text
    created_at = DateTime, default=now
```

---

### PurchaseOrder
**Purpose:** Ordering inventory

```python
class PurchaseOrder(db.Model):
    id = Integer, PK
    po_number = String(50), unique, not null

    vendor_id = Integer, FK(Vendor.id), not null
    order_date = Date, not null, default=now
    expected_delivery_date = Date
    actual_delivery_date = Date

    # Financial
    subtotal = Decimal(10, 2)
    tax_amount = Decimal(10, 2), default=0.00
    shipping_cost = Decimal(10, 2), default=0.00
    total_amount = Decimal(10, 2)

    # Status
    status = String(50), default='Draft'  # Draft, Submitted, Received, Cancelled

    notes = Text
    created_by_id = Integer, FK(User.id)
    received_by_id = Integer, FK(User.id)
    created_at = DateTime, default=now

    # Relationships
    vendor = relationship('Vendor')
    items = relationship('PurchaseOrderItem', back_populates='purchase_order')
    created_by = relationship('User', foreign_keys=[created_by_id])
    received_by = relationship('User', foreign_keys=[received_by_id])
```

---

### PurchaseOrderItem
**Purpose:** Line items on purchase order

```python
class PurchaseOrderItem(db.Model):
    id = Integer, PK
    purchase_order_id = Integer, FK(PurchaseOrder.id), not null
    product_id = Integer, FK(Product.id), not null

    quantity_ordered = Integer, not null
    quantity_received = Integer, default=0
    unit_cost = Decimal(10, 2), not null
    line_total = Decimal(10, 2), not null

    lot_number = String(100)
    expiration_date = Date

    # Relationships
    purchase_order = relationship('PurchaseOrder', back_populates='items')
    product = relationship('Product')
```

---

### InventoryTransaction
**Purpose:** Track inventory movements

```python
class InventoryTransaction(db.Model):
    id = Integer, PK

    product_id = Integer, FK(Product.id), not null
    transaction_type = String(50), not null  # Purchase, Sale, Adjustment, Expired, Transfer
    quantity = Integer, not null  # Positive for additions, negative for reductions

    # Context
    reference_type = String(50)  # PurchaseOrder, Invoice, Adjustment
    reference_id = Integer

    # Details
    lot_number = String(100)
    expiration_date = Date
    notes = Text

    # Stock After Transaction
    stock_after = Integer

    # Metadata
    transaction_date = DateTime, not null, default=now
    user_id = Integer, FK(User.id)

    # Relationships
    product = relationship('Product', back_populates='inventory_transactions')
    user = relationship('User')
```

**Indexes:**
- idx_inventory_product
- idx_inventory_date

---

### Staff (Extended User Info)
**Purpose:** Additional staff information beyond User model

```python
class Staff(db.Model):
    id = Integer, PK
    user_id = Integer, FK(User.id), not null, unique

    # Professional Info
    title = String(100)  # DVM, RVT, etc.
    license_number = String(100)
    license_expiration = Date
    dea_number = String(50)

    # Employment
    hire_date = Date
    employment_status = String(50)  # Full-time, Part-time, Contract
    hourly_rate = Decimal(10, 2)

    # Availability
    default_schedule = JSON  # JSON object with weekly schedule

    notes = Text

    # Relationships
    user = relationship('User')
```

---

### Schedule
**Purpose:** Staff scheduling

```python
class Schedule(db.Model):
    id = Integer, PK

    staff_id = Integer, FK(Staff.id), not null
    shift_date = Date, not null
    start_time = Time, not null
    end_time = Time, not null

    shift_type = String(50)  # Regular, On-call, Emergency
    status = String(50), default='Scheduled'  # Scheduled, Completed, Cancelled

    notes = Text
    created_at = DateTime, default=now

    # Relationships
    staff = relationship('Staff')
```

**Indexes:**
- idx_schedule_staff_date

---

### TimeOff
**Purpose:** Time-off requests

```python
class TimeOff(db.Model):
    id = Integer, PK

    staff_id = Integer, FK(Staff.id), not null
    start_date = Date, not null
    end_date = Date, not null

    request_type = String(50)  # Vacation, Sick, Personal
    status = String(50), default='Pending'  # Pending, Approved, Denied

    notes = Text
    requested_at = DateTime, default=now
    reviewed_by_id = Integer, FK(User.id)
    reviewed_at = DateTime

    # Relationships
    staff = relationship('Staff')
    reviewed_by = relationship('User')
```

---

## Phase 4 Models (Documents & Protocols)

### Document
**Purpose:** File storage and management

```python
class Document(db.Model):
    id = Integer, PK

    # File Info
    filename = String(500), not null
    file_type = String(100)  # PDF, Image, etc.
    file_size_bytes = Integer
    storage_path = String(500), not null  # S3 key or file path
    mime_type = String(100)

    # Classification
    category = String(100)  # Medical Record, Consent Form, X-ray, Lab Result
    description = Text
    tags = String(500)  # Comma-separated tags

    # Links (polymorphic)
    linked_entity_type = String(50)  # Patient, Visit, Invoice
    linked_entity_id = Integer

    # Metadata
    uploaded_by_id = Integer, FK(User.id)
    uploaded_at = DateTime, default=now

    # Relationships
    uploaded_by = relationship('User')
```

**Indexes:**
- idx_document_linked_entity

---

### TreatmentPlan
**Purpose:** Multi-visit treatment planning

```python
class TreatmentPlan(db.Model):
    id = Integer, PK

    patient_id = Integer, FK(Patient.id), not null
    created_by_id = Integer, FK(User.id), not null

    title = String(200), not null
    description = Text

    # Dates
    start_date = Date, not null
    end_date = Date

    # Cost
    estimated_cost = Decimal(10, 2)
    actual_cost = Decimal(10, 2)

    # Status
    status = String(50), default='Active'  # Active, Completed, Cancelled
    progress_percentage = Integer, default=0

    notes = Text
    created_at = DateTime, default=now
    updated_at = DateTime, onupdate=now

    # Relationships
    patient = relationship('Patient')
    created_by = relationship('User')
    steps = relationship('TreatmentPlanStep', back_populates='plan')
```

---

### TreatmentPlanStep
**Purpose:** Individual steps in treatment plan

```python
class TreatmentPlanStep(db.Model):
    id = Integer, PK
    plan_id = Integer, FK(TreatmentPlan.id), not null

    step_number = Integer, not null
    description = Text, not null
    estimated_cost = Decimal(10, 2)

    scheduled_date = Date
    completed_date = Date
    status = String(50), default='Pending'  # Pending, Completed, Skipped

    visit_id = Integer, FK(Visit.id), nullable
    notes = Text

    # Relationships
    plan = relationship('TreatmentPlan', back_populates='steps')
    visit = relationship('Visit')
```

---

### Protocol
**Purpose:** Standard protocols and templates

```python
class Protocol(db.Model):
    id = Integer, PK

    name = String(200), not null
    protocol_type = String(50)  # Surgical, Treatment, Exam, Emergency
    description = Text

    # Template Content
    content = Text  # JSON or structured content

    is_active = Boolean, default=True
    created_by_id = Integer, FK(User.id)
    created_at = DateTime, default=now
    updated_at = DateTime, onupdate=now

    # Relationships
    created_by = relationship('User')
```

---

## Supporting Models

### AuditLog
**Purpose:** Track data access and changes (HIPAA compliance)

```python
class AuditLog(db.Model):
    id = Integer, PK

    user_id = Integer, FK(User.id), not null
    action = String(100), not null  # CREATE, READ, UPDATE, DELETE
    entity_type = String(100), not null  # Patient, Visit, Invoice, etc.
    entity_id = Integer, not null

    changes = JSON  # Store what changed
    ip_address = String(50)
    user_agent = String(500)

    timestamp = DateTime, default=now

    # Relationships
    user = relationship('User')
```

**Indexes:**
- idx_audit_user
- idx_audit_entity
- idx_audit_timestamp

---

### Reminder
**Purpose:** Automated reminders

```python
class Reminder(db.Model):
    id = Integer, PK

    client_id = Integer, FK(Client.id), not null
    patient_id = Integer, FK(Patient.id)

    reminder_type = String(50), not null  # Appointment, Vaccination, Follow-up
    message_template = String(100)

    scheduled_date = Date, not null
    sent_date = DateTime

    method = String(50)  # Email, SMS, Phone
    status = String(50), default='Pending'  # Pending, Sent, Failed, Cancelled

    # Context
    appointment_id = Integer, FK(Appointment.id)

    notes = Text

    # Relationships
    client = relationship('Client')
    patient = relationship('Patient')
    appointment = relationship('Appointment')
```

**Indexes:**
- idx_reminder_scheduled
- idx_reminder_status

---

## Database Relationships Summary

```
Client (1) → (Many) Patient
Client (1) → (Many) Appointment
Client (1) → (Many) Invoice
Client (1) → (Many) Payment

Patient (1) → (Many) Appointment
Patient (1) → (Many) Visit
Patient (1) → (Many) Allergy
Patient (1) → (Many) Vaccination
Patient (1) → (Many) CurrentMedication
Patient (1) → (Many) Prescription

Appointment (1) → (1) Visit
Appointment (Many) → (1) User (assigned_to)

Visit (1) → (1) SOAPNote
Visit (1) → (Many) VitalSigns
Visit (1) → (Many) Diagnosis
Visit (1) → (Many) Prescription
Visit (1) → (1) Invoice

Invoice (1) → (Many) InvoiceItem
Invoice (1) → (Many) Payment

Product (1) → (Many) InvoiceItem
Product (1) → (Many) InventoryTransaction
Product (Many) → (1) Vendor

PurchaseOrder (1) → (Many) PurchaseOrderItem
PurchaseOrder (Many) → (1) Vendor

User (1) → (1) Staff
Staff (1) → (Many) Schedule
```

---

## Migration Strategy

### Phase 1 Migrations
1. Expand User model
2. Create Client model
3. Expand Patient model (add owner_id FK)
4. Expand Appointment model (add patient_id, client_id, assigned_to_id FKs)
5. Create AppointmentType model

### Phase 2 Migrations
1. Create Visit, SOAPNote, VitalSigns models
2. Create Diagnosis, Allergy, Vaccination models
3. Create Medication, Prescription, CurrentMedication models
4. Create Invoice, InvoiceItem, Payment, Service models

### Phase 3 Migrations
1. Create Product, Vendor, PurchaseOrder models
2. Create InventoryTransaction model
3. Create Staff, Schedule, TimeOff models
4. Create AuditLog model

### Phase 4 Migrations
1. Create Document model
2. Create TreatmentPlan, TreatmentPlanStep models
3. Create Protocol model
4. Create Reminder model

---

## Indexes & Performance Considerations

### Critical Indexes
- All foreign keys should have indexes
- Date fields used for filtering (appointment dates, invoice dates)
- Search fields (client name, patient name, phone, email)
- Status fields (appointment status, invoice status)

### Composite Indexes
- (client.last_name, client.first_name)
- (appointment.start_time, appointment.status)
- (invoice.client_id, invoice.status)

### Query Optimization
- Use eager loading for common relationships
- Implement pagination for large lists
- Cache frequently accessed data (product catalog, services)
- Use database views for complex reporting queries

---

**Last Updated:** 2025-10-25
**Next Review:** Beginning of Phase 2
