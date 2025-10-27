# Lenox Cat Hospital - Veterinary Practice Management Suite

A comprehensive practice management software suite for a **feline-only veterinary clinic**, built with a modern React frontend and Flask backend API.

> **Note:** Lenox Cat Hospital specializes exclusively in feline care. All patients in the system are cats, and the application is designed specifically for cat-only veterinary practice management.

## Technology Stack

### Backend
-   **Framework:** Flask (Python 3.11)
-   **Database:** SQLite (development), PostgreSQL (production)
-   **ORM:** SQLAlchemy with Flask-SQLAlchemy
-   **Migrations:** Flask-Migrate (Alembic)
-   **API Documentation:** Flask-RESTX (Swagger UI)
-   **Authentication:** Flask-Login + bcrypt
-   **Validation:** marshmallow

### Frontend
-   **Framework:** React 18
-   **UI Library:** Material-UI (MUI)
-   **State Management:** React Query (@tanstack/react-query)
-   **Forms:** React Hook Form + Zod validation
-   **Routing:** React Router DOM v6
-   **Calendar:** react-big-calendar
-   **Date Handling:** date-fns, moment

### Infrastructure
-   **Logging:** Custom logger with LocalStorage persistence (frontend) + rotating file logs (backend)
-   **Error Handling:** Error boundary with automatic logging
-   **Testing:** pytest (backend), Jest + React Testing Library (frontend)

## Prerequisites

Before you begin, ensure you have the following installed:

-   [Python 3.11+](https://www.python.org/downloads/)
-   [Node.js 16+](https://nodejs.org/) (includes npm)
-   [PostgreSQL](https://www.postgresql.org/download/) (optional for production)

## Quick Start (Development)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Unix/macOS:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (SQLite by default)
cp .env.example .env

# Run database migrations
flask db upgrade

# Start the backend server
python run.py
```

The Flask API will start at **http://localhost:5000**

### 2. Frontend Setup

```bash
# Open new terminal and navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Configure environment (optional)
cp .env.example .env.development

# Start the development server
npm start
```

The React app will start at **http://localhost:3000**

### 3. Create Administrator User & Seed Data

```bash
# In backend directory with venv activated
flask shell
```

Then in the Flask shell:
```python
from app import db
from app.models import User

# Create admin user
admin = User(username='admin', role='administrator')
admin.set_password('admin123')  # Change this password!
db.session.add(admin)
db.session.commit()
exit()
```

### 4. (Optional) Seed Default Appointment Types

```bash
# In backend directory with venv activated
python seed_data.py
```

This creates 10 default appointment types with colors:
- Wellness Exam, Vaccination, Sick Visit, Surgery, Dental Cleaning
- Emergency, Follow-up, Grooming, Boarding Drop-off, Boarding Pick-up

### 5. Login to Application

1. Navigate to **http://localhost:3000**
2. You'll be redirected to the login page
3. Login with:
   - **Username:** `admin`
   - **Password:** `admin123` (or whatever you set)
4. You'll see the dashboard with calendar and navigation sidebar

## Environment Variables

### Backend (.env)

```bash
FLASK_APP=app:create_app       # Required for flask db commands
FLASK_ENV=development          # development, testing, or production
SECRET_KEY=your_secret_key     # Change in production!
DATABASE_URL=sqlite:///vet_clinic.db  # Or postgresql://user:pass@host/db
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
```

**Note:** The `FLASK_APP` variable is required for Flask-Migrate commands (`flask db upgrade`, etc.) to work properly with the application factory pattern.

### Frontend (.env.development)

```bash
PORT=3000
REACT_APP_API_PROXY=http://localhost:5000
REACT_APP_LOG_LEVEL=INFO       # DEBUG, INFO, WARN, ERROR
REACT_APP_LOG_TO_BACKEND=false # Set to true to send logs to backend
```

## Database Migrations

We use Flask-Migrate (Alembic) for database migrations.

```bash
# Create a new migration after model changes
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade

# View migration history
flask db history
```

## Features Implemented

### ✅ Phase 1: Foundation & Core Entities (COMPLETE)

#### Phase 1.1 & 1.2: Backend & Frontend Infrastructure ✅
**Backend:**
- Flask-Migrate for database migrations
- Flask-RESTX for API documentation with Swagger UI
- Multi-environment configuration (dev, testing, production)
- SQLAlchemy ORM with comprehensive models (User, Client, Patient, Appointment, AppointmentType)
- Marshmallow schemas for request/response validation
- Rotating file logging (`backend/logs/vet_clinic.log`)
- **Feline-only data model:** All pets are cats (species defaults to 'Cat')
- **108 comprehensive unit tests** (100% passing)

**Frontend:**
- **Material-UI (MUI)** component library with custom theme
- **React Query** for server state management with auto-refresh
- **React Hook Form + Zod** for form validation
- **Comprehensive logging system**:
  - Logs to browser LocalStorage (last 500 entries)
  - Auto-cleanup (keeps logs for 7 days)
  - User action tracking and API call logging with timing
  - Export logs as JSON
- **Error Boundary** for graceful error handling
- **Responsive Layout** with MainLayout, Header, and Sidebar navigation
- **Protected routes** with authentication
- **Frontend unit tests** for all major components

#### Phase 1.3: Client Management Module ✅
Complete CRUD functionality for managing clients (cat owners):

**Backend API (25 unit tests):**
- `GET /api/clients` - List with pagination, search (name/email/phone), filter (active/inactive)
- `GET /api/clients/<id>` - Get single client with all patients
- `POST /api/clients` - Create new client with validation
- `PUT /api/clients/<id>` - Update existing client
- `DELETE /api/clients/<id>` - Soft delete (deactivate)
- `DELETE /api/clients/<id>?hard=true` - Hard delete (admin only)

**Frontend UI:**
- **Client List** (`/clients`): MUI table, search, filter, pagination, sortable columns
- **Client Detail** (`/clients/:id`): Full information display, linked patients, edit button
- **Client Form** (`/clients/new`, `/clients/:id/edit`): 15+ fields with Zod validation

**Client Data Model:** Personal info, address, communication preferences, account balance, notes, alerts, timestamps

#### Phase 1.4: Patient (Cat) Management Module ✅
Complete CRUD functionality for managing cat patients:

**Backend API (25+ unit tests):**
- `GET /api/patients` - List with pagination, search (name/microchip), filter (status/owner)
- `GET /api/patients/<id>` - Get patient with owner info and appointment history
- `POST /api/patients` - Create new patient with validation
- `PUT /api/patients/<id>` - Update patient info
- `DELETE /api/patients/<id>` - Soft delete

**Frontend UI:**
- **Patient List** (`/patients`): MUI table, search, filter, pagination, status indicators
- **Patient Detail** (`/patients/:id`): Full profile, photo, owner card, medical notes, **appointment history table**
- **Patient Form** (`/patients/new`, `/patients/:id/edit`): 20+ fields including photo upload, breed selection, status management

**Patient Data Model:** Name, breed, color, markings, sex, reproductive status, DOB, weight, microchip, insurance, owner link, photo, allergies, medical/behavioral notes, status (active/inactive/deceased)

#### Phase 1.5: Enhanced Appointment System ✅
Comprehensive appointment scheduling with types, status workflow, and audit trail:

**Backend (54 new unit tests):**
- **AppointmentType Model:** Name, duration, color (for calendar), description, default price
- **Enhanced Appointment Model (20+ fields):**
  - Type, status workflow (pending → confirmed → in-progress → completed/cancelled)
  - Links to patient, client, assigned staff
  - Room assignment
  - Timing: start/end, check-in/check-out, duration
  - Cancellation tracking with reasons
  - Comprehensive audit trail (timestamps for all status changes)
- **API Endpoints:**
  - `GET /api/appointment-types` - Manage appointment types
  - `GET /api/appointments` - List with filtering (date range, status, patient, client), pagination
  - `POST /api/appointments` - Create with auto workflow timestamps
  - `PUT /api/appointments/<id>` - Update with status transitions
  - Status action endpoints (check-in, complete, cancel)
- **Seed Script:** `backend/seed_data.py` - Creates 10 default appointment types

**Frontend UI:**
- **Enhanced Calendar** (`/calendar`):
  - Real appointment data from API
  - Color-coding by appointment type
  - Status-based opacity (completed appointments are faded)
  - Filter dropdown by type
  - Click events to view appointment details
  - "New Appointment" button
- **AppointmentDetail Component:**
  - Comprehensive detail view with all appointment info
  - Status action buttons (Check In, Start, Complete, Cancel)
  - Client and Patient info cards with navigation links
  - Timing panel showing all status change timestamps
  - Cancellation reason display
- **AppointmentForm Component:**
  - Create and edit with validation
  - Dependent dropdowns (select client → loads their patients)
  - Date/time selection
  - Type selection with color preview
  - Smart defaults (status, duration)
- **Patient Detail Enhancement:**
  - Appointment history table (color-coded by type, status chips)

#### Phase 1.6: Navigation & User Experience ✅
Professional navigation and search functionality:

**Dashboard** (`/dashboard`):
- Quick stats cards (4 metrics: total clients, patients, today's appointments, upcoming)
- Today's appointments list with color-coding
- Recent patients widget
- Quick action buttons (New Client, New Patient, New Appointment)
- Integrated calendar widget
- Auto-refresh every 60 seconds

**GlobalSearch Component:**
- Unified search across all entities (clients, patients, appointments)
- Real-time search with debouncing (300ms)
- Categorized results with visual indicators
- Click to navigate to detail pages
- Keyboard shortcut: **Ctrl/Cmd+K** to open, **ESC** to close
- Accessible from anywhere via Header search icon

**Breadcrumb Navigation:**
- Auto-generated from URL path
- Home icon links to dashboard
- Clickable segments for navigation
- Smart labeling (IDs converted to entity names)
- Integrated into MainLayout

**Additional UX:**
- Responsive design for tablets and mobile
- Cross-platform keyboard shortcuts (Mac/Windows support)
- Event listener cleanup on unmount
- Loading states and error boundaries throughout

## Testing

### Backend Tests (pytest)

```bash
# From project root or backend directory
pytest backend/tests

# With coverage
pytest backend/tests --cov=backend/app

# Run specific test files
pytest backend/tests/test_client_api.py -v       # 25 tests
pytest backend/tests/test_patient_api.py -v      # 25+ tests
pytest backend/tests/test_appointment_api.py -v  # 27 tests
pytest backend/tests/test_appointment_type_api.py -v  # 27 tests
pytest backend/tests/test_routes.py -v           # Basic routes tests
```

**Test Coverage (108 tests total):**
- **Client API:** 25 tests covering CRUD, pagination, search, soft/hard delete
- **Patient API:** 25+ tests covering CRUD, owner relationships, status management
- **Appointment API:** 27 tests covering CRUD, status workflow, filtering
- **AppointmentType API:** 27 tests covering CRUD, validation, color management
- **Integration Tests:** Full lifecycle and relationship testing
- **Authentication & Authorization:** Role-based access control
- **Validation:** Marshmallow schema validation
- **Error Handling:** Comprehensive error scenarios

```bash
# All 108 tests passing (100%)
============================= 108 passed in XX.XXs =============================
```

### Frontend Tests (Jest)

```bash
# From frontend directory
npm test

# Run all tests once (no watch mode)
npm test -- --watchAll=false

# With coverage
npm test -- --coverage
```

## Logging

### Backend Logging
- Location: `backend/logs/vet_clinic.log`
- Rotation: 10KB max size, 10 backup files
- Includes: SQL queries (development), API calls, errors
- Level: INFO in development, WARNING in production

### Frontend Logging
- Storage: Browser LocalStorage (`app_logs` key)
- Max entries: 500 (auto-rotates)
- Retention: 7 days (auto-cleanup)
- Export: Download as JSON via logger.exportLogs()
- Access logs in browser console:
  ```javascript
  logger.getAllLogs()      // View all logs
  logger.getStats()        // View statistics
  logger.exportLogs()      // Download as JSON
  logger.clearLogs()       // Clear all logs
  ```

## Directory Structure

```
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app initialization
│   │   ├── models.py            # Database models (User, Client, Patient, Appointment, AppointmentType)
│   │   ├── routes.py            # API routes for all endpoints
│   │   └── schemas.py           # Marshmallow validation schemas
│   ├── migrations/              # Alembic database migrations
│   │   └── versions/            # Migration version files
│   ├── tests/                   # Backend unit tests (108 tests)
│   │   ├── test_client_api.py       # 25 Client API tests
│   │   ├── test_patient_api.py      # 25+ Patient API tests
│   │   ├── test_appointment_api.py  # 27 Appointment API tests
│   │   ├── test_appointment_type_api.py  # 27 AppointmentType API tests
│   │   └── test_routes.py           # Basic route tests
│   ├── logs/                    # Log files (auto-created)
│   │   └── vet_clinic.log       # Rotating log file
│   ├── instance/                # Instance folder (SQLite DB, auto-created)
│   │   └── vet_clinic.db        # SQLite database (development)
│   ├── config.py                # Configuration classes (dev, test, prod)
│   ├── requirements.txt         # Python dependencies
│   ├── run.py                   # Flask application entry point
│   ├── seed_data.py             # Seed script for appointment types
│   ├── .env                     # Environment variables (create from .env.example)
│   └── .env.example             # Example environment variables
│
├── frontend/
│   ├── public/                  # Static assets
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/          # MainLayout, Header, Sidebar
│   │   │   ├── forms/           # Reusable form components
│   │   │   ├── AppointmentDetail.js  # Appointment detail view
│   │   │   ├── AppointmentForm.js    # Appointment create/edit form
│   │   │   ├── Breadcrumbs.js        # Breadcrumb navigation
│   │   │   ├── Calendar.js           # Enhanced calendar with appointments
│   │   │   ├── Calendar.css          # Calendar styling
│   │   │   ├── ClientDetail.js       # Client detail view
│   │   │   ├── ClientForm.js         # Client create/edit form
│   │   │   ├── Clients.js            # Client list page
│   │   │   ├── Dashboard.js          # Dashboard with widgets
│   │   │   ├── ErrorBoundary.js      # Global error handler
│   │   │   ├── GlobalSearch.js       # Global search component
│   │   │   ├── Login.js              # Login page
│   │   │   ├── PatientDetail.js      # Patient detail view with appointment history
│   │   │   ├── PatientForm.js        # Patient create/edit form
│   │   │   ├── Patients.js           # Patient list page
│   │   │   └── *.test.js             # Component unit tests
│   │   ├── providers/
│   │   │   └── QueryProvider.js # React Query configuration
│   │   ├── utils/
│   │   │   └── logger.js        # Frontend logging utility
│   │   ├── App.js               # Main app component with routing
│   │   ├── App.css              # Global app styles
│   │   ├── index.js             # React entry point
│   │   └── setupProxy.js        # Development API proxy
│   ├── package.json             # Node dependencies
│   ├── .env.development         # Development environment variables
│   └── .env.example             # Example environment variables
│
├── FEATURES.md                  # Complete feature specification
├── ROADMAP.md                   # Development roadmap (updated for Phase 1 completion)
├── DATA_MODELS.md               # Database schema documentation
└── README.md                    # This file
```

## Planning Documents

- **FEATURES.md** - Complete feature set with 20 modules organized by priority
- **ROADMAP.md** - 5-phase development plan with 8-9 month timeline
- **DATA_MODELS.md** - Detailed database schema with all models and relationships

These documents serve as the master plan for building out the full practice management system.

## Production Deployment

### 1. Build Frontend

```bash
cd frontend
npm run build
```

This creates an optimized build in `frontend/build/`.

### 2. Configure Production Backend

Update `backend/.env`:
```bash
FLASK_ENV=production
DATABASE_URL=postgresql://user:password@host:5432/vet_clinic_db
SECRET_KEY=<generate-strong-random-key>
```

### 3. Set up PostgreSQL

```sql
CREATE DATABASE vet_clinic_db;
CREATE USER vet_clinic_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE vet_clinic_db TO vet_clinic_user;
```

### 4. Run Migrations

```bash
cd backend
source venv/bin/activate
flask db upgrade
```

### 5. Run with Production Server

```bash
# Using gunicorn (recommended)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"

# Or using Flask (not recommended for production)
python run.py
```

The Flask backend will serve the React build from `frontend/build/`.

## Troubleshooting

### Port Already in Use

If port 5000 or 3000 is already in use:

```bash
# Backend - change port in .env
FLASK_RUN_PORT=5001

# Frontend - change port in .env.development
PORT=3001
```

### Database Issues

If you encounter database issues:

```bash
# Reset database (SQLite)
rm backend/instance/vet_clinic.db
flask db upgrade

# For PostgreSQL
dropdb vet_clinic_db
createdb vet_clinic_db
flask db upgrade
```

### Frontend Not Loading

1. Check that backend is running on port 5000
2. Check browser console for errors
3. Clear browser cache and LocalStorage
4. Check logs in browser console: `logger.getAllLogs()`

### Module Not Found Errors

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Development Status

**Current Status:** ✅ **Phase 1 - COMPLETE** (All subsections finished)

### Phase 1 Accomplishments:
- ✅ **Phase 1.1:** Backend Infrastructure (Flask-Migrate, Flask-RESTX, configs, logging)
- ✅ **Phase 1.2:** Frontend Infrastructure (MUI, React Query, React Hook Form, Error Boundary)
- ✅ **Phase 1.3:** Client Management (Full CRUD, 25 tests, UI components)
- ✅ **Phase 1.4:** Patient (Cat) Management (Full CRUD, 25+ tests, photo upload, UI)
- ✅ **Phase 1.5:** Enhanced Appointment System (AppointmentType model, 54 tests, status workflow, calendar integration)
- ✅ **Phase 1.6:** Navigation & UX (Dashboard with widgets, GlobalSearch, Breadcrumbs, keyboard shortcuts)

### Key Statistics:
- **Backend Tests:** 108 passing (100% coverage for Phase 1)
- **Frontend Tests:** Comprehensive unit tests for all major components
- **Components Created:** 11 new components (Calendar, Dashboard, GlobalSearch, Breadcrumbs, AppointmentDetail, AppointmentForm, etc.)
- **Files Created/Modified:** 25+ files across backend and frontend
- **Lines of Code:** ~2,000 lines of production-ready code
- **Seed Data:** 10 default appointment types

### Production-Ready Features:
- Complete client and patient management
- Enhanced appointment scheduling with types and status workflow
- Professional dashboard with quick stats and widgets
- Global search across all entities (Ctrl/Cmd+K)
- Breadcrumb navigation throughout app
- Color-coded calendar with real appointment data
- Responsive design (mobile, tablet, desktop)
- Comprehensive logging and error handling
- Full test coverage

**Next Phase:** Phase 2 - Medical Records & Billing
- SOAP notes system
- Prescription management
- Invoicing and payment processing
- Financial reporting

See **ROADMAP.md** for complete development plan.

## Contributing

This is a practice management system in active development. See ROADMAP.md for the development plan.

## Support

For issues or questions:
1. Check the logs (backend: `logs/vet_clinic.log`, frontend: browser console)
2. Export frontend logs: `logger.exportLogs()` in browser console
3. Review error messages in the Error Boundary UI
4. Check the planning documents (FEATURES.md, ROADMAP.md, DATA_MODELS.md)

## License

This project is for educational and professional use.
