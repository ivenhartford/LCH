import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_default_secret_key')
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost/vet_clinic')
    FLASK_RUN_HOST = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    FLASK_RUN_PORT = int(os.environ.get('FLASK_RUN_PORT', 5000))
