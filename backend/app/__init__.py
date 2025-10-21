import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

from config import Config

def create_app(config_class=Config, config_overrides=None):
    app = Flask(__name__, static_folder=None, static_url_path='/')
    app.config.from_object(config_class)
    app.config['STATIC_FOLDER'] = '../../frontend/build'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = False

    if config_overrides:
        app.config.update(config_overrides)

    if not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/vet_clinic.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Vet Clinic startup')

    db.init_app(app)

    from . import models
    with app.app_context():
        db.create_all()

    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    from . import routes
    app.register_blueprint(routes.bp)

    return app
