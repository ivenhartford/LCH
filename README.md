# Veterinary Practice Management Suite

This is a Flask/Javascript/HTML application designed to be used as a practice management software suite for a veterinary clinic.

## Technology Stack

-   **Backend:** Flask (Python 3.11)
-   **Database:** PostgreSQL
-   **Frontend:** HTML, CSS, JavaScript

## Prerequisites

Before you begin, ensure you have the following installed on your local machine:

-   [Python 3.11+](https://www.python.org/downloads/)
-   [PostgreSQL](https://www.postgresql.org/download/)

## Local Development Environment Setup

To set up and run the development environment on your local machine, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Create and activate a Python virtual environment:**
    This isolates the project's dependencies from your system's Python installation.
    ```bash
    # For Unix/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up the PostgreSQL Database:**
    -   Make sure your PostgreSQL server is running.
    -   Create a new database and a user with access to it. You can do this using `psql` or a graphical tool like pgAdmin.
        ```sql
        CREATE DATABASE vet_clinic_db;
        CREATE USER vet_clinic_user WITH PASSWORD 'your_password';
        GRANT ALL PRIVILEGES ON DATABASE vet_clinic_db TO vet_clinic_user;
        ```

5.  **Configure the Environment Variable:**
    The application connects to the database using an environment variable called `DATABASE_URL`. You must set this variable in your terminal session before running the app.
    ```bash
    # For Unix/macOS (replace with your actual username, password, and database name)
    export DATABASE_URL="postgresql://vet_clinic_user:your_password@localhost:5432/vet_clinic_db"

    # For Windows (Command Prompt)
    set DATABASE_URL="postgresql://vet_clinic_user:your_password@localhost:5432/vet_clinic_db"
    ```
    **Note:** For a more permanent solution, consider using a `.env` file with a library like `python-dotenv`, but for now, setting it in the terminal is sufficient.

6.  **Run the application:**
    ```bash
    python run.py
    ```
    The application will start, and the necessary database tables will be created automatically.

7.  **Access the application:**
    Once the application is running, you can access it in your web browser at:
    [http://localhost:5000](http://localhost:5000)

## Directory Structure

-   `app/`: The main application folder.
    -   `__init__.py`: Initializes the Flask application and the database.
    -   `routes.py`: Defines the routes for the application.
    -   `models.py`: Defines the database models using Flask-SQLAlchemy.
    -   `static/`: Contains static files such as CSS and Javascript.
    -   `templates/`: Contains HTML templates.
-   `requirements.txt`: Lists the Python dependencies for the project.
-   `run.py`: The entry point to run the Flask application.
=======
## Directory Structure

- `app/`: The main application folder.
  - `__init__.py`: Initializes the Flask application.
  - `routes.py`: Defines the routes for the application.
  - `models.py`: Defines the database models.
  - `static/`: Contains static files such as CSS and Javascript.
    - `css/`: Contains CSS files.
    - `js/`: Contains Javascript files.
  - `templates/`: Contains HTML templates.
    - `index.html`: The main index page.
- `requirements.txt`: Lists the Python dependencies for the project.
