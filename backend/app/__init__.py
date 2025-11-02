import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restx import Api
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
api = Api(
    version="1.0",
    title="Lenox Cat Hospital API",
    description="Veterinary Practice Management System API",
    doc="/api/docs",
)

from config import config_by_name


def create_app(config_name=None, config_overrides=None):
    # Get config name from environment or use default
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    config_class = config_by_name.get(config_name, config_by_name["default"])

    app = Flask(__name__, static_folder=None, static_url_path="/")
    app.config.from_object(config_class)
    app.config["STATIC_FOLDER"] = "../../frontend/build"

    if config_overrides:
        app.config.update(config_overrides)

    if not app.testing:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler("logs/vet_clinic.log", maxBytes=10240, backupCount=10)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("Vet Clinic startup")

    db.init_app(app)
    migrate.init_app(app, db)

    from . import models

    # Database tables are managed via Flask-Migrate
    # Use: flask db migrate -m "message" && flask db upgrade

    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    # Initialize API with app first
    api.init_app(app)

    # Then register routes blueprint
    from . import routes

    app.register_blueprint(routes.bp)

    return app
