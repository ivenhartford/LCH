import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db

import tempfile
import shutil


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    static_folder = tempfile.mkdtemp()

    app = create_app(
        config_overrides={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "STATIC_FOLDER": static_folder,
        }
    )

    with open(os.path.join(static_folder, "index.html"), "w") as f:
        f.write("test")

    with app.app_context():
        db.create_all()

    yield app

    # Clean up database after test
    with app.app_context():
        db.session.remove()
        db.drop_all()

    shutil.rmtree(static_folder)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(autouse=True)
def reset_db(app):
    """
    Automatically reset database session after each test.
    This prevents "Working outside of application context" errors
    during fixture teardown.
    """
    yield
    # Clean up any remaining database sessions
    with app.app_context():
        db.session.remove()
