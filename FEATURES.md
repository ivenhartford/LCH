# Lenox Cat Hospital - Feature Set

## Overview
Comprehensive practice management software suite for a **feline-only veterinary clinic**. Lenox Cat Hospital exclusively treats cats - all patients in the system are felines, and the application is designed specifically for cat-focused veterinary care.

> **Important:** This is a cat-only clinic. The patient management system defaults to species='Cat' and focuses on feline-specific medical care, treatments, and protocols.

## Core Modules

### 1. Client Management
**Priority: HIGH | Phase: 1**

- **Client Profile**
  - Contact information (name, email, phone, address)
  - Multiple contact methods (emergency contact)
  - Communication preferences (email, SMS, phone)
  - Client notes and alerts
  - Payment methods on file
  - Account balance and credit

- **Client Portal** (Phase 3)
  - Online account access
  - View pet records
  - Book appointments
  - Pay invoices online
  - Request prescription refills
  - Secure messaging with clinic

### 2. Patient (Cat) Management
**Priority: HIGH | Phase: 1**

- **Patient Profile**
  - Basic info (name, breed, color, markings)
  - Species: Always 'Cat' (feline-only clinic)
  - Breed: Cat breeds (Persian, Siamese, Maine Coon, Domestic Shorthair, etc.)
  - Date of birth / age
  - Sex and reproductive status (spayed/neutered)
  - Microchip number
  - Insurance information
  - Photo upload
  - Multiple cats per client
  - Active/inactive/deceased status

- **Medical History**
  - Previous conditions
  - Allergies and reactions
  - Current medications
  - Vaccination history
  - Surgical history
  - Behavioral notes

### 3. Appointment Management
**Priority: HIGH | Phase: 1 (Enhanced)**

- **Scheduling**
  - Visual calendar (already started)
  - Multiple appointment types (wellness, surgery, emergency, grooming)
  - Duration-based scheduling
  - Recurring appointments
  - Waitlist management
  - Color-coding by type/doctor
  - Drag-and-drop rescheduling

- **Appointment Details**
  - Link to patient and client
  - Assigned veterinarian/technician
  - Room assignment
  - Appointment status (scheduled, checked-in, in-progress, completed, no-show)
  - Estimated duration
  - Appointment notes
  - Pre-appointment instructions

- **Reminders**
  - Automated email/SMS reminders
  - Confirmation requests
  - Follow-up appointment reminders
  - Vaccination due reminders

### 4. Medical Records (SOAP Notes)
**Priority: HIGH | Phase: 2**

- **Visit Documentation**
  - SOAP format (Subjective, Objective, Assessment, Plan)
  - Chief complaint
  - Vital signs (temperature, weight, heart rate, respiratory rate)
  - Physical examination findings
  - Diagnoses (with ICD codes)
  - Treatment plan
  - Prescribed medications
  - Follow-up instructions
  - Doctor signature/timestamp

- **Diagnostic Results**
  - Lab results entry and tracking
  - Integration with external labs
  - Imaging results (X-rays, ultrasounds)
  - Document attachment (PDFs, images)

- **Treatment History**
  - Complete chronological record
  - Filter by date, type, doctor
  - Print/export medical records
  - Medical record requests

### 5. Prescription Management
**Priority: HIGH | Phase: 2**

- **Prescriptions**
  - Medication database
  - Dosage calculator by weight
  - Prescription writing and printing
  - Refill management
  - Controlled substance tracking (DEA compliance)
  - Drug interaction warnings
  - Client instructions

- **Medication Inventory Link**
  - Auto-deduct from inventory
  - Low stock alerts for prescriptions
  - Expiration tracking

### 6. Invoicing & Billing
**Priority: HIGH | Phase: 2**

- **Invoice Creation**
  - Line items for services, medications, supplies
  - Link to appointment/visit
  - Tax calculation
  - Discounts and adjustments
  - Multiple payment methods (cash, card, check, CareCredit)
  - Split payments
  - Partial payments and balance tracking

- **Payment Processing**
  - Credit card processing (Stripe/Square integration)
  - Payment receipts (email, print)
  - Refund processing
  - Payment plans

- **Insurance Claims**
  - Pet insurance claim forms
  - Claim tracking
  - Direct insurance billing (if available)

- **Financial Reporting**
  - Daily/weekly/monthly revenue reports
  - Outstanding balances report
  - Payment method breakdown
  - Service revenue analysis
  - Doctor production reports

### 7. Inventory Management
**Priority: MEDIUM | Phase: 3**

- **Product Management**
  - Medications, vaccines, supplies, retail items
  - Product categories
  - SKU/barcode
  - Pricing (cost, markup, retail)
  - Reorder levels and points
  - Preferred vendors
  - Expiration date tracking

- **Inventory Tracking**
  - Current stock levels
  - Real-time updates on usage
  - Inventory adjustments
  - Stock transfers between locations
  - Low stock alerts

- **Ordering**
  - Purchase order creation
  - Receiving/check-in
  - Vendor management
  - Order history

- **Reporting**
  - Inventory valuation
  - Usage reports
  - Expiring items report
  - Dead stock analysis

### 8. Staff Management
**Priority: MEDIUM | Phase: 3**

- **Staff Profiles**
  - Employee information
  - Roles (DVM, Vet Tech, Receptionist, Admin)
  - Credentials and licenses
  - Schedule availability
  - Hourly rate / salary

- **Scheduling**
  - Staff schedule calendar
  - Shift management
  - Time-off requests
  - On-call rotation

- **Permissions & Security**
  - Role-based access control (RBAC)
  - Audit logs of record access
  - Action permissions by role
  - HIPAA compliance tracking

### 9. Laboratory Management
**Priority: MEDIUM | Phase: 3**

- **In-House Tests**
  - Test catalog (bloodwork, urinalysis, fecal, etc.)
  - Result entry and normal ranges
  - Abnormal flagging
  - Trend analysis over time

- **External Lab Integration**
  - Send tests to reference labs
  - Electronic result import (if available)
  - Lab order tracking
  - Result notification to doctor

### 10. Treatment Plans & Protocols ✅
**Priority: MEDIUM | Phase: 4.2 | Status: COMPLETE**

- **Protocol Library**
  - Reusable treatment plan templates
  - Protocol categories (general, dental, surgical, emergency, chronic care, preventive, diagnostic)
  - Multi-step protocol definitions
  - Estimated cost and duration tracking
  - Day offset scheduling for steps
  - Active/inactive protocol management
  - Search and filter protocols by category
  - Detailed protocol steps with descriptions

- **Treatment Plans**
  - Apply protocol templates to patients
  - Patient-specific treatment plans
  - Customizable start dates
  - Multi-step treatment workflows
  - Progress tracking with visual indicators
  - Status workflow: draft → active → completed/cancelled
  - Cost comparison: estimated vs actual
  - Step-level tracking:
    - Scheduled and completed dates
    - Step status (pending, in_progress, completed, skipped)
    - Individual step notes
    - Actual cost tracking per step
  - Auto-calculation of progress percentage
  - Auto-calculation of total actual costs
  - Filter plans by status and patient
  - Search across treatment plan titles

- **Clinical Workflow Integration**
  - Link treatment plans to specific patients
  - View treatment plans from patient detail pages
  - Track compliance and completion
  - Cost estimation before treatment begins
  - Real-time progress monitoring

### 11. Document Management
**Priority: MEDIUM | Phase: 4**

- **Document Storage**
  - PDF upload and storage
  - Image storage (X-rays, photos)
  - Consent forms
  - Client communications
  - Link documents to patients/visits

- **Document Generation**
  - Generate PDFs from templates
  - Medical record summaries
  - Vaccination certificates
  - Health certificates

### 12. Reporting & Analytics
**Priority: MEDIUM | Phase: 4**

- **Business Intelligence**
  - Dashboard with KPIs
  - Revenue trends
  - Appointment volume trends
  - Client retention metrics
  - New client acquisition
  - Average transaction value

- **Clinical Reports**
  - Case statistics
  - Procedure volumes
  - Disease prevalence
  - Vaccination compliance rates

- **Custom Reports**
  - Report builder
  - Export to Excel/CSV
  - Scheduled report delivery

### 13. Communication Center
**Priority: LOW | Phase: 5**

- **Email/SMS**
  - Bulk messaging
  - Appointment reminders (auto)
  - Marketing campaigns
  - Birthday/anniversary messages
  - Recall reminders

- **Internal Messaging**
  - Staff-to-staff messaging
  - Patient care notes between staff
  - Task assignments

### 14. Multi-Location Support
**Priority: LOW | Phase: 5**

- **Location Management**
  - Multiple clinic locations
  - Centralized client database
  - Location-specific inventory
  - Cross-location appointments
  - Consolidated reporting

### 15. Compliance & Security
**Priority: HIGH | Ongoing**

- **HIPAA Compliance**
  - Audit logging
  - Data encryption
  - Secure access controls
  - Breach notification procedures

- **DEA Compliance**
  - Controlled substance tracking
  - Usage logs
  - Inventory reconciliation

- **Data Backup**
  - Automated daily backups
  - Point-in-time recovery
  - Disaster recovery plan

## Nice-to-Have Features (Future)

### 16. Mobile App
- iOS/Android app for doctors
- View schedules
- Access patient records
- Write SOAP notes on tablet

### 17. Telemedicine
- Video consultations
- Remote prescription refills
- Follow-up check-ins

### 18. Boarding & Grooming
- Boarding reservations
- Grooming appointments
- Special care instructions
- Boarding invoicing

### 19. Advanced Analytics
- AI-powered insights
- Predictive analytics
- Client churn prediction
- Revenue forecasting

### 20. Client Education
- Educational resource library
- After-visit summaries
- Condition-specific care instructions
- Video resources

## Technical Requirements

### Non-Functional Requirements
- **Performance**: Page load < 2 seconds
- **Availability**: 99.9% uptime
- **Scalability**: Support 5,000+ patients
- **Security**: HIPAA compliant, encrypted data
- **Usability**: Intuitive UI, minimal training needed
- **Mobile-Responsive**: Works on tablets and phones
- **Data Retention**: 7+ years for medical records
- **Backup**: Daily automated backups with 30-day retention

### Integration Requirements
- Payment processors (Stripe, Square)
- Email service (SendGrid, AWS SES)
- SMS service (Twilio)
- Cloud storage (AWS S3, MinIO)
- External lab systems (HL7, if available)
- Accounting software (QuickBooks export)

## Success Metrics
- Time to schedule appointment: < 2 minutes
- Time to check-in patient: < 30 seconds
- Time to write SOAP note: < 5 minutes
- Time to generate invoice: < 1 minute
- Client satisfaction: > 4.5/5 stars
- Staff adoption rate: > 90% within 30 days
