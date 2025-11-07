import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restx import Api
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
api = Api(
    version="1.0",
    title="Lenox Cat Hospital API",
    description="Veterinary Practice Management System API",
    doc="/api/docs",
)

# Rate limiting configuration
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
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

    # SECURITY: Enforce SECRET_KEY in production
    if config_name == "production" and not app.config.get("SECRET_KEY"):
        raise ValueError(
            "SECRET_KEY environment variable MUST be set in production. "
            "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )

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

    @login_manager.unauthorized_handler
    def unauthorized():
        """Return 401 JSON response for unauthorized API requests"""
        return jsonify({"error": "Authentication required"}), 401

    # Initialize rate limiter
    limiter.init_app(app)

    # CORS Configuration
    cors_origins = app.config.get("CORS_ORIGINS", ["http://localhost:3000"])
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    )

    # Security Headers with Flask-Talisman (only in production)
    if not app.debug and not app.testing:
        csp = {
            "default-src": "'self'",
            "script-src": ["'self'", "'unsafe-inline'"],
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:", "https:"],
            "font-src": ["'self'", "data:"],
            "connect-src": ["'self'"],
        }
        Talisman(
            app,
            force_https=True,
            strict_transport_security=True,
            content_security_policy=csp,
            content_security_policy_nonce_in=["script-src"],
        )

    # CSRF Protection - Initialize but exempt API endpoints that use JWT
    csrf.init_app(app)

    # Exempt JWT-authenticated portal endpoints from CSRF
    # (they use Bearer token authentication instead)
    csrf.exempt("routes.portal_login")
    csrf.exempt("routes.portal_register")
    csrf.exempt("routes.portal_dashboard")
    csrf.exempt("routes.portal_patients")
    csrf.exempt("routes.portal_patient_detail")
    csrf.exempt("routes.portal_appointments")
    csrf.exempt("routes.portal_invoices")
    csrf.exempt("routes.portal_invoice_detail")
    csrf.exempt("routes.create_appointment_request")
    csrf.exempt("routes.get_client_appointment_requests")
    csrf.exempt("routes.get_appointment_request_detail")
    csrf.exempt("routes.cancel_appointment_request")

    # Initialize error handlers and security monitoring
    from .error_handlers import (
        handle_validation_error,
        handle_not_found_error,
        handle_auth_error,
        handle_permission_error,
        handle_database_error,
    )
    from .security_monitor import get_security_monitor
    from marshmallow import ValidationError
    from werkzeug.exceptions import NotFound, Unauthorized, Forbidden
    from sqlalchemy.exc import SQLAlchemyError

    # Register error handlers
    app.register_error_handler(ValidationError, handle_validation_error)
    app.register_error_handler(NotFound, handle_not_found_error)
    app.register_error_handler(Unauthorized, handle_auth_error)
    app.register_error_handler(Forbidden, handle_permission_error)
    app.register_error_handler(SQLAlchemyError, handle_database_error)

    # Initialize security monitor (accessible via get_security_monitor())
    app.security_monitor = get_security_monitor()

    # Initialize API with app first
    api.init_app(app)

    # Then register routes blueprint
    from . import routes

    app.register_blueprint(routes.bp)

    return app
