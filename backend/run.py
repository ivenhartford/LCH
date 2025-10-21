from app import create_app
from dotenv import load_dotenv
import os

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = create_app()

if __name__ == '__main__':
    app.run(host=app.config['FLASK_RUN_HOST'], port=app.config['FLASK_RUN_PORT'])
