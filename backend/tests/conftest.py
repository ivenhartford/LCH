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
        db.drop_all()

    shutil.rmtree(static_folder)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
