# Lenox Cat Hospital - User Guide

**Version 2.0** | Last Updated: October 2025

Welcome to the Lenox Cat Hospital Practice Management System! This guide will help you navigate and use the system effectively for daily clinic operations.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Client Management](#client-management)
4. [Patient Management](#patient-management)
5. [Appointment Scheduling](#appointment-scheduling)
6. [Clinical Visits](#clinical-visits)
7. [Medical Records](#medical-records)
8. [Prescriptions](#prescriptions)
9. [Billing & Invoicing](#billing--invoicing)
10. [Payment Processing](#payment-processing)
11. [Financial Reports](#financial-reports)
12. [Global Search](#global-search)
13. [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### Logging In

1. Open your web browser and navigate to the clinic management system
2. Enter your username and password
3. Click the "Login" button

**First Time Users:**
- Contact your system administrator to create your account
- You'll receive your username and initial password
- Change your password after first login (Settings)

### Main Navigation

The system has a sidebar on the left with the following sections:

**Main**
- Dashboard - Your home screen with quick stats
- Calendar - Appointment calendar view

**Management**
- Clients - Client information and contact details
- Patients - Patient profiles and medical history

**Clinical**
- Visits - Patient visits and medical records
- Appointments - Appointment management
- Medications - Drug database
- Services - Service catalog for billing

**Financial**
- Invoices - Billing and invoices

**Reports**
- Reports - Financial analytics and reporting

---

## Dashboard Overview

When you log in, you'll see the Dashboard with:

### Quick Stats Cards
- **Total Clients** - Current number of active clients
- **Active Patients** - Total patients in the system
- **Appointments Today** - Number of appointments scheduled for today
- **Recent Visits** - Visits from the past week

### Today's Appointments
- See all appointments scheduled for today
- Color-coded by appointment type
- Click any appointment to view details

### Recent Patients
- Quick access to recently seen patients
- Click a patient to view their full profile

### Quick Actions
- **New Client** - Add a new client
- **New Patient** - Add a new patient
- **New Appointment** - Schedule an appointment
- **New Visit** - Start a patient visit

**Tip:** The dashboard auto-refreshes every 60 seconds to show the latest information.

---

## Client Management

Clients are the pet owners who bring their animals to your clinic.

### Viewing Clients

1. Click **Clients** in the sidebar
2. You'll see a list of all clients with:
   - Name
   - Email
   - Phone number
   - Active patients count
   - Alerts (if any)

### Adding a New Client

1. Click **Clients** → **New Client** button
2. Fill in the required information:
   - **Name*** (required)
   - **Email**
   - **Phone*** (required)
   - **Address, City, State, ZIP**
   - **Emergency Contact**
   - **Preferred Communication** (email, phone, text)
3. Click **Save**

**Required fields are marked with an asterisk (*)**

### Editing Client Information

1. Click on a client's name from the list
2. Click the **Edit** button
3. Update the information
4. Click **Save**

### Client Notes

Add important notes about a client:
1. Open the client's detail page
2. Scroll to the **Notes** section
3. Click **Add Note**
4. Enter your note and click **Save**

**Examples of notes:**
- "Prefers early morning appointments"
- "Payment plan arranged"
- "Anxious pet owner - needs extra reassurance"

### Client Alerts

Set alerts for important client information:
1. Open the client's detail page
2. Click **Set Alert**
3. Choose alert type and enter message
4. Alerts appear in red on the client list

**Examples of alerts:**
- Payment required upfront
- Aggressive pet - handle with care
- VIP client

### Searching for Clients

Use the search box at the top of the client list:
- Search by name
- Search by email
- Search by phone number

---

## Patient Management

Patients are the animals receiving care at your clinic.

### Viewing Patients

1. Click **Patients** in the sidebar
2. View all patients with:
   - Name and photo
   - Species and breed
   - Client name
   - Age
   - Status (Active, Inactive, Deceased)

### Adding a New Patient

1. Click **Patients** → **New Patient** button
2. Fill in patient information:
   - **Client*** (select from dropdown)
   - **Name*** (required)
   - **Species*** (Cat, Dog, etc.)
   - **Breed**
   - **Sex*** (Male, Female, Neutered, Spayed)
   - **Date of Birth**
   - **Weight**
   - **Color/Markings**
   - **Microchip Number**
   - **Insurance Information**
3. Click **Save**

### Patient Profile

Click on a patient to view their complete profile:

**Patient Information Tab:**
- Basic details (name, breed, age, weight)
- Client information
- Microchip and insurance

**Medical History Tab:**
- Past visits
- Chronic conditions
- Allergies
- Current medications

**Appointments Tab:**
- Upcoming appointments
- Past appointment history
- Color-coded by appointment type

**Documents Tab:**
- Uploaded files and documents
- Lab results
- X-rays and images

### Uploading a Patient Photo

1. Open the patient's profile
2. Click the camera icon or **Upload Photo**
3. Select an image file from your computer
4. Photo will appear on the patient's profile

### Changing Patient Status

1. Open the patient's profile
2. Click **Edit**
3. Change **Status** dropdown:
   - **Active** - Current patient
   - **Inactive** - No longer coming to clinic
   - **Deceased** - Passed away
4. Click **Save**

---

## Appointment Scheduling

### Calendar View

1. Click **Calendar** in the sidebar
2. View appointments by:
   - Day
   - Week
   - Month

**Color Coding:**
- Each appointment type has a unique color
- Status affects opacity (pending is lighter, confirmed is darker)

### Creating an Appointment

**Method 1: From Calendar**
1. Click on an empty time slot
2. Fill in appointment details
3. Click **Save**

**Method 2: From New Appointment Button**
1. Click **New Appointment** button
2. Fill in the form:
   - **Appointment Type*** (Wellness, Emergency, Surgery, etc.)
   - **Client*** (select from dropdown)
   - **Patient*** (select from dropdown - filtered by client)
   - **Date & Time***
   - **Duration** (default 30 minutes)
   - **Assigned Staff**
   - **Room/Location**
   - **Reason for Visit**
   - **Notes**
3. Click **Save**

### Viewing Appointment Details

1. Click on an appointment in the calendar
2. View complete appointment information:
   - Client and patient details
   - Appointment type and status
   - Assigned staff and room
   - Timing information
   - Notes

### Managing Appointment Status

Appointments flow through these statuses:

1. **Pending** → Initial booking
2. **Confirmed** → Client confirmed
3. **Checked In** → Patient arrived
4. **In Progress** → Currently being seen
5. **Completed** → Visit finished
6. **Cancelled** → Appointment cancelled

**To update status:**
1. Open appointment details
2. Use the status action buttons:
   - **Confirm** - Confirm the appointment
   - **Check In** - Patient has arrived
   - **Complete** - Appointment finished
   - **Cancel** - Cancel with reason

### Cancelling an Appointment

1. Open appointment details
2. Click **Cancel** button
3. Select cancellation reason:
   - Client cancelled
   - No show
   - Rescheduled
   - Weather/Emergency
   - Other
4. Enter optional notes
5. Click **Confirm**

### Rescheduling an Appointment

1. Open the appointment
2. Click **Edit**
3. Change the date/time
4. Click **Save**

**Tip:** You can also cancel and create a new appointment.

---

## Clinical Visits

Visits are the core of patient care documentation.

### Creating a New Visit

1. Click **Visits** in the sidebar
2. Click **New Visit** button
3. Fill in visit information:
   - **Patient*** (select from dropdown)
   - **Visit Type*** (Wellness, Illness, Surgery, Emergency, Follow-up)
   - **Visit Date*** (defaults to today)
   - **Chief Complaint** - Why is the patient here?
   - **Assigned Veterinarian**
4. Click **Save**

### Visit Detail Page

Once a visit is created, you'll see a tabbed interface:

**Tabs:**
- **Overview** - Visit summary
- **Vital Signs** - Temperature, weight, heart rate, etc.
- **SOAP Note** - Clinical notes
- **Diagnoses** - ICD-10 coded diagnoses
- **Prescriptions** - Medications prescribed
- **Vaccinations** - Vaccines administered
- **Procedures** - Procedures performed

### Recording Vital Signs

1. Open the visit
2. Click **Vital Signs** tab
3. Click **Add Vital Signs**
4. Enter measurements:
   - **Temperature** (°F)
   - **Weight** (lbs or kg)
   - **Heart Rate** (bpm)
   - **Respiratory Rate** (breaths/min)
   - **Blood Pressure** (systolic/diastolic)
   - **Pain Score** (0-10 scale)
   - **Body Condition Score** (1-9 scale)
   - **Mucous Membrane Color**
   - **Capillary Refill Time**
5. Click **Save**

**Normal Ranges for Cats:**
- Temperature: 100.5-102.5°F
- Heart Rate: 140-220 bpm
- Respiratory Rate: 20-30 breaths/min

---

## Medical Records

### SOAP Notes

SOAP is a standardized format for clinical notes:

**S - Subjective**
- What the client tells you
- Patient's history and symptoms
- Example: "Cat not eating for 2 days, vomiting"

**O - Objective**
- What you observe and measure
- Physical exam findings
- Vital signs and test results
- Example: "Temp 103.2°F, dehydrated, thin body condition"

**A - Assessment**
- Your professional diagnosis/opinion
- What you think is wrong
- Example: "Possible gastroenteritis, dehydration"

**P - Plan**
- What you're going to do about it
- Treatment plan
- Follow-up instructions
- Example: "Fluids, anti-nausea medication, diet change, recheck in 3 days"

**To create a SOAP note:**
1. Open the visit
2. Click **SOAP Note** tab
3. Click **Add SOAP Note**
4. Fill in each section (S, O, A, P)
5. Click **Save**

### Adding Diagnoses

1. Open the visit
2. Click **Diagnoses** tab
3. Click **Add Diagnosis**
4. Fill in:
   - **Diagnosis Name** (e.g., "Upper Respiratory Infection")
   - **ICD-10 Code** (if known)
   - **Status** (Preliminary, Confirmed, Ruled Out)
   - **Notes**
5. Click **Save**

**Common Feline ICD-10 Codes:**
- J06.9 - Upper Respiratory Infection
- K52.9 - Gastroenteritis
- N18.9 - Chronic Kidney Disease
- E11.9 - Diabetes Mellitus

### Recording Vaccinations

1. Open the visit
2. Click **Vaccinations** tab
3. Click **Record Vaccination**
4. Fill in:
   - **Vaccine Name** (e.g., "FVRCP")
   - **Manufacturer**
   - **Lot Number**
   - **Expiration Date**
   - **Site** (location on body)
   - **Route** (Subcutaneous, Intramuscular)
   - **Next Due Date** (typically 1-3 years)
5. Check for adverse reactions
6. Click **Save**

**Common Feline Vaccines:**
- FVRCP (Feline Viral Rhinotracheitis, Calicivirus, Panleukopenia)
- Rabies
- FeLV (Feline Leukemia)

**Adverse Reactions:**
If the patient has a reaction to the vaccine, check the "Adverse Reaction" box and describe the reaction.

---

## Prescriptions

### Medication Database

Before prescribing, medications must be in your database.

**To add a medication:**
1. Click **Medications** in the sidebar
2. Click **New Medication**
3. Fill in drug information:
   - **Drug Name*** (generic name)
   - **Brand Names**
   - **Drug Class**
   - **Controlled Substance** (Yes/No)
   - **DEA Schedule** (if controlled)
   - **Available Forms** (capsule, liquid, tablet)
   - **Strengths** (mg, ml)
   - **Typical Dose for Cats**
   - **Dosing Frequency**
   - **Route** (Oral, Injectable, Topical)
   - **Indications** - What it's used for
   - **Contraindications** - When NOT to use
   - **Side Effects**
   - **Warnings**
4. Click **Save**

### Writing a Prescription

1. Open a visit
2. Click **Prescriptions** tab
3. Click **New Prescription**
4. Fill in prescription details:
   - **Medication*** (select from database)
   - **Dosage*** (e.g., "100mg")
   - **Dosage Form** (capsule, tablet, liquid)
   - **Frequency*** (e.g., "Every 12 hours")
   - **Route** (Oral, Topical, etc.)
   - **Duration** (e.g., 14 days)
   - **Quantity*** (e.g., "28 capsules")
   - **Refills Allowed** (0-12)
   - **Instructions** - Directions for client
   - **Indication** - What it's treating
5. Click **Save**

**Example Instructions:**
- "Give 1 capsule by mouth every 12 hours with food for 14 days"
- "Apply thin layer to affected area twice daily"
- "Give 0.5ml by mouth once daily in the morning"

### Prescription Status

Prescriptions have these statuses:
- **Active** - Currently being used
- **Completed** - Finished the course
- **Discontinued** - Stopped early
- **On Hold** - Temporarily paused

**To discontinue a prescription:**
1. Open the prescription
2. Click **Discontinue**
3. Enter reason for discontinuation
4. Click **Confirm**

---

## Billing & Invoicing

### Service Catalog

Before creating invoices, set up your service catalog.

**To add a service:**
1. Click **Services** in the sidebar
2. Click **New Service**
3. Fill in service details:
   - **Name*** (e.g., "Wellness Exam - Feline")
   - **Description**
   - **Category** (Examination, Surgery, Diagnostic, etc.)
   - **Service Type*** (Service, Product, Vaccine)
   - **Unit Price*** (e.g., $65.00)
   - **Cost** (your cost - optional)
   - **Taxable** (Yes/No)
   - **Status** (Active/Inactive)
4. Click **Save**

**Service Categories:**
- Examination
- Surgery
- Diagnostic (X-ray, Ultrasound, Lab)
- Vaccination
- Medication/Pharmacy
- Dental
- Hospitalization
- Grooming
- Retail (food, toys, supplies)

### Creating an Invoice

1. Click **Invoices** in the sidebar
2. Click **New Invoice**
3. Fill in invoice header:
   - **Client*** (select from dropdown)
   - **Patient** (optional - select if for specific patient)
   - **Visit** (optional - link to visit)
   - **Invoice Date*** (defaults to today)
   - **Due Date** (e.g., 30 days from invoice date)
4. Add line items:
   - Click **Add Item**
   - Select **Service** from catalog OR
   - Enter custom **Description**
   - Enter **Quantity**
   - Enter **Unit Price**
   - Check **Taxable** if applicable
   - Item total calculates automatically
5. Review invoice totals:
   - **Subtotal** - Sum of all items
   - **Tax** - Applied to taxable items only
   - **Discount** (if any)
   - **Total Amount**
6. Add **Notes** (optional)
7. Click **Save**

**Invoice automatically generates a unique invoice number** (format: INV-YYYYMMDD-XXXX)

### Invoice Status

Invoices have these statuses:
- **Draft** - Not yet sent to client
- **Sent** - Sent to client, awaiting payment
- **Partial Paid** - Some payment received
- **Paid** - Fully paid
- **Overdue** - Past due date with balance

**Status updates automatically** when payments are recorded.

### Viewing Invoice Details

1. Click on an invoice from the list
2. View complete invoice with:
   - Client and patient information
   - All line items
   - Tax calculation breakdown
   - Payment history
   - Outstanding balance

### Editing an Invoice

**You can only edit Draft invoices.**

1. Open the invoice
2. Click **Edit**
3. Make changes
4. Click **Save**

**Once an invoice is "Sent" or has payments, you cannot edit it.** Create a new invoice or credit memo instead.

---

## Payment Processing

### Recording a Payment

1. Open an invoice with a balance due
2. Click **Record Payment** button
3. Fill in payment details:
   - **Amount*** (can be partial or full)
   - **Payment Date*** (defaults to today)
   - **Payment Method***:
     - Cash
     - Check
     - Credit Card
     - Debit Card
     - Bank Transfer
     - Other
   - **Reference Number** (check number, last 4 of card, confirmation #)
   - **Notes** (optional)
4. Click **Save Payment**

**What happens automatically:**
- Payment is added to invoice
- Amount Paid is updated
- Balance Due is recalculated
- Invoice status updates:
  - If full balance paid → Status = "Paid"
  - If partial payment → Status = "Partial Paid"

### Partial Payments

Clients can pay in installments:

**Example:**
- Invoice Total: $450.00
- Payment 1: $200.00 (Status → Partial Paid, Balance = $250)
- Payment 2: $250.00 (Status → Paid, Balance = $0)

**To accept partial payment:**
1. Enter the amount the client is paying (less than total)
2. Record payment as normal
3. Invoice shows remaining balance
4. Record additional payments as received

### Payment History

View all payments for an invoice:
1. Open invoice detail page
2. Scroll to **Payment History** section
3. See table with:
   - Payment date
   - Amount
   - Payment method
   - Reference number
   - Processed by (staff member)

### Deleting a Payment

**Use caution - this cannot be undone!**

1. Open invoice detail page
2. Find payment in Payment History
3. Click **Delete** icon
4. Confirm deletion

**What happens:**
- Payment is removed
- Amount Paid decreases
- Balance Due increases
- Invoice status updates accordingly

**When to delete:**
- Payment was entered incorrectly
- Check bounced
- Credit card was declined
- Duplicate payment entry

---

## Financial Reports

Access comprehensive financial analytics to track clinic performance.

### Accessing Reports

1. Click **Reports** in the sidebar
2. View the Financial Reports dashboard

### Summary Metrics

Four key cards at the top show:

**Total Revenue**
- Total revenue from paid invoices
- Number of paid invoices
- Updates based on date range

**Outstanding Balance**
- Total unpaid/partially paid invoices
- Amount clients still owe
- Critical for cash flow management

**Total Payments**
- Sum of all payments received
- All payment methods combined
- Updates based on date range

**Average Invoice**
- Average invoice amount
- Total invoices issued
- Helps track pricing trends

### Date Range Filtering

**To change date range:**
1. Select **Start Date**
2. Select **End Date**
3. Reports update automatically

**Quick Shortcuts:**
- Click **Reset to YTD** for Year-to-Date (January 1 to today)
- Use for monthly, quarterly, or annual reports

### Revenue by Period Report

**Tab 1: Revenue by Period**

View revenue trends over time:

1. Click **Revenue by Period** tab
2. Select period type:
   - **Daily** - Each day's revenue
   - **Weekly** - Each week's revenue
   - **Monthly** - Each month's revenue (default)
3. View table showing:
   - Period (date/week/month)
   - Revenue amount
   - Number of invoices

**Use this report for:**
- Tracking seasonal trends
- Identifying busy periods
- Budget planning
- Setting revenue goals

**To export:**
- Click **Export CSV** button
- Open in Excel or Google Sheets

### Outstanding Balance Report

**Tab 2: Outstanding Balance**

See which clients have unpaid invoices:

1. Click **Outstanding Balance** tab
2. View table showing:
   - Client name
   - Total amount owed
   - Number of unpaid invoices
   - Oldest invoice date (for aging)
3. Sorted by highest balance first

**Use this report for:**
- Collections follow-up
- Identifying payment issues
- Cash flow forecasting
- Accounts receivable aging

**Follow-up actions:**
- Contact clients with old balances
- Send payment reminders
- Arrange payment plans

### Payment Methods Report

**Tab 3: Payment Methods**

Analyze how clients are paying:

1. Click **Payment Methods** tab
2. View breakdown by payment type:
   - Cash
   - Check
   - Credit Card
   - Debit Card
   - Bank Transfer
   - Other
3. See total amount and transaction count for each
4. Average payment amount per method

**Use this report for:**
- Understanding client preferences
- Processing fee analysis (credit card fees)
- Cash handling requirements
- Payment terminal needs

### Service Revenue Report

**Tab 4: Service Revenue**

Identify your most profitable services:

1. Click **Service Revenue** tab
2. View services ranked by revenue:
   - Service name
   - Service type
   - Total revenue
   - Quantity sold
   - Times sold
   - Average per sale
3. Sorted by highest revenue first

**Use this report for:**
- Pricing analysis
- Marketing focus areas
- Inventory planning
- Staff training priorities

**Questions this answers:**
- What are our top revenue services?
- Which products sell best?
- Are we pricing appropriately?
- What should we promote?

### Exporting Reports

**All reports can be exported to CSV:**

1. Navigate to desired report tab
2. Click **Export CSV** button
3. File downloads automatically
4. Open in Excel, Google Sheets, or accounting software

**CSV files include:**
- All data from the current report
- Current date range in filename
- Easy to import into other systems

---

## Global Search

Quickly find clients, patients, or appointments.

### Using Global Search

**Keyboard Shortcut:**
- **Windows/Linux**: Ctrl + K
- **Mac**: Cmd + K

**Or click** the search icon in the top header.

### How to Search

1. Open search (Ctrl/Cmd + K)
2. Start typing:
   - Client name
   - Patient name
   - Phone number
   - Email address
3. Results appear as you type (debounced for performance)
4. Results are categorized:
   - **Clients** (person icon)
   - **Patients** (paw icon)
   - **Appointments** (calendar icon)
5. Click a result to navigate to that page

### Search Tips

- Search works across all entities simultaneously
- Minimum 2 characters to start searching
- Results are limited to most relevant matches
- Press ESC to close search dialog

**Example searches:**
- "Smith" - Finds clients named Smith and their pets
- "555-1234" - Finds client by phone
- "Whiskers" - Finds patients named Whiskers

---

## Tips & Best Practices

### Daily Workflow

**Morning Routine:**
1. Log in and check Dashboard
2. Review today's appointments
3. Check recent visits that need follow-up
4. Review any client alerts

**During Appointments:**
1. Check in patient on appointment
2. Create visit from appointment
3. Record vital signs immediately
4. Complete SOAP note during/after exam
5. Write prescriptions before client leaves
6. Create invoice before checkout
7. Process payment
8. Mark appointment complete

**End of Day:**
1. Complete any pending SOAP notes
2. Follow up on outstanding invoices
3. Prepare for next day's appointments
4. Review any pending tasks

### Data Entry Best Practices

**Be Consistent:**
- Use standard abbreviations
- Format phone numbers the same way
- Use complete sentences in SOAP notes
- Date format: MM/DD/YYYY

**Be Thorough:**
- Complete all required fields
- Add notes when relevant
- Document everything in SOAP notes
- Record ALL medications and vaccines

**Be Accurate:**
- Double-check client contact info
- Verify patient weight and vitals
- Confirm medication dosages
- Review invoices before sending

### Client Communication

**Professional Communication:**
- Use clear, jargon-free language in client notes
- Document all client interactions
- Note client preferences and concerns
- Follow up on promises made

**Payment Discussions:**
- Provide estimates before procedures
- Explain invoices line by line if needed
- Offer payment plans for large balances
- Be consistent with payment policies

### Security & Privacy

**Protecting Client Data:**
- Log out when leaving workstation
- Never share passwords
- Don't access records you don't need
- Report any data breaches immediately

**HIPAA Compliance:**
- Veterinary records may not be HIPAA-covered, but treat with same care
- Don't discuss cases in public areas
- Secure all printed materials
- Use secure communication channels

### Common Shortcuts

**Navigation:**
- Dashboard: Click logo in top left
- Back: Use browser back button or breadcrumbs
- Search: Ctrl/Cmd + K

**Forms:**
- Save: Usually Ctrl/Cmd + Enter (if supported)
- Cancel: ESC key
- Required fields: Look for red asterisk (*)

### Troubleshooting

**Can't find a client/patient:**
- Use Global Search (Ctrl/Cmd + K)
- Check spelling
- Try partial name match
- Search by phone number

**Invoice totals don't match:**
- Check tax rate settings
- Verify which items are taxable
- Ensure quantities are correct
- Recalculate if needed

**Payment not updating invoice:**
- Refresh the page
- Check that payment saved successfully
- Verify payment amount
- Contact support if issue persists

**Appointment not showing on calendar:**
- Check date/time are correct
- Verify it wasn't cancelled
- Try refreshing calendar
- Check calendar view (day/week/month)

---

## Getting Help

**System Support:**
- Contact your system administrator
- Check TESTING_GUIDE.md for technical details
- Report bugs to development team

**Training:**
- Review this user guide periodically
- Ask experienced staff for tips
- Attend training sessions
- Practice with test data

**Feedback:**
- Suggest improvements to workflows
- Report confusing features
- Share best practices with team
- Help improve the system

---

## Appendix

### Glossary

**BCS (Body Condition Score)** - 9-point scale assessing body fat (1=emaciated, 9=obese, 5=ideal)

**Chief Complaint** - Primary reason for the visit

**ICD-10** - International Classification of Diseases, 10th revision - standardized diagnosis codes

**Invoice** - Bill for services rendered

**Line Item** - Individual item on an invoice

**SOAP** - Subjective, Objective, Assessment, Plan - clinical note format

**Vital Signs** - Basic physiological measurements (temp, HR, RR, etc.)

### Keyboard Shortcuts

| Action | Windows/Linux | Mac |
|--------|---------------|-----|
| Global Search | Ctrl + K | Cmd + K |
| Close Dialog | ESC | ESC |
| Save Form | Ctrl + Enter | Cmd + Enter |
| Navigate Back | Backspace | Delete |

### Common Cat Vital Sign Ranges

| Vital Sign | Normal Range |
|------------|--------------|
| Temperature | 100.5-102.5°F |
| Heart Rate | 140-220 bpm |
| Respiratory Rate | 20-30 breaths/min |
| Capillary Refill | < 2 seconds |
| Body Condition Score | 4-5 / 9 (ideal) |

### Invoice Status Flow

```
Draft → Sent → Partial Paid → Paid
              ↓
           Overdue (if past due date)
```

### Appointment Status Flow

```
Pending → Confirmed → Checked In → In Progress → Completed
                                              ↓
                                          Cancelled
```

---

**Thank you for using the Lenox Cat Hospital Practice Management System!**

*This guide is version 2.0 and reflects Phase 1 & 2 functionality.*
*Last updated: October 2025*
