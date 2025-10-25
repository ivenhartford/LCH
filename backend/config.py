import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_default_secret_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///vet_clinic.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_RUN_HOST = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    FLASK_RUN_PORT = int(os.environ.get('FLASK_RUN_PORT', 5000))

    # API Settings
    RESTX_MASK_SWAGGER = False
    ERROR_404_HELP = False

    # Pagination
    ITEMS_PER_PAGE = 50
    MAX_ITEMS_PER_PAGE = 100

    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')

    # Session
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True  # Log SQL queries


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Production should use PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://localhost/vet_clinic')

    # Enhanced security for production
    SESSION_COOKIE_SECURE = True  # Require HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'

    # Production logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', False)


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
