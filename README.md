# Veterinary Practice Management Suite

This is a practice management software suite for a veterinary clinic, built with a modern React front-end and a Flask back-end API.

## Technology Stack

-   **Backend:** Flask (Python 3.11)
-   **Frontend:** React (JavaScript)
-   **Database:** PostgreSQL

## Prerequisites

Before you begin, ensure you have the following installed on your local machine:

-   [Python 3.11+](https://www.python.org/downloads/)
-   [Node.js](https://nodejs.org/) (which includes npm)
-   [PostgreSQL](https://www.postgresql.org/download/)

## Local Development Environment Setup

This project is divided into two main parts: a `backend` Flask application and a `frontend` React application. You will need to run both concurrently for local development.

### Backend Setup (Flask API)

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    # For Unix/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install the Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up the PostgreSQL Database:**
    -   Make sure your PostgreSQL server is running.
    -   Create a new database and a user with access to it.
        ```sql
        CREATE DATABASE vet_clinic_db;
        CREATE USER vet_clinic_user WITH PASSWORD 'your_password';
        GRANT ALL PRIVILEGES ON DATABASE vet_clinic_db TO vet_clinic_user;
        ```

5.  **Configure Environment Variables:**
    The backend uses a `.env` file for configuration. Copy the example file and edit it with your local settings.
    ```bash
    cp .env.example .env
    ```
    Now, open `.env` and set your `DATABASE_URL`, `SECRET_KEY`, and other values as needed.

6.  **Run the backend server:**
    ```bash
    python run.py
    ```
    The Flask API server will start on the host and port specified in your `.env` file (default is `http://0.0.0.0:5000`).

### Frontend Setup (React App)

1.  **Open a new terminal window** and navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```

2.  **Install the Node.js dependencies:**
    ```bash
    npm install
    ```

3.  **Configure Environment Variables:**
    The frontend uses a `.env.development` file for local configuration. Copy the example file:
    ```bash
    cp .env.example .env.development
    ```
    You can edit `.env.development` to change the `PORT` for the React development server or the `REACT_APP_API_PROXY` location.

4.  **Run the frontend development server:**
    ```bash
    npm start
    ```
    The React application will open in your web browser at the port specified in your `.env.development` file (default is `http://localhost:3000`).

## Creating an Administrator User

To create an administrator user, you can use the Flask shell.

1.  **Open a new terminal** and navigate to the `backend` directory.

2.  **Activate your virtual environment.**

3.  **Start the Flask shell:**
    ```bash
    flask shell
    ```

4.  **In the shell, run the following commands:**
    ```python
    from app import db
    from app.models import User

    # Create a new user
    admin = User(username='admin', role='administrator')
    admin.set_password('your_password')  # Choose a strong password
    db.session.add(admin)
    db.session.commit()
    ```

## Running in Production

To run the application in a production-like environment:

1.  **Build the React application:**
    From the `frontend` directory, run:
    ```bash
    npm run build
    ```
    This will create an optimized, static build of the React app in the `frontend/build` directory.

2.  **Run the Flask server:**
    The Flask application is pre-configured to serve the static files from the `frontend/build` directory. Simply run the backend server from the `backend` directory:
    ```bash
    python run.py
    ```
    You can now access the production-ready application at `http://localhost:5000`.

## Logging

The backend application is configured to log to a rotating file located at `logs/vet_clinic.log`. The log directory will be created automatically if it doesn't exist. Logs are rotated when they reach 10KB, and up to 10 backup files are kept.

## Testing

### Backend (pytest)

To run the backend tests, navigate to the project root and run:

```bash
pytest backend/tests
```

### Frontend (Jest)

To run the frontend tests, navigate to the `frontend` directory and run:

```bash
npm test
```

## Directory Structure

-   `backend/`: The Flask API application.
    -   `app/`: The main application folder.
        -   `__init__.py`: Initializes the Flask application and the database.
        -   `routes.py`: Defines the API routes.
        -   `models.py`: Defines the database models.
    -   `config.py`: Loads configuration from environment variables.
    -   `.env.example`: Example environment variables for the backend.
    -   `requirements.txt`: Python dependencies.
    -   `run.py`: Entry point to run the Flask server.
-   `frontend/`: The React front-end application.
    -   `public/`: Public assets and `index.html` template.
    -   `src/`: React source code.
        -   `setupProxy.js`: Configures the API proxy for the development server.
    -   `.env.example`: Example environment variables for the frontend.
    -   `package.json`: Node.js dependencies and scripts.
