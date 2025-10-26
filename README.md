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

### 3. Create Administrator User

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

### 4. Login to Application

1. Navigate to **http://localhost:3000**
2. You'll be redirected to the login page
3. Login with:
   - **Username:** `admin`
   - **Password:** `admin123` (or whatever you set)
4. You'll see the dashboard with calendar and navigation sidebar

## Environment Variables

### Backend (.env)

```bash
FLASK_ENV=development          # development, testing, or production
SECRET_KEY=your_secret_key     # Change in production!
DATABASE_URL=sqlite:///vet_clinic.db  # Or postgresql://user:pass@host/db
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
```

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

## Features Implemented (Phase 1.1)

### ✅ Backend Infrastructure
- Flask-Migrate for database migrations
- Flask-RESTX for API documentation (in progress)
- Multi-environment configuration (dev, testing, production)
- SQLAlchemy ORM with models for User, Pet (Cat patients), Appointment, Client
- Rotating file logging (`logs/vet_clinic.log`)
- Input validation with marshmallow
- **Feline-only data model:** All pets are cats (species defaults to 'Cat')

### ✅ Frontend Infrastructure
- **Material-UI** component library with custom theme
- **React Query** for server state management
- **Comprehensive logging system**:
  - Logs to browser LocalStorage (last 500 entries)
  - Auto-cleanup (keeps logs for 7 days)
  - User action tracking
  - API call logging with timing
  - Export logs as JSON
  - Global error handlers
- **Error Boundary** for graceful error handling
- **Responsive Layout** with sidebar navigation
- **Form system** with React Hook Form + Zod validation
- **Protected routes** with authentication

### ✅ User Interface
- Login page
- Dashboard with appointment calendar
- Sidebar navigation (11 routes):
  - Dashboard, Calendar, Clients, Patients, Medical Records
  - Appointments, Invoices, Inventory, Staff, Reports, Settings
- Header with user menu and logout
- Mobile-responsive design

## Features Implemented (Phase 1.2)

### ✅ Client Management Module
Complete CRUD functionality for managing clients (cat owners):

**Backend API:**
- `GET /api/clients` - List clients with pagination, search, and filtering
  - Search by name, email, or phone
  - Filter by active/inactive status
  - Pagination support (configurable page size)
- `GET /api/clients/<id>` - Get single client details
- `POST /api/clients` - Create new client
- `PUT /api/clients/<id>` - Update existing client
- `DELETE /api/clients/<id>` - Soft delete (deactivate) client
- `DELETE /api/clients/<id>?hard=true` - Hard delete (admin only)
- Marshmallow schemas for request/response validation
- Comprehensive error handling and logging
- **25 comprehensive unit tests** covering all endpoints (100% passing)

**Client Data Model:**
- Personal info (first name, last name, email, phones)
- Address (line 1, line 2, city, state, ZIP)
- Communication preferences (email/phone/SMS, reminders)
- Account balance and credit limit
- Notes and alerts
- Active/inactive status
- Timestamps (created_at, updated_at)

**Frontend UI:**
- **Client List Page** (`/clients`):
  - Material-UI table with pagination
  - Search by name, email, or phone
  - Filter by active/inactive status
  - Sortable columns
  - Click row to view details
- **Client Detail Page** (`/clients/:id`):
  - Complete client information display
  - Account balance highlighted
  - Communication preferences
  - Notes and alerts
  - Edit button
- **Client Create/Edit Form** (`/clients/new`, `/clients/:id/edit`):
  - Comprehensive form with 15+ fields
  - Zod validation schema
  - React Hook Form integration
  - Real-time validation feedback
  - Unsaved changes warning
- **Comprehensive logging** of all user actions and API calls

## Testing

### Backend Tests (pytest)

```bash
# From project root
pytest backend/tests

# With coverage
pytest backend/tests --cov=backend/app

# Run specific test file
pytest backend/tests/test_routes.py

# Run Client API tests (Phase 1.2)
pytest backend/tests/test_client_api.py -v
```

**Client API Test Coverage:**
- 25 comprehensive tests covering all CRUD operations
- Tests for authentication and authorization
- Tests for validation and error handling
- Tests for pagination and search
- Tests for soft delete vs hard delete
- Integration tests for full lifecycle

```bash
# All tests passing
============================= 25 passed in 13.44s =============================
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
│   │   ├── models.py            # Database models (User, Client, Pet/Cat, Appointment)
│   │   └── routes.py            # API routes
│   ├── migrations/              # Alembic migrations
│   ├── tests/                   # Backend tests
│   ├── logs/                    # Log files (auto-created)
│   ├── config.py                # Configuration classes
│   ├── requirements.txt         # Python dependencies
│   ├── run.py                   # Entry point
│   ├── .env                     # Environment variables (create from .env.example)
│   └── .env.example             # Example environment variables
│
├── frontend/
│   ├── public/                  # Static assets
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/          # Header, Sidebar, MainLayout
│   │   │   ├── forms/           # Form, FormTextField
│   │   │   ├── ErrorBoundary.js # Global error handler
│   │   │   ├── Dashboard.js     # Dashboard with calendar
│   │   │   ├── Calendar.js      # Calendar component
│   │   │   ├── Login.js         # Login page
│   │   │   └── NavigationBar.js # Navigation bar
│   │   ├── providers/
│   │   │   └── QueryProvider.js # React Query setup
│   │   ├── utils/
│   │   │   └── logger.js        # Logging utility
│   │   ├── App.js               # Main app component
│   │   ├── App.css              # App styles
│   │   ├── index.js             # Entry point
│   │   └── setupProxy.js        # API proxy config
│   ├── package.json             # Node dependencies
│   ├── .env.development         # Development environment variables
│   └── .env.example             # Example environment variables
│
├── FEATURES.md                  # Complete feature specification
├── ROADMAP.md                   # Development roadmap (5 phases)
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

**Current Phase:** Phase 1.2 - COMPLETE ✅

**Phase 1.1 - Infrastructure (COMPLETE):**
- ✅ Backend infrastructure (Flask-Migrate, Flask-RESTX, configs)
- ✅ Frontend infrastructure (logging, error handling, Material-UI, React Query)
- ✅ Layout components (Header, Sidebar, MainLayout)
- ✅ Form system (React Hook Form + Zod)
- ✅ Authentication and protected routes
- ✅ Calendar/appointment view
- ✅ Feline-only clinic data model (all pets are cats)

**Phase 1.2 - Client Management (COMPLETE):**
- ✅ Enhanced Client model with 20+ fields
- ✅ Client API endpoints (GET, POST, PUT, DELETE)
- ✅ Marshmallow schemas for validation
- ✅ 25 comprehensive unit tests for API (100% passing)
- ✅ Client List page with search, filter, and pagination
- ✅ Client Detail page with full information display
- ✅ Client Create/Edit form with Zod validation
- ✅ Comprehensive logging throughout
- ✅ Soft delete and hard delete support

**Next Phase:** Phase 1.2 (continued) - Patient Management Module
- Enhanced Patient (Cat) model
- Patient CRUD API endpoints
- Patient List and Detail pages
- Link patients to clients
- Cat breed management

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
