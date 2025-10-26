import os
from flask import jsonify, send_from_directory, request, Blueprint
from flask import current_app as app
from .models import db, User, Pet, Appointment, Client
from .schemas import client_schema, clients_schema, client_update_schema
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from functools import wraps
from flask import abort
from marshmallow import ValidationError as MarshmallowValidationError
from sqlalchemy.exc import IntegrityError

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

# ============================================================================
# Client Management API Endpoints
# ============================================================================

@bp.route('/api/clients', methods=['GET'])
@login_required
def get_clients():
    """
    Get list of clients with optional search and pagination
    Query params:
        - page: Page number (default 1)
        - per_page: Items per page (default 50)
        - search: Search term (searches name, email, phone)
        - active_only: Filter by active status (default true)
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '').strip()
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        app.logger.info(f"GET /api/clients - User: {current_user.username}, Page: {page}, Search: '{search}', Active only: {active_only}")

        # Build query
        query = Client.query

        # Filter by active status
        if active_only:
            query = query.filter_by(is_active=True)

        # Apply search filter if provided
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                db.or_(
                    Client.first_name.ilike(search_filter),
                    Client.last_name.ilike(search_filter),
                    Client.email.ilike(search_filter),
                    Client.phone_primary.ilike(search_filter)
                )
            )

        # Order by last name, first name
        query = query.order_by(Client.last_name, Client.first_name)

        # Paginate results
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        clients = pagination.items

        app.logger.info(f"Found {pagination.total} clients, returning page {page} of {pagination.pages}")

        # Serialize clients
        result = clients_schema.dump(clients)

        return jsonify({
            'clients': result,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        app.logger.error(f"Error getting clients: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/clients/<int:client_id>', methods=['GET'])
@login_required
def get_client(client_id):
    """Get a specific client by ID"""
    try:
        app.logger.info(f"GET /api/clients/{client_id} - User: {current_user.username}")

        client = Client.query.get_or_404(client_id)

        if not client.is_active:
            app.logger.warning(f"Accessed inactive client {client_id}")

        app.logger.info(f"Retrieved client {client_id}: {client.first_name} {client.last_name}")

        result = client_schema.dump(client)
        return jsonify(result), 200

    except Exception as e:
        app.logger.error(f"Error getting client {client_id}: {str(e)}", exc_info=True)
        if 'not found' in str(e).lower():
            return jsonify({'error': 'Client not found'}), 404
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/clients', methods=['POST'])
@login_required
def create_client():
    """Create a new client"""
    try:
        data = request.get_json()

        app.logger.info(f"POST /api/clients - User: {current_user.username}, Data: {data.get('first_name')} {data.get('last_name')}")

        # Validate request data
        try:
            validated_data = client_schema.load(data)
        except MarshmallowValidationError as err:
            app.logger.warning(f"Validation error creating client: {err.messages}")
            return jsonify({'error': 'Validation error', 'messages': err.messages}), 400

        # Check for duplicate email if provided
        if validated_data.get('email'):
            existing = Client.query.filter_by(email=validated_data['email']).first()
            if existing:
                app.logger.warning(f"Attempted to create client with duplicate email: {validated_data['email']}")
                return jsonify({'error': 'Email already exists'}), 409

        # Create new client
        new_client = Client(**validated_data)
        db.session.add(new_client)
        db.session.commit()

        app.logger.info(f"Created client {new_client.id}: {new_client.first_name} {new_client.last_name}")

        result = client_schema.dump(new_client)
        return jsonify(result), 201

    except IntegrityError as e:
        db.session.rollback()
        app.logger.error(f"Integrity error creating client: {str(e)}")
        return jsonify({'error': 'Database integrity error', 'message': str(e)}), 409

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating client: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/clients/<int:client_id>', methods=['PUT'])
@login_required
def update_client(client_id):
    """Update an existing client"""
    try:
        data = request.get_json()

        app.logger.info(f"PUT /api/clients/{client_id} - User: {current_user.username}")

        client = Client.query.get_or_404(client_id)

        # Validate request data
        try:
            validated_data = client_update_schema.load(data)
        except MarshmallowValidationError as err:
            app.logger.warning(f"Validation error updating client {client_id}: {err.messages}")
            return jsonify({'error': 'Validation error', 'messages': err.messages}), 400

        # Check for duplicate email if email is being changed
        if 'email' in validated_data and validated_data['email']:
            if validated_data['email'] != client.email:
                existing = Client.query.filter_by(email=validated_data['email']).first()
                if existing:
                    app.logger.warning(f"Attempted to update client {client_id} with duplicate email: {validated_data['email']}")
                    return jsonify({'error': 'Email already exists'}), 409

        # Update client fields
        for key, value in validated_data.items():
            setattr(client, key, value)

        db.session.commit()

        app.logger.info(f"Updated client {client_id}: {client.first_name} {client.last_name}")

        result = client_schema.dump(client)
        return jsonify(result), 200

    except IntegrityError as e:
        db.session.rollback()
        app.logger.error(f"Integrity error updating client {client_id}: {str(e)}")
        return jsonify({'error': 'Database integrity error', 'message': str(e)}), 409

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating client {client_id}: {str(e)}", exc_info=True)
        if 'not found' in str(e).lower():
            return jsonify({'error': 'Client not found'}), 404
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/clients/<int:client_id>', methods=['DELETE'])
@login_required
def delete_client(client_id):
    """
    Soft delete a client (sets is_active to False)
    Use ?hard=true query param for hard delete (requires admin)
    """
    try:
        hard_delete = request.args.get('hard', 'false').lower() == 'true'

        app.logger.info(f"DELETE /api/clients/{client_id} - User: {current_user.username}, Hard: {hard_delete}")

        client = Client.query.get_or_404(client_id)

        if hard_delete:
            # Hard delete requires admin role
            if current_user.role != 'administrator':
                app.logger.warning(f"Non-admin user {current_user.username} attempted hard delete of client {client_id}")
                return jsonify({'error': 'Admin access required for hard delete'}), 403

            db.session.delete(client)
            db.session.commit()
            app.logger.info(f"Hard deleted client {client_id}: {client.first_name} {client.last_name}")
            return jsonify({'message': 'Client permanently deleted'}), 200
        else:
            # Soft delete
            client.is_active = False
            db.session.commit()
            app.logger.info(f"Soft deleted (deactivated) client {client_id}: {client.first_name} {client.last_name}")
            return jsonify({'message': 'Client deactivated'}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting client {client_id}: {str(e)}", exc_info=True)
        if 'not found' in str(e).lower():
            return jsonify({'error': 'Client not found'}), 404
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================

@bp.route('/', defaults={'path': ''})
@bp.route('/<path:path>')
def serve(path):
    static_folder = app.config.get('STATIC_FOLDER')
    if path != "" and os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)
    else:
        return send_from_directory(static_folder, 'index.html')
