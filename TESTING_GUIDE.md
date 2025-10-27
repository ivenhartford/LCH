# LCH Application - Testing Guide

## Server Status ✅

- **Backend**: Running on http://127.0.0.1:5000 (Flask Development Server)
- **Frontend**: Running on http://localhost:3000 (React Development Server)
- **Database**: SQLite (instance/clinic.db)

## Test Credentials

The application should have default users created. If not, you'll need to register first.

**Default Admin User** (if seeded):
- Username: `admin`
- Password: `admin123`

If you need to create a new user, use the registration endpoint:
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

---

## Testing Workflow

### 1. Authentication & Dashboard ✅

**What to Test:**
- [ ] Login page loads at http://localhost:3000
- [ ] Login with valid credentials
- [ ] Dashboard displays with 4 metric cards
- [ ] Today's appointments widget
- [ ] Recent patients widget
- [ ] Quick action buttons work
- [ ] Global search (Ctrl/Cmd+K)

**How to Test:**
1. Open http://localhost:3000 in your browser
2. You should see the login page
3. Enter credentials and click "Login"
4. Dashboard should load with summary stats

---

### 2. Client Management (Phase 1) ✅

**What to Test:**
- [ ] Navigate to Clients from sidebar
- [ ] Client list displays
- [ ] Search/filter clients
- [ ] Create new client
- [ ] Edit existing client
- [ ] View client detail page
- [ ] Add client notes
- [ ] Set client alerts

**Test Data Example:**
```
Name: Jane Smith
Email: jane.smith@example.com
Phone: (555) 123-4567
Address: 123 Main St, Boston, MA 02101
```

**How to Test:**
1. Click "Clients" in sidebar
2. Click "New Client" button
3. Fill in form with test data
4. Save and verify client appears in list
5. Click client name to view details
6. Test search by typing client name
7. Edit client and save changes

---

### 3. Patient Management (Phase 1) ✅

**What to Test:**
- [ ] Navigate to Patients from sidebar
- [ ] Patient list displays
- [ ] Create new patient (linked to client)
- [ ] Edit patient details
- [ ] View patient profile
- [ ] Upload patient photo
- [ ] Change patient status (active/inactive/deceased)
- [ ] View appointment history on patient detail

**Test Data Example:**
```
Name: Whiskers
Species: Cat
Breed: Domestic Shorthair
Sex: Male (neutered)
Date of Birth: 2020-05-15
Weight: 12.5 lbs
Microchip: 123456789012345
```

**How to Test:**
1. Click "Patients" in sidebar
2. Click "New Patient" button
3. Select client from dropdown
4. Fill in patient details
5. Save and view patient profile
6. Test photo upload (if available)
7. View appointment history

---

### 4. Appointment System (Phase 1) ✅

**What to Test:**
- [ ] Calendar view displays
- [ ] Create new appointment
- [ ] Edit appointment
- [ ] View appointment detail
- [ ] Status workflow (pending → confirmed → in-progress → completed)
- [ ] Appointment type color-coding
- [ ] Filter appointments by type/status
- [ ] Check-in appointment
- [ ] Complete appointment
- [ ] Cancel appointment (with reason)

**Test Data Example:**
```
Type: Wellness Exam
Client: (select from dropdown)
Patient: (select from dropdown)
Date/Time: Tomorrow at 10:00 AM
Assigned Staff: Dr. Smith
Duration: 30 minutes
```

**How to Test:**
1. Click "Calendar" in sidebar
2. Click empty time slot or "New Appointment" button
3. Fill in appointment form
4. Save and verify it appears on calendar
5. Click appointment to view details
6. Test status changes (check-in, complete)
7. Try filtering by appointment type
8. Test cancellation with reason

---

### 5. Visit & Medical Records (Phase 2.1-2.2) ✅

**What to Test:**
- [ ] Navigate to Visits
- [ ] Create new visit
- [ ] Add vital signs
- [ ] Write SOAP note
- [ ] Add diagnoses with ICD-10 codes
- [ ] Record vaccinations
- [ ] View visit history
- [ ] Adverse reactions tracking

**Test SOAP Note:**
```
Subjective: Cat not eating well for 2 days, seems lethargic
Objective: Temp 103.2°F, Weight 11.8 lbs (down from 12.5)
Assessment: Possible URI, mild dehydration
Plan: Fluids, appetite stimulant, recheck in 3 days
```

**Test Vital Signs:**
```
Temperature: 103.2°F
Weight: 11.8 lbs
Heart Rate: 180 bpm
Respiratory Rate: 32 breaths/min
Pain Score: 2/10
BCS: 5/9
```

**How to Test:**
1. Click "Visits" in sidebar
2. Create new visit for a patient
3. Click on visit to view detail
4. Go to "Vital Signs" tab and add vitals
5. Go to "SOAP Note" tab and write notes
6. Go to "Diagnoses" tab and add diagnosis
7. Go to "Vaccinations" tab and record vaccine
8. Verify all data saves correctly

---

### 6. Prescription Management (Phase 2.3) ✅

**What to Test:**
- [ ] Navigate to Medications
- [ ] View medication database
- [ ] Create new medication
- [ ] Search/filter medications
- [ ] Write prescription from visit
- [ ] Prescription status tracking
- [ ] Refills management
- [ ] Dosage calculator

**Test Medication:**
```
Drug Name: Gabapentin
Brand Names: Neurontin
Drug Class: Anticonvulsant
Strengths: 100mg, 300mg capsules
Typical Dose: 5-10mg/kg q8-12h
Indications: Chronic pain, seizures
```

**Test Prescription:**
```
Medication: Gabapentin
Dosage: 100mg
Frequency: Every 12 hours
Route: Oral
Duration: 30 days
Quantity: 60 capsules
Refills: 2
Instructions: Give 1 capsule by mouth every 12 hours with food
```

**How to Test:**
1. Click "Medications" in sidebar
2. Create new medication entry
3. Go to a Visit detail page
4. Click "Prescriptions" tab
5. Click "New Prescription"
6. Select medication, enter dosage
7. Save and verify prescription appears
8. Test dosage calculator (if available)

---

### 7. Services & Invoicing (Phase 2.4) ✅

**What to Test:**
- [ ] Navigate to Services
- [ ] Create service catalog items
- [ ] Edit service pricing
- [ ] Filter by type/category/status
- [ ] Navigate to Invoices
- [ ] Create new invoice
- [ ] Add line items from services
- [ ] Tax calculation
- [ ] Invoice status tracking
- [ ] View invoice detail

**Test Services:**
```
Service 1:
  Name: Wellness Exam - Feline
  Type: Service
  Category: Examination
  Unit Price: $65.00
  Taxable: No

Service 2:
  Name: Rabies Vaccine
  Type: Vaccine
  Category: Vaccination
  Unit Price: $25.00
  Taxable: No

Service 3:
  Name: Premium Cat Food
  Type: Product
  Category: Retail
  Unit Price: $45.00
  Taxable: Yes
```

**Test Invoice:**
```
Client: (select)
Patient: (select)
Items:
  - Wellness Exam - Feline: 1 x $65.00
  - Rabies Vaccine: 1 x $25.00
  - Premium Cat Food: 2 x $45.00
Tax Rate: 6.25% (on taxable items only)
```

**How to Test:**
1. Click "Services" in sidebar
2. Create 3-5 service catalog items
3. Click "Invoices" in sidebar
4. Click "New Invoice"
5. Select client and patient
6. Add line items from service catalog
7. Verify tax calculation (only on taxable items)
8. Save invoice
9. Click invoice to view detail
10. Verify all amounts calculate correctly

---

### 8. Payment Processing (Phase 2.5) ✅

**What to Test:**
- [ ] View invoice detail
- [ ] Record payment
- [ ] Multiple payment methods
- [ ] Partial payments
- [ ] Full payments
- [ ] Payment history
- [ ] Delete payment
- [ ] Invoice status auto-update

**Test Payments:**
```
Payment 1:
  Amount: $100.00
  Method: Cash
  Date: Today
  Note: Partial payment

Payment 2:
  Amount: $80.00
  Method: Credit Card
  Date: Today
  Reference: 1234-5678-9012
  Note: Final payment
```

**How to Test:**
1. Open an invoice with balance due
2. Click "Record Payment" button
3. Enter payment amount (less than total for partial)
4. Select payment method
5. Add reference number and notes
6. Save payment
7. Verify invoice status changes to "partial_paid"
8. Add another payment for remaining balance
9. Verify status changes to "paid"
10. Test delete payment
11. Verify balance recalculates

---

### 9. Financial Reports (Phase 2.6) ✅ NEW!

**What to Test:**
- [ ] Navigate to Reports
- [ ] View financial summary cards
- [ ] Set date range filter
- [ ] Revenue by Period tab
- [ ] Change period (daily/weekly/monthly)
- [ ] Outstanding Balance tab
- [ ] Payment Methods tab
- [ ] Service Revenue tab
- [ ] CSV export for each report

**How to Test:**
1. Click "Reports" in sidebar (bottom section)
2. Verify 4 summary cards display:
   - Total Revenue
   - Outstanding Balance
   - Total Payments
   - Average Invoice
3. Test date range filter:
   - Set start date to 3 months ago
   - Set end date to today
   - Verify data updates
4. **Revenue by Period Tab:**
   - Click "Revenue by Period" tab
   - Change period dropdown (daily/weekly/monthly)
   - Verify data groups correctly
   - Click "Export CSV" button
5. **Outstanding Balance Tab:**
   - Click "Outstanding Balance" tab
   - Verify clients with unpaid invoices show
   - Check oldest invoice dates
   - Export to CSV
6. **Payment Methods Tab:**
   - Click "Payment Methods" tab
   - Verify breakdown by payment type
   - Check totals and counts
   - Export to CSV
7. **Service Revenue Tab:**
   - Click "Service Revenue" tab
   - Verify services ranked by revenue
   - Check quantity and times sold
   - Export to CSV

---

## Common Issues & Solutions

### Login Issues
- **Problem**: Can't log in with default credentials
- **Solution**: Register a new user first using the registration endpoint or check if admin user exists

### Data Not Appearing
- **Problem**: Lists are empty
- **Solution**: Create test data following the testing workflow above

### Server Errors
- **Problem**: 500 Internal Server Error
- **Solution**: Check backend terminal for error logs

### Port Already in Use
- **Problem**: Can't start servers
- **Solution**: Kill existing processes:
```bash
# Kill backend
lsof -ti:5000 | xargs kill -9
# Kill frontend
lsof -ti:3000 | xargs kill -9
```

---

## Testing Checklist Summary

### Phase 1 Features ✅
- [x] Authentication & Dashboard
- [x] Client Management (CRUD)
- [x] Patient Management (CRUD)
- [x] Appointment System (Calendar, Status Workflow)
- [x] Global Search (Ctrl/Cmd+K)
- [x] Navigation & Breadcrumbs

### Phase 2 Features ✅
- [x] Visit Management
- [x] SOAP Notes
- [x] Vital Signs
- [x] Diagnoses (ICD-10)
- [x] Vaccinations
- [x] Medication Database
- [x] Prescriptions
- [x] Service Catalog
- [x] Invoicing System
- [x] Payment Processing
- [x] Financial Reports (NEW!)

---

## Next Steps After Testing

1. **Report Issues**: Note any bugs or issues encountered
2. **Review UX**: Provide feedback on user experience
3. **Data Validation**: Test edge cases and validation
4. **Performance**: Test with larger datasets
5. **Decision**: Continue to Phase 3 or refine Phase 2

---

## Quick Test Data Script

If you want to quickly populate test data via API:

```bash
# Create a client
curl -X POST http://localhost:5000/api/clients \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "name": "Test Client",
    "email": "test@example.com",
    "phone": "555-1234",
    "address": "123 Test St",
    "city": "Boston",
    "state": "MA",
    "zip_code": "02101"
  }'
```

---

**Happy Testing! 🎉**

For any issues or questions, check the server logs in the terminal.
