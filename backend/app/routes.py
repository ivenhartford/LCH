import os
from flask import jsonify, send_from_directory
from flask import current_app as app
from .models import Pet
from . import db

@app.route('/api/pets')
def get_pets():
    pets = Pet.query.all()
    return jsonify([{'name': pet.name, 'breed': pet.breed, 'owner': pet.owner} for pet in pets])

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')
