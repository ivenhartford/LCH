import os
from flask import jsonify, send_from_directory, request, Blueprint
from flask import current_app as app
from .models import db, User, Patient, Pet, Appointment, AppointmentType, Client
from .schemas import (
    client_schema, clients_schema, client_update_schema,
    patient_schema, patients_schema, patient_update_schema,
    appointment_type_schema, appointment_types_schema, appointment_type_update_schema,
    appointment_schema, appointments_schema, appointment_update_schema
)
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

# ============================================================================
# AppointmentType Management API Endpoints
# ============================================================================

@bp.route('/api/appointment-types', methods=['GET'])
@login_required
def get_appointment_types():
    """
    Get list of appointment types
    Query params:
        - active_only: Filter by active status (default true)
    """
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        app.logger.info(f"GET /api/appointment-types - User: {current_user.username}, Active only: {active_only}")

        query = AppointmentType.query
        if active_only:
            query = query.filter_by(is_active=True)

        query = query.order_by(AppointmentType.name)
        appointment_types = query.all()

        app.logger.info(f"Found {len(appointment_types)} appointment types")

        result = appointment_types_schema.dump(appointment_types)
        return jsonify(result), 200

    except Exception as e:
        app.logger.error(f"Error getting appointment types: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/appointment-types/<int:type_id>', methods=['GET'])
@login_required
def get_appointment_type(type_id):
    """Get a specific appointment type by ID"""
    try:
        app.logger.info(f"GET /api/appointment-types/{type_id} - User: {current_user.username}")

        appointment_type = AppointmentType.query.get_or_404(type_id)

        result = appointment_type_schema.dump(appointment_type)
        return jsonify(result), 200

    except Exception as e:
        app.logger.error(f"Error getting appointment type {type_id}: {str(e)}", exc_info=True)
        if 'not found' in str(e).lower():
            return jsonify({'error': 'Appointment type not found'}), 404
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/appointment-types', methods=['POST'])
@login_required
def create_appointment_type():
    """Create a new appointment type"""
    try:
        data = request.get_json()

        app.logger.info(f"POST /api/appointment-types - User: {current_user.username}, Data: {data.get('name')}")

        # Validate request data
        try:
            validated_data = appointment_type_schema.load(data)
        except MarshmallowValidationError as err:
            app.logger.warning(f"Validation error creating appointment type: {err.messages}")
            return jsonify({'error': 'Validation error', 'messages': err.messages}), 400

        # Check for duplicate name
        existing = AppointmentType.query.filter_by(name=validated_data['name']).first()
        if existing:
            app.logger.warning(f"Attempted to create appointment type with duplicate name: {validated_data['name']}")
            return jsonify({'error': 'Appointment type name already exists'}), 409

        # Create new appointment type
        new_type = AppointmentType(**validated_data)
        db.session.add(new_type)
        db.session.commit()

        app.logger.info(f"Created appointment type {new_type.id}: {new_type.name}")

        result = appointment_type_schema.dump(new_type)
        return jsonify(result), 201

    except IntegrityError as e:
        db.session.rollback()
        app.logger.error(f"Integrity error creating appointment type: {str(e)}")
        return jsonify({'error': 'Database integrity error', 'message': str(e)}), 409

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating appointment type: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/appointment-types/<int:type_id>', methods=['PUT'])
@login_required
def update_appointment_type(type_id):
    """Update an existing appointment type"""
    try:
        data = request.get_json()

        app.logger.info(f"PUT /api/appointment-types/{type_id} - User: {current_user.username}")

        appointment_type = AppointmentType.query.get_or_404(type_id)

        # Validate request data
        try:
            validated_data = appointment_type_update_schema.load(data)
        except MarshmallowValidationError as err:
            app.logger.warning(f"Validation error updating appointment type {type_id}: {err.messages}")
            return jsonify({'error': 'Validation error', 'messages': err.messages}), 400

        # Check for duplicate name if name is being changed
        if 'name' in validated_data and validated_data['name'] != appointment_type.name:
            existing = AppointmentType.query.filter_by(name=validated_data['name']).first()
            if existing:
                app.logger.warning(f"Attempted to update appointment type {type_id} with duplicate name: {validated_data['name']}")
                return jsonify({'error': 'Appointment type name already exists'}), 409

        # Update fields
        for key, value in validated_data.items():
            setattr(appointment_type, key, value)

        db.session.commit()

        app.logger.info(f"Updated appointment type {type_id}: {appointment_type.name}")

        result = appointment_type_schema.dump(appointment_type)
        return jsonify(result), 200

    except IntegrityError as e:
        db.session.rollback()
        app.logger.error(f"Integrity error updating appointment type {type_id}: {str(e)}")
        return jsonify({'error': 'Database integrity error', 'message': str(e)}), 409

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating appointment type {type_id}: {str(e)}", exc_info=True)
        if 'not found' in str(e).lower():
            return jsonify({'error': 'Appointment type not found'}), 404
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/appointment-types/<int:type_id>', methods=['DELETE'])
@login_required
def delete_appointment_type(type_id):
    """
    Soft delete an appointment type (sets is_active to False)
    Use ?hard=true query param for hard delete (requires admin)
    """
    try:
        hard_delete = request.args.get('hard', 'false').lower() == 'true'

        app.logger.info(f"DELETE /api/appointment-types/{type_id} - User: {current_user.username}, Hard: {hard_delete}")

        appointment_type = AppointmentType.query.get_or_404(type_id)

        if hard_delete:
            # Hard delete requires admin role
            if current_user.role != 'administrator':
                app.logger.warning(f"Non-admin user {current_user.username} attempted hard delete of appointment type {type_id}")
                return jsonify({'error': 'Admin access required for hard delete'}), 403

            db.session.delete(appointment_type)
            db.session.commit()
            app.logger.info(f"Hard deleted appointment type {type_id}: {appointment_type.name}")
            return jsonify({'message': 'Appointment type permanently deleted'}), 200
        else:
            # Soft delete
            appointment_type.is_active = False
            db.session.commit()
            app.logger.info(f"Soft deleted (deactivated) appointment type {type_id}: {appointment_type.name}")
            return jsonify({'message': 'Appointment type deactivated'}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting appointment type {type_id}: {str(e)}", exc_info=True)
        if 'not found' in str(e).lower():
            return jsonify({'error': 'Appointment type not found'}), 404
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Enhanced Appointment Management API Endpoints
# ============================================================================

@bp.route('/api/appointments', methods=['GET'])
@login_required
def get_appointments():
    """
    Get list of appointments with optional filters and pagination
    Query params:
        - page: Page number (default 1)
        - per_page: Items per page (default 100)
        - status: Filter by status (scheduled, confirmed, checked_in, in_progress, completed, cancelled, no_show)
        - client_id: Filter by specific client
        - patient_id: Filter by specific patient
        - assigned_staff_id: Filter by assigned staff member
        - start_date: Filter appointments >= this date (ISO format)
        - end_date: Filter appointments <= this date (ISO format)
        - appointment_type_id: Filter by appointment type
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        status_filter = request.args.get('status', '').strip()
        client_id = request.args.get('client_id', type=int)
        patient_id = request.args.get('patient_id', type=int)
        assigned_staff_id = request.args.get('assigned_staff_id', type=int)
        appointment_type_id = request.args.get('appointment_type_id', type=int)
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()

        app.logger.info(f"GET /api/appointments - User: {current_user.username}, Filters: status={status_filter}, client={client_id}, patient={patient_id}")

        # Build query
        query = Appointment.query

        # Apply filters
        if status_filter:
            query = query.filter_by(status=status_filter)

        if client_id:
            query = query.filter_by(client_id=client_id)

        if patient_id:
            query = query.filter_by(patient_id=patient_id)

        if assigned_staff_id:
            query = query.filter_by(assigned_staff_id=assigned_staff_id)

        if appointment_type_id:
            query = query.filter_by(appointment_type_id=appointment_type_id)

        # Date range filters
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.filter(Appointment.start_time >= start_dt)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)'}), 400

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                query = query.filter(Appointment.end_time <= end_dt)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)'}), 400

        # Order by start time
        query = query.order_by(Appointment.start_time)

        # Paginate results
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        appointments = pagination.items

        app.logger.info(f"Found {pagination.total} appointments, returning page {page} of {pagination.pages}")

        # Serialize appointments
        result = appointments_schema.dump(appointments)

        return jsonify({
            'appointments': result,
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
        app.logger.error(f"Error getting appointments: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/appointments/<int:appointment_id>', methods=['GET'])
@login_required
def get_appointment(appointment_id):
    """Get a specific appointment by ID"""
    try:
        app.logger.info(f"GET /api/appointments/{appointment_id} - User: {current_user.username}")

        appointment = Appointment.query.get_or_404(appointment_id)

        app.logger.info(f"Retrieved appointment {appointment_id}: {appointment.title}")

        result = appointment_schema.dump(appointment)
        return jsonify(result), 200

    except Exception as e:
        app.logger.error(f"Error getting appointment {appointment_id}: {str(e)}", exc_info=True)
        if 'not found' in str(e).lower():
            return jsonify({'error': 'Appointment not found'}), 404
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/appointments', methods=['POST'])
@login_required
def create_appointment():
    """Create a new appointment"""
    try:
        data = request.get_json()

        app.logger.info(f"POST /api/appointments - User: {current_user.username}, Data: {data.get('title')}")

        # Validate request data
        try:
            validated_data = appointment_schema.load(data)
        except MarshmallowValidationError as err:
            app.logger.warning(f"Validation error creating appointment: {err.messages}")
            return jsonify({'error': 'Validation error', 'messages': err.messages}), 400

        # Verify client exists
        client = Client.query.get(validated_data['client_id'])
        if not client:
            app.logger.warning(f"Attempted to create appointment with non-existent client_id: {validated_data['client_id']}")
            return jsonify({'error': 'Client not found'}), 404

        # Verify patient exists if provided
        if validated_data.get('patient_id'):
            patient = Patient.query.get(validated_data['patient_id'])
            if not patient:
                app.logger.warning(f"Attempted to create appointment with non-existent patient_id: {validated_data['patient_id']}")
                return jsonify({'error': 'Patient not found'}), 404

        # Verify appointment type exists if provided
        if validated_data.get('appointment_type_id'):
            apt_type = AppointmentType.query.get(validated_data['appointment_type_id'])
            if not apt_type:
                app.logger.warning(f"Attempted to create appointment with non-existent appointment_type_id: {validated_data['appointment_type_id']}")
                return jsonify({'error': 'Appointment type not found'}), 404

        # Verify staff exists if provided
        if validated_data.get('assigned_staff_id'):
            staff = User.query.get(validated_data['assigned_staff_id'])
            if not staff:
                app.logger.warning(f"Attempted to create appointment with non-existent assigned_staff_id: {validated_data['assigned_staff_id']}")
                return jsonify({'error': 'Assigned staff not found'}), 404

        # Set created_by to current user
        validated_data['created_by_id'] = current_user.id

        # Create new appointment
        new_appointment = Appointment(**validated_data)
        db.session.add(new_appointment)
        db.session.commit()

        app.logger.info(f"Created appointment {new_appointment.id}: {new_appointment.title}")

        result = appointment_schema.dump(new_appointment)
        return jsonify(result), 201

    except IntegrityError as e:
        db.session.rollback()
        app.logger.error(f"Integrity error creating appointment: {str(e)}")
        return jsonify({'error': 'Database integrity error', 'message': str(e)}), 409

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating appointment: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/appointments/<int:appointment_id>', methods=['PUT'])
@login_required
def update_appointment(appointment_id):
    """Update an existing appointment"""
    try:
        data = request.get_json()

        app.logger.info(f"PUT /api/appointments/{appointment_id} - User: {current_user.username}")

        appointment = Appointment.query.get_or_404(appointment_id)

        # Validate request data
        try:
            validated_data = appointment_update_schema.load(data)
        except MarshmallowValidationError as err:
            app.logger.warning(f"Validation error updating appointment {appointment_id}: {err.messages}")
            return jsonify({'error': 'Validation error', 'messages': err.messages}), 400

        # Verify entities exist if being changed
        if 'client_id' in validated_data:
            client = Client.query.get(validated_data['client_id'])
            if not client:
                return jsonify({'error': 'Client not found'}), 404

        if 'patient_id' in validated_data and validated_data['patient_id']:
            patient = Patient.query.get(validated_data['patient_id'])
            if not patient:
                return jsonify({'error': 'Patient not found'}), 404

        if 'appointment_type_id' in validated_data and validated_data['appointment_type_id']:
            apt_type = AppointmentType.query.get(validated_data['appointment_type_id'])
            if not apt_type:
                return jsonify({'error': 'Appointment type not found'}), 404

        if 'assigned_staff_id' in validated_data and validated_data['assigned_staff_id']:
            staff = User.query.get(validated_data['assigned_staff_id'])
            if not staff:
                return jsonify({'error': 'Assigned staff not found'}), 404

        # Handle status changes with special logic
        if 'status' in validated_data:
            new_status = validated_data['status']

            # Auto-set check_in_time when status changes to checked_in
            if new_status == 'checked_in' and not appointment.check_in_time:
                appointment.check_in_time = datetime.utcnow()

            # Auto-set actual_start_time when status changes to in_progress
            if new_status == 'in_progress' and not appointment.actual_start_time:
                appointment.actual_start_time = datetime.utcnow()

            # Auto-set actual_end_time when status changes to completed
            if new_status == 'completed' and not appointment.actual_end_time:
                appointment.actual_end_time = datetime.utcnow()

            # Auto-set cancelled_at and cancelled_by when status changes to cancelled
            if new_status == 'cancelled' and not appointment.cancelled_at:
                appointment.cancelled_at = datetime.utcnow()
                appointment.cancelled_by_id = current_user.id

        # Update appointment fields
        for key, value in validated_data.items():
            setattr(appointment, key, value)

        db.session.commit()

        app.logger.info(f"Updated appointment {appointment_id}: {appointment.title}")

        result = appointment_schema.dump(appointment)
        return jsonify(result), 200

    except IntegrityError as e:
        db.session.rollback()
        app.logger.error(f"Integrity error updating appointment {appointment_id}: {str(e)}")
        return jsonify({'error': 'Database integrity error', 'message': str(e)}), 409

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating appointment {appointment_id}: {str(e)}", exc_info=True)
        if 'not found' in str(e).lower():
            return jsonify({'error': 'Appointment not found'}), 404
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
@login_required
def delete_appointment(appointment_id):
    """
    Delete an appointment (requires admin)
    For non-admin users, use PUT to change status to 'cancelled' instead
    """
    try:
        app.logger.info(f"DELETE /api/appointments/{appointment_id} - User: {current_user.username}")

        # Only admins can delete appointments
        if current_user.role != 'administrator':
            app.logger.warning(f"Non-admin user {current_user.username} attempted to delete appointment {appointment_id}")
            return jsonify({'error': 'Admin access required to delete appointments. Use PUT to cancel instead.'}), 403

        appointment = Appointment.query.get_or_404(appointment_id)

        db.session.delete(appointment)
        db.session.commit()
        app.logger.info(f"Deleted appointment {appointment_id}: {appointment.title}")
        return jsonify({'message': 'Appointment permanently deleted'}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting appointment {appointment_id}: {str(e)}", exc_info=True)
        if 'not found' in str(e).lower():
            return jsonify({'error': 'Appointment not found'}), 404
        return jsonify({'error': 'Internal server error'}), 500

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
# Patient (Cat) Management API Endpoints
# ============================================================================

@bp.route('/api/patients', methods=['GET'])
@login_required
def get_patients():
    """
    Get list of patients (cats) with optional search and pagination
    Query params:
        - page: Page number (default 1)
        - per_page: Items per page (default 50)
        - search: Search term (searches name, owner name, breed, microchip)
        - status: Filter by status (Active, Inactive, Deceased)
        - owner_id: Filter by specific owner/client
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()
        owner_id = request.args.get('owner_id', type=int)

        app.logger.info(f"GET /api/patients - User: {current_user.username}, Page: {page}, Search: '{search}', Status: '{status_filter}', Owner: {owner_id}")

        # Build query
        query = Patient.query

        # Filter by status
        if status_filter:
            query = query.filter_by(status=status_filter)
        else:
            # Default: show only active patients
            query = query.filter_by(status='Active')

        # Filter by owner
        if owner_id:
            query = query.filter_by(owner_id=owner_id)

        # Apply search filter if provided
        if search:
            search_filter = f"%{search}%"
            query = query.join(Client).filter(
                db.or_(
                    Patient.name.ilike(search_filter),
                    Patient.breed.ilike(search_filter),
                    Patient.color.ilike(search_filter),
                    Patient.microchip_number.ilike(search_filter),
                    Client.first_name.ilike(search_filter),
                    Client.last_name.ilike(search_filter)
                )
            )

        # Order by name
        query = query.order_by(Patient.name)

        # Paginate results
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        patients = pagination.items

        app.logger.info(f"Found {pagination.total} patients, returning page {page} of {pagination.pages}")

        # Serialize patients
        result = patients_schema.dump(patients)

        return jsonify({
            'patients': result,
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
        app.logger.error(f"Error getting patients: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/patients/<int:patient_id>', methods=['GET'])
@login_required
def get_patient(patient_id):
    """Get a specific patient by ID"""
    try:
        app.logger.info(f"GET /api/patients/{patient_id} - User: {current_user.username}")

        patient = Patient.query.get_or_404(patient_id)

        if patient.status == 'Deceased':
            app.logger.warning(f"Accessed deceased patient {patient_id}")

        app.logger.info(f"Retrieved patient {patient_id}: {patient.name}")

        result = patient_schema.dump(patient)
        return jsonify(result), 200

    except Exception as e:
        app.logger.error(f"Error getting patient {patient_id}: {str(e)}", exc_info=True)
        if 'not found' in str(e).lower():
            return jsonify({'error': 'Patient not found'}), 404
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/patients', methods=['POST'])
@login_required
def create_patient():
    """Create a new patient (cat)"""
    try:
        data = request.get_json()

        app.logger.info(f"POST /api/patients - User: {current_user.username}, Data: {data.get('name')}")

        # Validate request data
        try:
            validated_data = patient_schema.load(data)
        except MarshmallowValidationError as err:
            app.logger.warning(f"Validation error creating patient: {err.messages}")
            return jsonify({'error': 'Validation error', 'messages': err.messages}), 400

        # Verify owner exists
        owner = Client.query.get(validated_data['owner_id'])
        if not owner:
            app.logger.warning(f"Attempted to create patient with non-existent owner_id: {validated_data['owner_id']}")
            return jsonify({'error': 'Owner (client) not found'}), 404

        # Check for duplicate microchip if provided
        if validated_data.get('microchip_number'):
            existing = Patient.query.filter_by(microchip_number=validated_data['microchip_number']).first()
            if existing:
                app.logger.warning(f"Attempted to create patient with duplicate microchip: {validated_data['microchip_number']}")
                return jsonify({'error': 'Microchip number already exists'}), 409

        # Create new patient
        new_patient = Patient(**validated_data)
        db.session.add(new_patient)
        db.session.commit()

        app.logger.info(f"Created patient {new_patient.id}: {new_patient.name} (owner: {owner.first_name} {owner.last_name})")

        result = patient_schema.dump(new_patient)
        return jsonify(result), 201

    except IntegrityError as e:
        db.session.rollback()
        app.logger.error(f"Integrity error creating patient: {str(e)}")
        return jsonify({'error': 'Database integrity error', 'message': str(e)}), 409

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating patient: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/patients/<int:patient_id>', methods=['PUT'])
@login_required
def update_patient(patient_id):
    """Update an existing patient"""
    try:
        data = request.get_json()

        app.logger.info(f"PUT /api/patients/{patient_id} - User: {current_user.username}")

        patient = Patient.query.get_or_404(patient_id)

        # Validate request data
        try:
            validated_data = patient_update_schema.load(data)
        except MarshmallowValidationError as err:
            app.logger.warning(f"Validation error updating patient {patient_id}: {err.messages}")
            return jsonify({'error': 'Validation error', 'messages': err.messages}), 400

        # Check for duplicate microchip if microchip is being changed
        if 'microchip_number' in validated_data and validated_data['microchip_number']:
            if validated_data['microchip_number'] != patient.microchip_number:
                existing = Patient.query.filter_by(microchip_number=validated_data['microchip_number']).first()
                if existing:
                    app.logger.warning(f"Attempted to update patient {patient_id} with duplicate microchip: {validated_data['microchip_number']}")
                    return jsonify({'error': 'Microchip number already exists'}), 409

        # Verify new owner exists if owner_id is being changed
        if 'owner_id' in validated_data:
            owner = Client.query.get(validated_data['owner_id'])
            if not owner:
                app.logger.warning(f"Attempted to update patient {patient_id} with non-existent owner_id: {validated_data['owner_id']}")
                return jsonify({'error': 'Owner (client) not found'}), 404

        # Update patient fields
        for key, value in validated_data.items():
            setattr(patient, key, value)

        db.session.commit()

        app.logger.info(f"Updated patient {patient_id}: {patient.name}")

        result = patient_schema.dump(patient)
        return jsonify(result), 200

    except IntegrityError as e:
        db.session.rollback()
        app.logger.error(f"Integrity error updating patient {patient_id}: {str(e)}")
        return jsonify({'error': 'Database integrity error', 'message': str(e)}), 409

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating patient {patient_id}: {str(e)}", exc_info=True)
        if 'not found' in str(e).lower():
            return jsonify({'error': 'Patient not found'}), 404
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/api/patients/<int:patient_id>', methods=['DELETE'])
@login_required
def delete_patient(patient_id):
    """
    Delete a patient
    Note: For cats, we typically set status to 'Deceased' rather than delete.
    Use ?hard=true query param for hard delete (requires admin)
    """
    try:
        hard_delete = request.args.get('hard', 'false').lower() == 'true'

        app.logger.info(f"DELETE /api/patients/{patient_id} - User: {current_user.username}, Hard: {hard_delete}")

        patient = Patient.query.get_or_404(patient_id)

        if hard_delete:
            # Hard delete requires admin role
            if current_user.role != 'administrator':
                app.logger.warning(f"Non-admin user {current_user.username} attempted hard delete of patient {patient_id}")
                return jsonify({'error': 'Admin access required for hard delete'}), 403

            db.session.delete(patient)
            db.session.commit()
            app.logger.info(f"Hard deleted patient {patient_id}: {patient.name}")
            return jsonify({'message': 'Patient permanently deleted'}), 200
        else:
            # Soft delete - set to inactive
            patient.status = 'Inactive'
            db.session.commit()
            app.logger.info(f"Soft deleted (deactivated) patient {patient_id}: {patient.name}")
            return jsonify({'message': 'Patient deactivated', 'tip': 'Set status to Deceased if the cat has passed away'}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting patient {patient_id}: {str(e)}", exc_info=True)
        if 'not found' in str(e).lower():
            return jsonify({'error': 'Patient not found'}), 404
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
