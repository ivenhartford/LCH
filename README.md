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

5.  **Configure the `DATABASE_URL` Environment Variable:**
    The Flask app connects to the database using this environment variable.
    ```bash
    # For Unix/macOS (replace with your actual credentials)
    export DATABASE_URL="postgresql://vet_clinic_user:your_password@localhost:5432/vet_clinic_db"

    # For Windows (Command Prompt)
    set DATABASE_URL="postgresql://vet_clinic_user:your_password@localhost:5432/vet_clinic_db"
    ```

6.  **Run the backend server:**
    ```bash
    python run.py
    ```
    The Flask API server will start on `http://localhost:5000`.

### Frontend Setup (React App)

1.  **Open a new terminal window** and navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```

2.  **Install the Node.js dependencies:**
    ```bash
    npm install
    ```

3.  **Run the frontend development server:**
    ```bash
    npm start
    ```
    The React application will open in your web browser at `http://localhost:3000`. The app is configured to proxy API requests to the Flask backend, so you can interact with the full application from this address.

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

## Directory Structure

-   `backend/`: The Flask API application.
    -   `app/`: The main application folder.
        -   `__init__.py`: Initializes the Flask application and the database.
        -   `routes.py`: Defines the API routes.
        -   `models.py`: Defines the database models.
    -   `requirements.txt`: Python dependencies.
    -   `run.py`: Entry point to run the Flask server.
-   `frontend/`: The React front-end application.
    -   `public/`: Public assets and `index.html` template.
    -   `src/`: React source code.
    -   `package.json`: Node.js dependencies and scripts.
