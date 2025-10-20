from flask import render_template
from flask import current_app as app
from .models import Pet
from . import db

@app.route('/')
def home():
    pets = Pet.query.all()
    return render_template('index.html', pets=pets)
=======

@app.route('/')
def home():
    return render_template('index.html')
