import os
from flask import jsonify, send_from_directory, request, Blueprint
from flask import current_app as app
from .models import db, User, Pet, Appointment
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from functools import wraps
from datetime import datetime
from flask import abort

bp = Blueprint('main', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'administrator':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 400

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

@bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        login_user(user)
        app.logger.info(f"User {username} logged in successfully.")
        return jsonify({'message': 'Logged in successfully'}), 200

    app.logger.warning(f"Failed login attempt for username: {username}.")
    return jsonify({'message': 'Invalid credentials'}), 401

@bp.route('/api/check_session')
def check_session():
    if current_user.is_authenticated:
        return jsonify({'id': current_user.id, 'username': current_user.username, 'role': current_user.role})
    return jsonify({}), 401

@bp.route('/api/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@bp.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([{'id': user.id, 'username': user.username, 'role': user.role} for user in users])

@bp.route('/api/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'id': user.id, 'username': user.username, 'role': user.role})

@bp.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    user.username = data.get('username', user.username)
    user.role = data.get('role', user.role)
    if 'password' in data:
        user.set_password(data['password'])
    db.session.commit()
    return jsonify({'message': 'User updated successfully'})

@bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})

@bp.route('/api/pets')
def get_pets():
    pets = Pet.query.all()
    return jsonify([{'name': pet.name, 'breed': pet.breed, 'owner': pet.owner} for pet in pets])

@bp.route('/api/appointments', methods=['GET'])
@login_required
def get_appointments():
    appointments = Appointment.query.all()
    return jsonify([{
        'id': apt.id,
        'title': apt.title,
        'start': apt.start_time.isoformat(),
        'end': apt.end_time.isoformat(),
        'description': apt.description
    } for apt in appointments])

@bp.route('/api/appointments', methods=['POST'])
@login_required
def create_appointment():
    data = request.get_json()
    start_time = datetime.fromisoformat(data['start'])
    end_time = datetime.fromisoformat(data['end'])

    new_appointment = Appointment(
        title=data['title'],
        start_time=start_time,
        end_time=end_time,
        description=data.get('description')
    )
    db.session.add(new_appointment)
    db.session.commit()

    return jsonify({'message': 'Appointment created successfully'}), 201

@bp.route('/', defaults={'path': ''})
@bp.route('/<path:path>')
def serve(path):
    static_folder = app.config.get('STATIC_FOLDER')
    if path != "" and os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)
    else:
        return send_from_directory(static_folder, 'index.html')
