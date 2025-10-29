import os
from flask import jsonify, send_from_directory, request, Blueprint
from flask import current_app as app
from .models import (
    db, User, Patient, Pet, Appointment, AppointmentType, Client,
    Visit, VitalSigns, SOAPNote, Diagnosis, Vaccination,
    Medication, Prescription, Service, Invoice, InvoiceItem, Payment,
    Vendor, Product, PurchaseOrder, PurchaseOrderItem, InventoryTransaction
)
from .schemas import (
    client_schema,
    clients_schema,
    client_update_schema,
    patient_schema,
    patients_schema,
    patient_update_schema,
    appointment_schema,
    appointments_schema,
    appointment_type_schema,
    appointment_types_schema,
    vendor_schema,
    vendors_schema,
    product_schema,
    products_schema,
    purchase_order_schema,
    purchase_orders_schema,
    inventory_transaction_schema,
    inventory_transactions_schema,
)
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from functools import wraps
from flask import abort
from marshmallow import ValidationError as MarshmallowValidationError
from sqlalchemy.exc import IntegrityError

bp = Blueprint("main", __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "administrator":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated_function


@bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "User already exists"}), 400

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201


@bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        login_user(user)
        app.logger.info(f"User {username} logged in successfully.")
        return jsonify({"message": "Logged in successfully"}), 200

    app.logger.warning(f"Failed login attempt for username: {username}.")
    return jsonify({"message": "Invalid credentials"}), 401


@bp.route("/api/check_session")
def check_session():
    if current_user.is_authenticated:
        return jsonify({"id": current_user.id, "username": current_user.username, "role": current_user.role})
    return jsonify({}), 401


@bp.route("/api/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"})


@bp.route("/api/users", methods=["GET"])
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([{"id": user.id, "username": user.username, "role": user.role} for user in users])


@bp.route("/api/users/<int:user_id>", methods=["GET"])
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({"id": user.id, "username": user.username, "role": user.role})


@bp.route("/api/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    user.username = data.get("username", user.username)
    user.role = data.get("role", user.role)
    if "password" in data:
        user.set_password(data["password"])
    db.session.commit()
    return jsonify({"message": "User updated successfully"})


@bp.route("/api/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"})


@bp.route("/api/pets")
def get_pets():
    pets = Pet.query.all()
    return jsonify([{"name": pet.name, "breed": pet.breed, "owner": pet.owner} for pet in pets])


# ============================================================================
# APPOINTMENT API ENDPOINTS
# ============================================================================


@bp.route("/api/appointments", methods=["GET"])
@login_required
def get_appointments():
    """
    Get list of appointments with optional filtering and pagination
    Query params:
        - page: Page number (default 1)
        - per_page: Items per page (default 50)
        - status: Filter by status
        - client_id: Filter by client
        - patient_id: Filter by patient
        - assigned_staff_id: Filter by assigned staff
        - appointment_type_id: Filter by appointment type
        - start_date: Filter by start date (ISO format)
        - end_date: Filter by end date (ISO format)
    """
    try:
        # Get query parameters
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        status = request.args.get("status")
        client_id = request.args.get("client_id", type=int)
        patient_id = request.args.get("patient_id", type=int)
        assigned_staff_id = request.args.get("assigned_staff_id", type=int)
        appointment_type_id = request.args.get("appointment_type_id", type=int)
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # Build query
        query = Appointment.query

        if status:
            query = query.filter_by(status=status)
        if client_id:
            query = query.filter_by(client_id=client_id)
        if patient_id:
            query = query.filter_by(patient_id=patient_id)
        if assigned_staff_id:
            query = query.filter_by(assigned_staff_id=assigned_staff_id)
        if appointment_type_id:
            query = query.filter_by(appointment_type_id=appointment_type_id)
        if start_date:
            query = query.filter(Appointment.start_time >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Appointment.end_time <= datetime.fromisoformat(end_date))

        # Paginate
        pagination = query.order_by(Appointment.start_time).paginate(page=page, per_page=per_page, error_out=False)

        return jsonify(
            {
                "appointments": [apt.to_dict() for apt in pagination.items],
                "pagination": {
                    "page": pagination.page,
                    "per_page": pagination.per_page,
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev,
                },
            }
        ), 200

    except Exception as e:
        app.logger.error(f"Error fetching appointments: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/appointments/<int:appointment_id>", methods=["GET"])
@login_required
def get_appointment(appointment_id):
    """Get a specific appointment by ID"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        return jsonify(appointment.to_dict()), 200
    except Exception as e:
        app.logger.error(f"Error fetching appointment {appointment_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Appointment not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/appointments", methods=["POST"])
@login_required
def create_appointment():
    """Create a new appointment"""
    try:
        data = request.get_json()
        validated_data = appointment_schema.load(data)

        # Verify client exists
        client = Client.query.get(validated_data["client_id"])
        if not client:
            return jsonify({"error": "Client not found"}), 404

        # Verify patient exists if provided
        if validated_data.get("patient_id"):
            patient = Patient.query.get(validated_data["patient_id"])
            if not patient:
                return jsonify({"error": "Patient not found"}), 404

        appointment = Appointment(
            title=validated_data["title"],
            start_time=validated_data["start_time"],
            end_time=validated_data["end_time"],
            description=validated_data.get("description"),
            patient_id=validated_data.get("patient_id"),
            client_id=validated_data["client_id"],
            appointment_type_id=validated_data.get("appointment_type_id"),
            status=validated_data.get("status", "scheduled"),
            assigned_staff_id=validated_data.get("assigned_staff_id"),
            room=validated_data.get("room"),
            notes=validated_data.get("notes"),
            created_by_id=current_user.id,
        )

        db.session.add(appointment)
        db.session.commit()

        app.logger.info(f"Created appointment {appointment.id}")
        return jsonify(appointment.to_dict()), 201

    except MarshmallowValidationError as e:
        app.logger.warning(f"Validation error creating appointment: {e.messages}")
        return jsonify({"error": "Validation error", "details": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating appointment: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/appointments/<int:appointment_id>", methods=["PUT", "PATCH"])
@login_required
def update_appointment(appointment_id):
    """Update an appointment"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        data = request.get_json()
        validated_data = appointment_schema.load(data, partial=True)

        # Update fields
        for key, value in validated_data.items():
            if hasattr(appointment, key) and key not in ["id", "created_at", "created_by_id"]:
                setattr(appointment, key, value)

        # Handle status workflow timestamps
        if "status" in validated_data:
            if validated_data["status"] == "checked_in" and not appointment.check_in_time:
                appointment.check_in_time = datetime.utcnow()
            elif validated_data["status"] == "in_progress" and not appointment.actual_start_time:
                appointment.actual_start_time = datetime.utcnow()
            elif validated_data["status"] == "completed" and not appointment.actual_end_time:
                appointment.actual_end_time = datetime.utcnow()
            elif validated_data["status"] == "cancelled" and not appointment.cancelled_at:
                appointment.cancelled_at = datetime.utcnow()
                appointment.cancelled_by_id = current_user.id

        db.session.commit()
        app.logger.info(f"Updated appointment {appointment_id}")
        return jsonify(appointment.to_dict()), 200

    except MarshmallowValidationError as e:
        return jsonify({"error": "Validation error", "details": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating appointment {appointment_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Appointment not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/appointments/<int:appointment_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_appointment(appointment_id):
    """Delete an appointment (admin only)"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        db.session.delete(appointment)
        db.session.commit()

        app.logger.info(f"Deleted appointment {appointment_id}")
        return jsonify({"message": "Appointment deleted"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting appointment {appointment_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Appointment not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# APPOINTMENT TYPE API ENDPOINTS
# ============================================================================


@bp.route("/api/appointment-types", methods=["GET"])
@login_required
def get_appointment_types():
    """Get list of appointment types"""
    try:
        active_only = request.args.get("active_only", "true").lower() == "true"

        query = AppointmentType.query
        if active_only:
            query = query.filter_by(is_active=True)

        appointment_types = query.order_by(AppointmentType.name).all()
        return jsonify([apt.to_dict() for apt in appointment_types]), 200

    except Exception as e:
        app.logger.error(f"Error fetching appointment types: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/appointment-types/<int:type_id>", methods=["GET"])
@login_required
def get_appointment_type(type_id):
    """Get a specific appointment type by ID"""
    try:
        appointment_type = AppointmentType.query.get_or_404(type_id)
        return jsonify(appointment_type.to_dict()), 200
    except Exception as e:
        app.logger.error(f"Error fetching appointment type {type_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Appointment type not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/appointment-types", methods=["POST"])
@login_required
def create_appointment_type():
    """Create a new appointment type"""
    try:
        data = request.get_json()
        validated_data = appointment_type_schema.load(data)

        appointment_type = AppointmentType(**validated_data)
        db.session.add(appointment_type)
        db.session.commit()

        app.logger.info(f"Created appointment type: {appointment_type.name}")
        return jsonify(appointment_type.to_dict()), 201

    except MarshmallowValidationError as e:
        app.logger.warning(f"Validation error creating appointment type: {e.messages}")
        return jsonify({"error": "Validation error", "details": e.messages}), 400
    except IntegrityError as e:
        db.session.rollback()
        app.logger.error(f"Integrity error creating appointment type: {str(e)}")
        return jsonify({"error": "Appointment type name already exists"}), 409
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating appointment type: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/appointment-types/<int:type_id>", methods=["PUT", "PATCH"])
@login_required
def update_appointment_type(type_id):
    """Update an appointment type"""
    try:
        appointment_type = AppointmentType.query.get_or_404(type_id)
        data = request.get_json()
        validated_data = appointment_type_schema.load(data, partial=True)

        for key, value in validated_data.items():
            if hasattr(appointment_type, key):
                setattr(appointment_type, key, value)

        db.session.commit()
        app.logger.info(f"Updated appointment type {type_id}")
        return jsonify(appointment_type.to_dict()), 200

    except MarshmallowValidationError as e:
        return jsonify({"error": "Validation error", "details": e.messages}), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": "Appointment type name already exists"}), 409
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating appointment type {type_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Appointment type not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/appointment-types/<int:type_id>", methods=["DELETE"])
@login_required
def delete_appointment_type(type_id):
    """Soft delete an appointment type (set is_active=False) or hard delete (admin only)"""
    try:
        appointment_type = AppointmentType.query.get_or_404(type_id)

        # Check if hard delete is requested (admin only)
        hard_delete = request.args.get("hard", "false").lower() == "true"

        if hard_delete:
            if current_user.role != "administrator":
                return jsonify({"error": "Admin access required for hard delete"}), 403
            db.session.delete(appointment_type)
            db.session.commit()
            app.logger.info(f"Hard deleted appointment type {type_id}")
            return jsonify({"message": "Appointment type permanently deleted"}), 200
        else:
            appointment_type.is_active = False
            db.session.commit()
            app.logger.info(f"Soft deleted appointment type {type_id}")
            return jsonify({"message": "Appointment type deactivated"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting appointment type {type_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Appointment type not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# Client Management API Endpoints
# ============================================================================


@bp.route("/api/clients", methods=["GET"])
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
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        search = request.args.get("search", "").strip()
        active_only = request.args.get("active_only", "true").lower() == "true"

        app.logger.info(
            f"GET /api/clients - User: {current_user.username}, "
            f"Page: {page}, Search: '{search}', Active only: {active_only}"
        )

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
                    Client.phone_primary.ilike(search_filter),
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

        return (
            jsonify(
                {
                    "clients": result,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages,
                        "has_next": pagination.has_next,
                        "has_prev": pagination.has_prev,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Error getting clients: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/clients/<int:client_id>", methods=["GET"])
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
        if "not found" in str(e).lower():
            return jsonify({"error": "Client not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/clients", methods=["POST"])
@login_required
def create_client():
    """Create a new client"""
    try:
        data = request.get_json()

        app.logger.info(
            f"POST /api/clients - User: {current_user.username}, Data: {data.get('first_name')} {data.get('last_name')}"
        )

        # Validate request data
        try:
            validated_data = client_schema.load(data)
        except MarshmallowValidationError as err:
            app.logger.warning(f"Validation error creating client: {err.messages}")
            return jsonify({"error": "Validation error", "messages": err.messages}), 400

        # Check for duplicate email if provided
        if validated_data.get("email"):
            existing = Client.query.filter_by(email=validated_data["email"]).first()
            if existing:
                app.logger.warning(f"Attempted to create client with duplicate email: {validated_data['email']}")
                return jsonify({"error": "Email already exists"}), 409

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
        return jsonify({"error": "Database integrity error", "message": str(e)}), 409

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating client: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/clients/<int:client_id>", methods=["PUT"])
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
            return jsonify({"error": "Validation error", "messages": err.messages}), 400

        # Check for duplicate email if email is being changed
        if "email" in validated_data and validated_data["email"]:
            if validated_data["email"] != client.email:
                existing = Client.query.filter_by(email=validated_data["email"]).first()
                if existing:
                    app.logger.warning(
                        f"Attempted to update client {client_id} with duplicate email: {validated_data['email']}"
                    )
                    return jsonify({"error": "Email already exists"}), 409

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
        return jsonify({"error": "Database integrity error", "message": str(e)}), 409

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating client {client_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Client not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/clients/<int:client_id>", methods=["DELETE"])
@login_required
def delete_client(client_id):
    """
    Soft delete a client (sets is_active to False)
    Use ?hard=true query param for hard delete (requires admin)
    """
    try:
        hard_delete = request.args.get("hard", "false").lower() == "true"

        app.logger.info(f"DELETE /api/clients/{client_id} - User: {current_user.username}, Hard: {hard_delete}")

        client = Client.query.get_or_404(client_id)

        if hard_delete:
            # Hard delete requires admin role
            if current_user.role != "administrator":
                app.logger.warning(
                    f"Non-admin user {current_user.username} attempted hard delete of client {client_id}"
                )
                return jsonify({"error": "Admin access required for hard delete"}), 403

            db.session.delete(client)
            db.session.commit()
            app.logger.info(f"Hard deleted client {client_id}: {client.first_name} {client.last_name}")
            return jsonify({"message": "Client permanently deleted"}), 200
        else:
            # Soft delete
            client.is_active = False
            db.session.commit()
            app.logger.info(f"Soft deleted (deactivated) client {client_id}: {client.first_name} {client.last_name}")
            return jsonify({"message": "Client deactivated"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting client {client_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Client not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# Patient (Cat) Management API Endpoints
# ============================================================================


@bp.route("/api/patients", methods=["GET"])
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
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        search = request.args.get("search", "").strip()
        status_filter = request.args.get("status", "").strip()
        owner_id = request.args.get("owner_id", type=int)

        app.logger.info(
            f"GET /api/patients - User: {current_user.username}, Page: {page}, "
            f"Search: '{search}', Status: '{status_filter}', Owner: {owner_id}"
        )

        # Build query
        query = Patient.query

        # Filter by status
        if status_filter:
            query = query.filter_by(status=status_filter)
        else:
            # Default: show only active patients
            query = query.filter_by(status="Active")

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
                    Client.last_name.ilike(search_filter),
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

        return (
            jsonify(
                {
                    "patients": result,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages,
                        "has_next": pagination.has_next,
                        "has_prev": pagination.has_prev,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Error getting patients: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/patients/<int:patient_id>", methods=["GET"])
@login_required
def get_patient(patient_id):
    """Get a specific patient by ID"""
    try:
        app.logger.info(f"GET /api/patients/{patient_id} - User: {current_user.username}")

        patient = Patient.query.get_or_404(patient_id)

        if patient.status == "Deceased":
            app.logger.warning(f"Accessed deceased patient {patient_id}")

        app.logger.info(f"Retrieved patient {patient_id}: {patient.name}")

        result = patient_schema.dump(patient)
        return jsonify(result), 200

    except Exception as e:
        app.logger.error(f"Error getting patient {patient_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Patient not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/patients", methods=["POST"])
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
            return jsonify({"error": "Validation error", "messages": err.messages}), 400

        # Verify owner exists
        owner = Client.query.get(validated_data["owner_id"])
        if not owner:
            app.logger.warning(f"Attempted to create patient with non-existent owner_id: {validated_data['owner_id']}")
            return jsonify({"error": "Owner (client) not found"}), 404

        # Check for duplicate microchip if provided
        if validated_data.get("microchip_number"):
            existing = Patient.query.filter_by(microchip_number=validated_data["microchip_number"]).first()
            if existing:
                app.logger.warning(
                    f"Attempted to create patient with duplicate microchip: {validated_data['microchip_number']}"
                )
                return jsonify({"error": "Microchip number already exists"}), 409

        # Create new patient
        new_patient = Patient(**validated_data)
        db.session.add(new_patient)
        db.session.commit()

        app.logger.info(
            f"Created patient {new_patient.id}: {new_patient.name} (owner: {owner.first_name} {owner.last_name})"
        )

        result = patient_schema.dump(new_patient)
        return jsonify(result), 201

    except IntegrityError as e:
        db.session.rollback()
        app.logger.error(f"Integrity error creating patient: {str(e)}")
        return jsonify({"error": "Database integrity error", "message": str(e)}), 409

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating patient: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/patients/<int:patient_id>", methods=["PUT"])
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
            return jsonify({"error": "Validation error", "messages": err.messages}), 400

        # Check for duplicate microchip if microchip is being changed
        if "microchip_number" in validated_data and validated_data["microchip_number"]:
            if validated_data["microchip_number"] != patient.microchip_number:
                existing = Patient.query.filter_by(microchip_number=validated_data["microchip_number"]).first()
                if existing:
                    app.logger.warning(
                        f"Attempted to update patient {patient_id} with duplicate "
                        f"microchip: {validated_data['microchip_number']}"
                    )
                    return jsonify({"error": "Microchip number already exists"}), 409

        # Verify new owner exists if owner_id is being changed
        if "owner_id" in validated_data:
            owner = Client.query.get(validated_data["owner_id"])
            if not owner:
                app.logger.warning(
                    f"Attempted to update patient {patient_id} with non-existent owner_id: {validated_data['owner_id']}"
                )
                return jsonify({"error": "Owner (client) not found"}), 404

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
        return jsonify({"error": "Database integrity error", "message": str(e)}), 409

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating patient {patient_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Patient not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/patients/<int:patient_id>", methods=["DELETE"])
@login_required
def delete_patient(patient_id):
    """
    Delete a patient
    Note: For cats, we typically set status to 'Deceased' rather than delete.
    Use ?hard=true query param for hard delete (requires admin)
    """
    try:
        hard_delete = request.args.get("hard", "false").lower() == "true"

        app.logger.info(f"DELETE /api/patients/{patient_id} - User: {current_user.username}, Hard: {hard_delete}")

        patient = Patient.query.get_or_404(patient_id)

        if hard_delete:
            # Hard delete requires admin role
            if current_user.role != "administrator":
                app.logger.warning(
                    f"Non-admin user {current_user.username} attempted hard delete of patient {patient_id}"
                )
                return jsonify({"error": "Admin access required for hard delete"}), 403

            db.session.delete(patient)
            db.session.commit()
            app.logger.info(f"Hard deleted patient {patient_id}: {patient.name}")
            return jsonify({"message": "Patient permanently deleted"}), 200
        else:
            # Soft delete - set to inactive
            patient.status = "Inactive"
            db.session.commit()
            app.logger.info(f"Soft deleted (deactivated) patient {patient_id}: {patient.name}")
            return (
                jsonify(
                    {
                        "message": "Patient deactivated",
                        "tip": "Set status to Deceased if the cat has passed away",
                    }
                ),
                200,
            )

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting patient {patient_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Patient not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# MEDICAL RECORDS - VISIT ENDPOINTS
# ============================================================================


@bp.route("/api/visits", methods=["GET"])
@login_required
def get_visits():
    """Get all visits with optional filtering"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        patient_id = request.args.get("patient_id", type=int)
        status = request.args.get("status", "").strip()
        visit_type = request.args.get("visit_type", "").strip()

        app.logger.info(
            f"GET /api/visits - User: {current_user.username}, Page: {page}, "
            f"Patient: {patient_id}, Status: '{status}', Type: '{visit_type}'"
        )

        from .models import Visit

        query = Visit.query

        # Filter by patient if specified
        if patient_id:
            query = query.filter_by(patient_id=patient_id)

        # Filter by status
        if status:
            query = query.filter_by(status=status)

        # Filter by visit type
        if visit_type:
            query = query.filter_by(visit_type=visit_type)

        # Order by visit date descending (most recent first)
        query = query.order_by(Visit.visit_date.desc())

        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "visits": [visit.to_dict() for visit in paginated.items],
                    "total": paginated.total,
                    "pages": paginated.pages,
                    "current_page": page,
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Error fetching visits: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/visits/<int:visit_id>", methods=["GET"])
@login_required
def get_visit(visit_id):
    """Get a single visit by ID"""
    try:
        from .models import Visit

        visit = Visit.query.get_or_404(visit_id)
        app.logger.info(f"GET /api/visits/{visit_id} - User: {current_user.username}")
        return jsonify(visit.to_dict()), 200

    except Exception as e:
        app.logger.error(f"Error fetching visit {visit_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Visit not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/visits", methods=["POST"])
@login_required
def create_visit():
    """Create a new visit"""
    try:
        from .models import Visit, Patient
        from .schemas import visit_schema

        data = request.get_json()
        app.logger.info(f"POST /api/visits - User: {current_user.username}, Data: {data}")

        # Validate data
        validated_data = visit_schema.load(data)

        # Verify patient exists
        patient = Patient.query.get(validated_data["patient_id"])
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Create visit
        visit = Visit(
            visit_date=validated_data.get("visit_date"),
            visit_type=validated_data["visit_type"],
            status=validated_data.get("status", "scheduled"),
            patient_id=validated_data["patient_id"],
            veterinarian_id=validated_data.get("veterinarian_id"),
            appointment_id=validated_data.get("appointment_id"),
            chief_complaint=validated_data.get("chief_complaint"),
            visit_notes=validated_data.get("visit_notes"),
        )

        db.session.add(visit)
        db.session.commit()

        app.logger.info(f"Created visit {visit.id} for patient {patient.name}")
        return jsonify(visit.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating visit: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/visits/<int:visit_id>", methods=["PUT"])
@login_required
def update_visit(visit_id):
    """Update a visit"""
    try:
        from .models import Visit
        from .schemas import visit_schema

        visit = Visit.query.get_or_404(visit_id)
        data = request.get_json()

        app.logger.info(f"PUT /api/visits/{visit_id} - User: {current_user.username}, Data: {data}")

        # Validate data (partial update allowed)
        validated_data = visit_schema.load(data, partial=True)

        # Update fields
        for key, value in validated_data.items():
            if hasattr(visit, key):
                setattr(visit, key, value)

        # If marking as completed, set completed_at
        if validated_data.get("status") == "completed" and not visit.completed_at:

            visit.completed_at = datetime.utcnow()

        db.session.commit()

        app.logger.info(f"Updated visit {visit_id}")
        return jsonify(visit.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating visit {visit_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Visit not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/visits/<int:visit_id>", methods=["DELETE"])
@login_required
def delete_visit(visit_id):
    """Delete a visit"""
    try:
        from .models import Visit

        visit = Visit.query.get_or_404(visit_id)

        app.logger.info(f"DELETE /api/visits/{visit_id} - User: {current_user.username}")

        db.session.delete(visit)
        db.session.commit()

        app.logger.info(f"Deleted visit {visit_id}")
        return jsonify({"message": "Visit deleted"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting visit {visit_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Visit not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# MEDICAL RECORDS - VITAL SIGNS ENDPOINTS
# ============================================================================


@bp.route("/api/vital-signs", methods=["GET"])
@login_required
def get_vital_signs_list():
    """Get all vital signs with optional filtering"""
    try:
        visit_id = request.args.get("visit_id", type=int)

        from .models import VitalSigns

        query = VitalSigns.query

        if visit_id:
            query = query.filter_by(visit_id=visit_id)

        query = query.order_by(VitalSigns.recorded_at.desc())
        vital_signs = query.all()

        from .schemas import vital_signs_list_schema

        return jsonify(vital_signs_list_schema.dump(vital_signs)), 200

    except Exception as e:
        app.logger.error(f"Error fetching vital signs: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/vital-signs/<int:vital_signs_id>", methods=["GET"])
@login_required
def get_vital_signs(vital_signs_id):
    """Get a single vital signs record by ID"""
    try:
        from .models import VitalSigns

        vital_signs = VitalSigns.query.get_or_404(vital_signs_id)
        return jsonify(vital_signs.to_dict()), 200

    except Exception as e:
        app.logger.error(f"Error fetching vital signs {vital_signs_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Vital signs not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/vital-signs", methods=["POST"])
@login_required
def create_vital_signs():
    """Create a new vital signs record"""
    try:
        from .models import VitalSigns, Visit
        from .schemas import vital_signs_schema

        data = request.get_json()
        validated_data = vital_signs_schema.load(data)

        # Verify visit exists
        visit = Visit.query.get(validated_data["visit_id"])
        if not visit:
            return jsonify({"error": "Visit not found"}), 404

        # Create vital signs
        vital_signs = VitalSigns(
            visit_id=validated_data["visit_id"],
            temperature_c=validated_data.get("temperature_c"),
            weight_kg=validated_data.get("weight_kg"),
            heart_rate=validated_data.get("heart_rate"),
            respiratory_rate=validated_data.get("respiratory_rate"),
            blood_pressure_systolic=validated_data.get("blood_pressure_systolic"),
            blood_pressure_diastolic=validated_data.get("blood_pressure_diastolic"),
            capillary_refill_time=validated_data.get("capillary_refill_time"),
            mucous_membrane_color=validated_data.get("mucous_membrane_color"),
            body_condition_score=validated_data.get("body_condition_score"),
            pain_score=validated_data.get("pain_score"),
            notes=validated_data.get("notes"),
            recorded_by_id=current_user.id,
        )

        db.session.add(vital_signs)
        db.session.commit()

        app.logger.info(f"Created vital signs {vital_signs.id} for visit {visit.id}")
        return jsonify(vital_signs_schema.dump(vital_signs)), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating vital signs: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/vital-signs/<int:vital_signs_id>", methods=["PUT"])
@login_required
def update_vital_signs(vital_signs_id):
    """Update a vital signs record"""
    try:
        from .models import VitalSigns
        from .schemas import vital_signs_schema

        vital_signs = VitalSigns.query.get_or_404(vital_signs_id)
        data = request.get_json()
        validated_data = vital_signs_schema.load(data, partial=True)

        for key, value in validated_data.items():
            if hasattr(vital_signs, key) and key != "visit_id":
                setattr(vital_signs, key, value)

        db.session.commit()
        app.logger.info(f"Updated vital signs {vital_signs_id}")
        return jsonify(vital_signs_schema.dump(vital_signs)), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating vital signs {vital_signs_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Vital signs not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/vital-signs/<int:vital_signs_id>", methods=["DELETE"])
@login_required
def delete_vital_signs(vital_signs_id):
    """Delete a vital signs record"""
    try:
        from .models import VitalSigns

        vital_signs = VitalSigns.query.get_or_404(vital_signs_id)
        db.session.delete(vital_signs)
        db.session.commit()

        app.logger.info(f"Deleted vital signs {vital_signs_id}")
        return jsonify({"message": "Vital signs deleted"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting vital signs {vital_signs_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Vital signs not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# MEDICAL RECORDS - SOAP NOTE ENDPOINTS
# ============================================================================


@bp.route("/api/soap-notes", methods=["GET"])
@login_required
def get_soap_notes():
    """Get all SOAP notes with optional filtering"""
    try:
        visit_id = request.args.get("visit_id", type=int)

        from .models import SOAPNote

        query = SOAPNote.query

        if visit_id:
            query = query.filter_by(visit_id=visit_id)

        query = query.order_by(SOAPNote.created_at.desc())
        soap_notes = query.all()

        from .schemas import soap_notes_schema

        return jsonify(soap_notes_schema.dump(soap_notes)), 200

    except Exception as e:
        app.logger.error(f"Error fetching SOAP notes: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/soap-notes/<int:soap_note_id>", methods=["GET"])
@login_required
def get_soap_note(soap_note_id):
    """Get a single SOAP note by ID"""
    try:
        from .models import SOAPNote

        soap_note = SOAPNote.query.get_or_404(soap_note_id)
        return jsonify(soap_note.to_dict()), 200

    except Exception as e:
        app.logger.error(f"Error fetching SOAP note {soap_note_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "SOAP note not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/soap-notes", methods=["POST"])
@login_required
def create_soap_note():
    """Create a new SOAP note"""
    try:
        from .models import SOAPNote, Visit
        from .schemas import soap_note_schema

        data = request.get_json()
        validated_data = soap_note_schema.load(data)

        # Verify visit exists
        visit = Visit.query.get(validated_data["visit_id"])
        if not visit:
            return jsonify({"error": "Visit not found"}), 404

        # Create SOAP note
        soap_note = SOAPNote(
            visit_id=validated_data["visit_id"],
            subjective=validated_data.get("subjective"),
            objective=validated_data.get("objective"),
            assessment=validated_data.get("assessment"),
            plan=validated_data.get("plan"),
            created_by_id=current_user.id,
        )

        db.session.add(soap_note)
        db.session.commit()

        app.logger.info(f"Created SOAP note {soap_note.id} for visit {visit.id}")
        return jsonify(soap_note.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating SOAP note: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/soap-notes/<int:soap_note_id>", methods=["PUT"])
@login_required
def update_soap_note(soap_note_id):
    """Update a SOAP note"""
    try:
        from .models import SOAPNote
        from .schemas import soap_note_schema

        soap_note = SOAPNote.query.get_or_404(soap_note_id)
        data = request.get_json()
        validated_data = soap_note_schema.load(data, partial=True)

        for key, value in validated_data.items():
            if hasattr(soap_note, key) and key not in ["visit_id", "created_by_id"]:
                setattr(soap_note, key, value)

        db.session.commit()
        app.logger.info(f"Updated SOAP note {soap_note_id}")
        return jsonify(soap_note.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating SOAP note {soap_note_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "SOAP note not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/soap-notes/<int:soap_note_id>", methods=["DELETE"])
@login_required
def delete_soap_note(soap_note_id):
    """Delete a SOAP note"""
    try:
        from .models import SOAPNote

        soap_note = SOAPNote.query.get_or_404(soap_note_id)
        db.session.delete(soap_note)
        db.session.commit()

        app.logger.info(f"Deleted SOAP note {soap_note_id}")
        return jsonify({"message": "SOAP note deleted"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting SOAP note {soap_note_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "SOAP note not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# MEDICAL RECORDS - DIAGNOSIS ENDPOINTS
# ============================================================================


@bp.route("/api/diagnoses", methods=["GET"])
@login_required
def get_diagnoses():
    """Get all diagnoses with optional filtering"""
    try:
        visit_id = request.args.get("visit_id", type=int)
        status = request.args.get("status", "").strip()

        from .models import Diagnosis

        query = Diagnosis.query

        if visit_id:
            query = query.filter_by(visit_id=visit_id)

        if status:
            query = query.filter_by(status=status)

        query = query.order_by(Diagnosis.created_at.desc())
        diagnoses = query.all()

        from .schemas import diagnoses_schema

        return jsonify(diagnoses_schema.dump(diagnoses)), 200

    except Exception as e:
        app.logger.error(f"Error fetching diagnoses: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/diagnoses/<int:diagnosis_id>", methods=["GET"])
@login_required
def get_diagnosis(diagnosis_id):
    """Get a single diagnosis by ID"""
    try:
        from .models import Diagnosis

        diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
        return jsonify(diagnosis.to_dict()), 200

    except Exception as e:
        app.logger.error(f"Error fetching diagnosis {diagnosis_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Diagnosis not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/diagnoses", methods=["POST"])
@login_required
def create_diagnosis():
    """Create a new diagnosis"""
    try:
        from .models import Diagnosis, Visit
        from .schemas import diagnosis_schema

        data = request.get_json()
        validated_data = diagnosis_schema.load(data)

        # Verify visit exists
        visit = Visit.query.get(validated_data["visit_id"])
        if not visit:
            return jsonify({"error": "Visit not found"}), 404

        # Create diagnosis
        diagnosis = Diagnosis(
            visit_id=validated_data["visit_id"],
            diagnosis_name=validated_data["diagnosis_name"],
            icd_code=validated_data.get("icd_code"),
            diagnosis_type=validated_data.get("diagnosis_type", "primary"),
            severity=validated_data.get("severity"),
            status=validated_data.get("status", "active"),
            notes=validated_data.get("notes"),
            onset_date=validated_data.get("onset_date"),
            resolution_date=validated_data.get("resolution_date"),
            created_by_id=current_user.id,
        )

        db.session.add(diagnosis)
        db.session.commit()

        app.logger.info(f"Created diagnosis {diagnosis.id} for visit {visit.id}")
        return jsonify(diagnosis.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating diagnosis: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/diagnoses/<int:diagnosis_id>", methods=["PUT"])
@login_required
def update_diagnosis(diagnosis_id):
    """Update a diagnosis"""
    try:
        from .models import Diagnosis
        from .schemas import diagnosis_schema

        diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
        data = request.get_json()
        validated_data = diagnosis_schema.load(data, partial=True)

        for key, value in validated_data.items():
            if hasattr(diagnosis, key) and key not in ["visit_id", "created_by_id"]:
                setattr(diagnosis, key, value)

        db.session.commit()
        app.logger.info(f"Updated diagnosis {diagnosis_id}")
        return jsonify(diagnosis.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating diagnosis {diagnosis_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Diagnosis not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/diagnoses/<int:diagnosis_id>", methods=["DELETE"])
@login_required
def delete_diagnosis(diagnosis_id):
    """Delete a diagnosis"""
    try:
        from .models import Diagnosis

        diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
        db.session.delete(diagnosis)
        db.session.commit()

        app.logger.info(f"Deleted diagnosis {diagnosis_id}")
        return jsonify({"message": "Diagnosis deleted"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting diagnosis {diagnosis_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Diagnosis not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# MEDICAL RECORDS - VACCINATION ENDPOINTS
# ============================================================================


@bp.route("/api/vaccinations", methods=["GET"])
@login_required
def get_vaccinations():
    """Get all vaccinations with optional filtering"""
    try:
        patient_id = request.args.get("patient_id", type=int)
        status = request.args.get("status", "").strip()

        from .models import Vaccination

        query = Vaccination.query

        if patient_id:
            query = query.filter_by(patient_id=patient_id)

        if status:
            query = query.filter_by(status=status)

        query = query.order_by(Vaccination.administration_date.desc())
        vaccinations = query.all()

        from .schemas import vaccinations_schema

        return jsonify(vaccinations_schema.dump(vaccinations)), 200

    except Exception as e:
        app.logger.error(f"Error fetching vaccinations: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/vaccinations/<int:vaccination_id>", methods=["GET"])
@login_required
def get_vaccination(vaccination_id):
    """Get a single vaccination by ID"""
    try:
        from .models import Vaccination

        vaccination = Vaccination.query.get_or_404(vaccination_id)
        return jsonify(vaccination.to_dict()), 200

    except Exception as e:
        app.logger.error(f"Error fetching vaccination {vaccination_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Vaccination not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/vaccinations", methods=["POST"])
@login_required
def create_vaccination():
    """Create a new vaccination record"""
    try:
        from .models import Vaccination, Patient
        from .schemas import vaccination_schema

        data = request.get_json()
        validated_data = vaccination_schema.load(data)

        # Verify patient exists
        patient = Patient.query.get(validated_data["patient_id"])
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Create vaccination
        vaccination = Vaccination(
            patient_id=validated_data["patient_id"],
            visit_id=validated_data.get("visit_id"),
            vaccine_name=validated_data["vaccine_name"],
            vaccine_type=validated_data.get("vaccine_type"),
            manufacturer=validated_data.get("manufacturer"),
            lot_number=validated_data.get("lot_number"),
            serial_number=validated_data.get("serial_number"),
            administration_date=validated_data["administration_date"],
            expiration_date=validated_data.get("expiration_date"),
            next_due_date=validated_data.get("next_due_date"),
            dosage=validated_data.get("dosage"),
            route=validated_data.get("route"),
            administration_site=validated_data.get("administration_site"),
            status=validated_data.get("status", "current"),
            notes=validated_data.get("notes"),
            adverse_reactions=validated_data.get("adverse_reactions"),
            administered_by_id=current_user.id,
        )

        db.session.add(vaccination)
        db.session.commit()

        app.logger.info(f"Created vaccination {vaccination.id} for patient {patient.name}")
        return jsonify(vaccination.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating vaccination: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/vaccinations/<int:vaccination_id>", methods=["PUT"])
@login_required
def update_vaccination(vaccination_id):
    """Update a vaccination record"""
    try:
        from .models import Vaccination
        from .schemas import vaccination_schema

        vaccination = Vaccination.query.get_or_404(vaccination_id)
        data = request.get_json()
        validated_data = vaccination_schema.load(data, partial=True)

        for key, value in validated_data.items():
            if hasattr(vaccination, key) and key not in ["patient_id", "administered_by_id"]:
                setattr(vaccination, key, value)

        db.session.commit()
        app.logger.info(f"Updated vaccination {vaccination_id}")
        return jsonify(vaccination.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating vaccination {vaccination_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Vaccination not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/vaccinations/<int:vaccination_id>", methods=["DELETE"])
@login_required
def delete_vaccination(vaccination_id):
    """Delete a vaccination record"""
    try:
        from .models import Vaccination

        vaccination = Vaccination.query.get_or_404(vaccination_id)
        db.session.delete(vaccination)
        db.session.commit()

        app.logger.info(f"Deleted vaccination {vaccination_id}")
        return jsonify({"message": "Vaccination deleted"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting vaccination {vaccination_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Vaccination not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# MEDICATION ENDPOINTS
# ============================================================================


@bp.route("/api/medications", methods=["GET"])
@login_required
def get_medications():
    """Get all medications (drug database) with optional filtering"""
    try:
        from .models import Medication

        is_active = request.args.get("is_active", "").strip()
        drug_class = request.args.get("drug_class", "").strip()
        search = request.args.get("search", "").strip()

        query = Medication.query

        if is_active:
            active_val = is_active.lower() == "true"
            query = query.filter_by(is_active=active_val)

        if drug_class:
            query = query.filter_by(drug_class=drug_class)

        if search:
            search_term = f"%{search}%"
            query = query.filter(Medication.drug_name.ilike(search_term))

        medications = query.order_by(Medication.drug_name).all()
        return jsonify({"medications": [med.to_dict() for med in medications], "total": len(medications)}), 200

    except Exception as e:
        app.logger.error(f"Error fetching medications: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/medications/<int:medication_id>", methods=["GET"])
@login_required
def get_medication(medication_id):
    """Get a specific medication by ID"""
    try:
        from .models import Medication

        medication = Medication.query.get_or_404(medication_id)
        return jsonify(medication.to_dict()), 200

    except Exception as e:
        app.logger.error(f"Error fetching medication {medication_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Medication not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/medications", methods=["POST"])
@login_required
def create_medication():
    """Create a new medication in the drug database"""
    try:
        from .models import Medication
        from .schemas import medication_schema

        data = request.get_json()
        validated_data = medication_schema.load(data)

        # Check for duplicate drug name
        existing = Medication.query.filter_by(drug_name=validated_data["drug_name"]).first()
        if existing:
            return jsonify({"error": "Medication with this name already exists"}), 400

        medication = Medication(
            drug_name=validated_data["drug_name"],
            brand_names=validated_data.get("brand_names"),
            drug_class=validated_data.get("drug_class"),
            controlled_substance=validated_data.get("controlled_substance", False),
            dea_schedule=validated_data.get("dea_schedule"),
            available_forms=validated_data.get("available_forms"),
            strengths=validated_data.get("strengths"),
            typical_dose_cats=validated_data.get("typical_dose_cats"),
            dosing_frequency=validated_data.get("dosing_frequency"),
            route_of_administration=validated_data.get("route_of_administration"),
            indications=validated_data.get("indications"),
            contraindications=validated_data.get("contraindications"),
            side_effects=validated_data.get("side_effects"),
            warnings=validated_data.get("warnings"),
            stock_quantity=validated_data.get("stock_quantity", 0),
            reorder_level=validated_data.get("reorder_level", 0),
            unit_cost=validated_data.get("unit_cost"),
            is_active=validated_data.get("is_active", True),
        )

        db.session.add(medication)
        db.session.commit()

        app.logger.info(f"Created medication: {medication.drug_name}")
        return jsonify(medication.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating medication: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/medications/<int:medication_id>", methods=["PUT"])
@login_required
def update_medication(medication_id):
    """Update a medication"""
    try:
        from .models import Medication
        from .schemas import medication_schema

        medication = Medication.query.get_or_404(medication_id)
        data = request.get_json()
        validated_data = medication_schema.load(data, partial=True)

        for key, value in validated_data.items():
            if hasattr(medication, key):
                setattr(medication, key, value)

        db.session.commit()
        app.logger.info(f"Updated medication {medication_id}")
        return jsonify(medication.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating medication {medication_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Medication not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/medications/<int:medication_id>", methods=["DELETE"])
@login_required
def delete_medication(medication_id):
    """Delete a medication"""
    try:
        from .models import Medication

        medication = Medication.query.get_or_404(medication_id)

        # Check if medication has prescriptions
        if medication.prescriptions:
            return (
                jsonify({"error": "Cannot delete medication with existing prescriptions. Set to inactive instead."}),
                400,
            )

        db.session.delete(medication)
        db.session.commit()

        app.logger.info(f"Deleted medication {medication_id}")
        return jsonify({"message": "Medication deleted"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting medication {medication_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Medication not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# PRESCRIPTION ENDPOINTS
# ============================================================================


@bp.route("/api/prescriptions", methods=["GET"])
@login_required
def get_prescriptions():
    """Get all prescriptions with optional filtering"""
    try:
        from .models import Prescription

        patient_id = request.args.get("patient_id", type=int)
        visit_id = request.args.get("visit_id", type=int)
        status = request.args.get("status", "").strip()

        query = Prescription.query

        if patient_id:
            query = query.filter_by(patient_id=patient_id)

        if visit_id:
            query = query.filter_by(visit_id=visit_id)

        if status:
            query = query.filter_by(status=status)

        prescriptions = query.order_by(Prescription.created_at.desc()).all()
        return jsonify({"prescriptions": [rx.to_dict() for rx in prescriptions], "total": len(prescriptions)}), 200

    except Exception as e:
        app.logger.error(f"Error fetching prescriptions: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/prescriptions/<int:prescription_id>", methods=["GET"])
@login_required
def get_prescription(prescription_id):
    """Get a specific prescription by ID"""
    try:
        from .models import Prescription

        prescription = Prescription.query.get_or_404(prescription_id)
        return jsonify(prescription.to_dict()), 200

    except Exception as e:
        app.logger.error(f"Error fetching prescription {prescription_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Prescription not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/prescriptions", methods=["POST"])
@login_required
def create_prescription():
    """Create a new prescription"""
    try:
        from .models import Prescription, Patient, Medication, Visit
        from .schemas import prescription_schema

        data = request.get_json()
        validated_data = prescription_schema.load(data)

        # Verify patient exists
        patient = Patient.query.get(validated_data["patient_id"])
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Verify medication exists
        medication = Medication.query.get(validated_data["medication_id"])
        if not medication:
            return jsonify({"error": "Medication not found"}), 404

        # Verify visit if provided
        if validated_data.get("visit_id"):
            visit = Visit.query.get(validated_data["visit_id"])
            if not visit:
                return jsonify({"error": "Visit not found"}), 404

        # Initialize refills_remaining if not provided
        if "refills_remaining" not in validated_data or validated_data["refills_remaining"] is None:
            validated_data["refills_remaining"] = validated_data.get("refills_allowed", 0)

        prescription = Prescription(
            patient_id=validated_data["patient_id"],
            visit_id=validated_data.get("visit_id"),
            medication_id=validated_data["medication_id"],
            dosage=validated_data["dosage"],
            dosage_form=validated_data.get("dosage_form"),
            frequency=validated_data["frequency"],
            route=validated_data.get("route"),
            duration_days=validated_data.get("duration_days"),
            quantity=validated_data["quantity"],
            refills_allowed=validated_data.get("refills_allowed", 0),
            refills_remaining=validated_data["refills_remaining"],
            instructions=validated_data.get("instructions"),
            indication=validated_data.get("indication"),
            status=validated_data.get("status", "active"),
            start_date=validated_data["start_date"],
            end_date=validated_data.get("end_date"),
            prescribed_by_id=current_user.id,
        )

        db.session.add(prescription)
        db.session.commit()

        app.logger.info(f"Created prescription {prescription.id} for patient {patient.name}")
        return jsonify(prescription.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating prescription: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/prescriptions/<int:prescription_id>", methods=["PUT"])
@login_required
def update_prescription(prescription_id):
    """Update a prescription"""
    try:
        from .models import Prescription
        from .schemas import prescription_schema

        prescription = Prescription.query.get_or_404(prescription_id)
        data = request.get_json()
        validated_data = prescription_schema.load(data, partial=True)

        for key, value in validated_data.items():
            if hasattr(prescription, key) and key not in ["patient_id", "medication_id", "prescribed_by_id"]:
                setattr(prescription, key, value)

        db.session.commit()
        app.logger.info(f"Updated prescription {prescription_id}")
        return jsonify(prescription.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating prescription {prescription_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Prescription not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/prescriptions/<int:prescription_id>", methods=["DELETE"])
@login_required
def delete_prescription(prescription_id):
    """Delete a prescription"""
    try:
        from .models import Prescription

        prescription = Prescription.query.get_or_404(prescription_id)
        db.session.delete(prescription)
        db.session.commit()

        app.logger.info(f"Deleted prescription {prescription_id}")
        return jsonify({"message": "Prescription deleted"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting prescription {prescription_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Prescription not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# SERVICE CATALOG ENDPOINTS
# ============================================================================


@bp.route("/api/services", methods=["GET"])
@login_required
def get_services():
    """Get all services/products with optional filtering"""
    try:
        from .models import Service

        is_active = request.args.get("is_active", "").strip()
        category = request.args.get("category", "").strip()
        service_type = request.args.get("service_type", "").strip()

        query = Service.query

        if is_active:
            active_val = is_active.lower() == "true"
            query = query.filter_by(is_active=active_val)

        if category:
            query = query.filter_by(category=category)

        if service_type:
            query = query.filter_by(service_type=service_type)

        services = query.order_by(Service.name).all()
        return jsonify({"services": [s.to_dict() for s in services], "total": len(services)}), 200

    except Exception as e:
        app.logger.error(f"Error fetching services: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/services/<int:service_id>", methods=["GET"])
@login_required
def get_service(service_id):
    """Get a specific service by ID"""
    try:
        from .models import Service

        service = Service.query.get_or_404(service_id)
        return jsonify(service.to_dict()), 200

    except Exception as e:
        app.logger.error(f"Error fetching service {service_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Service not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/services", methods=["POST"])
@login_required
def create_service():
    """Create a new service"""
    try:
        from .models import Service
        from .schemas import service_schema

        data = request.get_json()
        validated_data = service_schema.load(data)

        service = Service(
            name=validated_data["name"],
            description=validated_data.get("description"),
            category=validated_data.get("category"),
            service_type=validated_data.get("service_type", "service"),
            unit_price=validated_data["unit_price"],
            cost=validated_data.get("cost"),
            taxable=validated_data.get("taxable", True),
            is_active=validated_data.get("is_active", True),
        )

        db.session.add(service)
        db.session.commit()

        app.logger.info(f"Created service: {service.name}")
        return jsonify(service.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating service: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/services/<int:service_id>", methods=["PUT"])
@login_required
def update_service(service_id):
    """Update a service"""
    try:
        from .models import Service
        from .schemas import service_schema

        service = Service.query.get_or_404(service_id)
        data = request.get_json()
        validated_data = service_schema.load(data, partial=True)

        for key, value in validated_data.items():
            if hasattr(service, key):
                setattr(service, key, value)

        db.session.commit()
        app.logger.info(f"Updated service {service_id}")
        return jsonify(service.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating service {service_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Service not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/services/<int:service_id>", methods=["DELETE"])
@login_required
def delete_service(service_id):
    """Delete a service"""
    try:
        from .models import Service

        service = Service.query.get_or_404(service_id)
        db.session.delete(service)
        db.session.commit()

        app.logger.info(f"Deleted service {service_id}")
        return jsonify({"message": "Service deleted"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting service {service_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Service not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# INVOICE ENDPOINTS
# ============================================================================


@bp.route("/api/invoices", methods=["GET"])
@login_required
def get_invoices():
    """Get all invoices with optional filtering"""
    try:
        from .models import Invoice

        client_id = request.args.get("client_id", type=int)
        status = request.args.get("status", "").strip()
        visit_id = request.args.get("visit_id", type=int)

        query = Invoice.query

        if client_id:
            query = query.filter_by(client_id=client_id)

        if status:
            query = query.filter_by(status=status)

        if visit_id:
            query = query.filter_by(visit_id=visit_id)

        invoices = query.order_by(Invoice.invoice_date.desc()).all()

        # Include line items in response
        result = []
        for invoice in invoices:
            invoice_dict = invoice.to_dict()
            invoice_dict["items"] = [item.to_dict() for item in invoice.items]
            result.append(invoice_dict)

        return jsonify({"invoices": result, "total": len(result)}), 200

    except Exception as e:
        app.logger.error(f"Error fetching invoices: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/invoices/<int:invoice_id>", methods=["GET"])
@login_required
def get_invoice(invoice_id):
    """Get a specific invoice by ID with items and payments"""
    try:
        from .models import Invoice

        invoice = Invoice.query.get_or_404(invoice_id)
        invoice_dict = invoice.to_dict()

        # Include line items
        invoice_dict["items"] = [item.to_dict() for item in invoice.items]

        # Include payments
        invoice_dict["payments"] = [payment.to_dict() for payment in invoice.payments]

        return jsonify(invoice_dict), 200

    except Exception as e:
        app.logger.error(f"Error fetching invoice {invoice_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Invoice not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/invoices", methods=["POST"])
@login_required
def create_invoice():
    """Create a new invoice with line items"""
    try:
        from .models import Invoice, InvoiceItem, Client
        from .schemas import invoice_schema
        from decimal import Decimal
        from datetime import datetime

        data = request.get_json()
        validated_data = invoice_schema.load(data)

        # Verify client exists
        client = Client.query.get(validated_data["client_id"])
        if not client:
            return jsonify({"error": "Client not found"}), 404

        # Generate invoice number (simple format: INV-YYYYMMDD-XXXX)
        today = datetime.utcnow().strftime("%Y%m%d")
        count = Invoice.query.filter(Invoice.invoice_number.like(f"INV-{today}-%")).count()
        invoice_number = f"INV-{today}-{count + 1:04d}"

        # Calculate totals from line items
        items_data = validated_data.get("items", [])
        subtotal = Decimal("0.0")
        tax_amount = Decimal("0.0")
        tax_rate = Decimal(str(validated_data.get("tax_rate", "0.0")))

        for item_data in items_data:
            item_total = Decimal(str(item_data["total_price"]))
            subtotal += item_total
            if item_data.get("taxable", True):
                tax_amount += item_total * (tax_rate / Decimal("100.0"))

        discount = Decimal(str(validated_data.get("discount_amount", "0.0")))
        total = subtotal + tax_amount - discount

        # Create invoice
        invoice = Invoice(
            client_id=validated_data["client_id"],
            patient_id=validated_data.get("patient_id"),
            visit_id=validated_data.get("visit_id"),
            invoice_number=invoice_number,
            invoice_date=validated_data["invoice_date"],
            due_date=validated_data.get("due_date"),
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            discount_amount=discount,
            total_amount=total,
            amount_paid=Decimal("0.0"),
            balance_due=total,
            status=validated_data.get("status", "draft"),
            notes=validated_data.get("notes"),
            created_by_id=current_user.id,
        )

        db.session.add(invoice)
        db.session.flush()  # Get invoice ID

        # Create line items
        for item_data in items_data:
            item = InvoiceItem(
                invoice_id=invoice.id,
                service_id=item_data.get("service_id"),
                description=item_data["description"],
                quantity=Decimal(str(item_data.get("quantity", "1.0"))),
                unit_price=Decimal(str(item_data["unit_price"])),
                total_price=Decimal(str(item_data["total_price"])),
                taxable=item_data.get("taxable", True),
            )
            db.session.add(item)

        db.session.commit()

        # Return invoice with items
        invoice_dict = invoice.to_dict()
        invoice_dict["items"] = [item.to_dict() for item in invoice.items]

        app.logger.info(f"Created invoice {invoice.invoice_number}")
        return jsonify(invoice_dict), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating invoice: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/invoices/<int:invoice_id>", methods=["PUT"])
@login_required
def update_invoice(invoice_id):
    """Update an invoice"""
    try:
        from .models import Invoice, InvoiceItem
        from .schemas import invoice_schema
        from decimal import Decimal

        invoice = Invoice.query.get_or_404(invoice_id)
        data = request.get_json()
        validated_data = invoice_schema.load(data, partial=True)

        # Update basic fields
        for key in ["patient_id", "visit_id", "invoice_date", "due_date", "status", "notes", "discount_amount"]:
            if key in validated_data:
                setattr(invoice, key, validated_data[key])

        # If items are provided, update them
        if "items" in validated_data:
            # Delete existing items
            for item in invoice.items:
                db.session.delete(item)

            # Create new items and recalculate totals
            items_data = validated_data["items"]
            subtotal = Decimal("0.0")
            tax_amount = Decimal("0.0")
            tax_rate = Decimal(str(validated_data.get("tax_rate", invoice.tax_rate)))

            for item_data in items_data:
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    service_id=item_data.get("service_id"),
                    description=item_data["description"],
                    quantity=Decimal(str(item_data.get("quantity", "1.0"))),
                    unit_price=Decimal(str(item_data["unit_price"])),
                    total_price=Decimal(str(item_data["total_price"])),
                    taxable=item_data.get("taxable", True),
                )
                db.session.add(item)

                item_total = Decimal(str(item_data["total_price"]))
                subtotal += item_total
                if item_data.get("taxable", True):
                    tax_amount += item_total * (tax_rate / Decimal("100.0"))

            discount = Decimal(str(validated_data.get("discount_amount", invoice.discount_amount)))
            total = subtotal + tax_amount - discount

            invoice.subtotal = subtotal
            invoice.tax_rate = tax_rate
            invoice.tax_amount = tax_amount
            invoice.discount_amount = discount
            invoice.total_amount = total
            invoice.balance_due = total - invoice.amount_paid

        db.session.commit()

        # Return invoice with items
        invoice_dict = invoice.to_dict()
        invoice_dict["items"] = [item.to_dict() for item in invoice.items]

        app.logger.info(f"Updated invoice {invoice_id}")
        return jsonify(invoice_dict), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating invoice {invoice_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Invoice not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/invoices/<int:invoice_id>", methods=["DELETE"])
@login_required
def delete_invoice(invoice_id):
    """Delete an invoice"""
    try:
        from .models import Invoice

        invoice = Invoice.query.get_or_404(invoice_id)
        db.session.delete(invoice)
        db.session.commit()

        app.logger.info(f"Deleted invoice {invoice_id}")
        return jsonify({"message": "Invoice deleted"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting invoice {invoice_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Invoice not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# PAYMENT ENDPOINTS
# ============================================================================


@bp.route("/api/payments", methods=["GET"])
@login_required
def get_payments():
    """Get all payments with optional filtering"""
    try:
        from .models import Payment

        invoice_id = request.args.get("invoice_id", type=int)
        client_id = request.args.get("client_id", type=int)

        query = Payment.query

        if invoice_id:
            query = query.filter_by(invoice_id=invoice_id)

        if client_id:
            query = query.filter_by(client_id=client_id)

        payments = query.order_by(Payment.payment_date.desc()).all()
        return jsonify({"payments": [p.to_dict() for p in payments], "total": len(payments)}), 200

    except Exception as e:
        app.logger.error(f"Error fetching payments: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/payments/<int:payment_id>", methods=["GET"])
@login_required
def get_payment(payment_id):
    """Get a specific payment by ID"""
    try:
        from .models import Payment

        payment = Payment.query.get_or_404(payment_id)
        return jsonify(payment.to_dict()), 200

    except Exception as e:
        app.logger.error(f"Error fetching payment {payment_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Payment not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/payments", methods=["POST"])
@login_required
def create_payment():
    """Create a new payment and update invoice"""
    try:
        from .models import Payment, Invoice
        from .schemas import payment_schema
        from decimal import Decimal

        data = request.get_json()
        validated_data = payment_schema.load(data)

        # Verify invoice exists
        invoice = Invoice.query.get(validated_data["invoice_id"])
        if not invoice:
            return jsonify({"error": "Invoice not found"}), 404

        # Create payment
        payment = Payment(
            invoice_id=validated_data["invoice_id"],
            client_id=validated_data["client_id"],
            payment_date=validated_data["payment_date"],
            amount=Decimal(str(validated_data["amount"])),
            payment_method=validated_data["payment_method"],
            reference_number=validated_data.get("reference_number"),
            notes=validated_data.get("notes"),
            processed_by_id=current_user.id,
        )

        db.session.add(payment)

        # Update invoice amounts
        invoice.amount_paid += payment.amount
        invoice.balance_due = invoice.total_amount - invoice.amount_paid

        # Update invoice status
        if invoice.balance_due <= Decimal("0.0"):
            invoice.status = "paid"
        elif invoice.amount_paid > Decimal("0.0"):
            invoice.status = "partial_paid"

        db.session.commit()

        app.logger.info(f"Created payment {payment.id} for invoice {invoice.invoice_number}")
        return jsonify(payment.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating payment: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/payments/<int:payment_id>", methods=["DELETE"])
@login_required
def delete_payment(payment_id):
    """Delete a payment and update invoice"""
    try:
        from .models import Payment
        from decimal import Decimal

        payment = Payment.query.get_or_404(payment_id)
        invoice = payment.invoice

        # Update invoice amounts
        invoice.amount_paid -= payment.amount
        invoice.balance_due = invoice.total_amount - invoice.amount_paid

        # Update invoice status
        if invoice.amount_paid <= Decimal("0.0"):
            invoice.status = "sent"
        elif invoice.balance_due <= Decimal("0.0"):
            invoice.status = "paid"
        else:
            invoice.status = "partial_paid"

        db.session.delete(payment)
        db.session.commit()

        app.logger.info(f"Deleted payment {payment_id}")
        return jsonify({"message": "Payment deleted"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting payment {payment_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Payment not found"}), 404
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# FINANCIAL REPORTS
# ============================================================================


@bp.route("/api/reports/financial-summary", methods=["GET"])
@login_required
def get_financial_summary():
    """Get overall financial summary"""
    try:
        from .models import Invoice, Payment
        from sqlalchemy import func
        from decimal import Decimal

        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # Base query
        invoice_query = db.session.query(Invoice)
        payment_query = db.session.query(Payment)

        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            invoice_query = invoice_query.filter(Invoice.invoice_date >= start_dt)
            payment_query = payment_query.filter(Payment.payment_date >= start_dt)

        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            invoice_query = invoice_query.filter(Invoice.invoice_date <= end_dt)
            payment_query = payment_query.filter(Payment.payment_date <= end_dt)

        # Total revenue (paid invoices)
        total_revenue = invoice_query.filter(Invoice.status == "paid").with_entities(
            func.sum(Invoice.total_amount)
        ).scalar() or Decimal("0.0")

        # Total outstanding balance
        total_outstanding = invoice_query.filter(Invoice.status.in_(["sent", "partial_paid", "overdue"])).with_entities(
            func.sum(Invoice.balance_due)
        ).scalar() or Decimal("0.0")

        # Total invoices issued
        total_invoices = invoice_query.count()

        # Paid invoices count
        paid_invoices = invoice_query.filter(Invoice.status == "paid").count()

        # Total payments received
        total_payments = payment_query.with_entities(func.sum(Payment.amount)).scalar() or Decimal("0.0")

        # Average invoice amount
        avg_invoice = invoice_query.with_entities(func.avg(Invoice.total_amount)).scalar() or Decimal("0.0")

        return (
            jsonify(
                {
                    "total_revenue": float(total_revenue),
                    "total_outstanding": float(total_outstanding),
                    "total_invoices": total_invoices,
                    "paid_invoices": paid_invoices,
                    "total_payments": float(total_payments),
                    "avg_invoice": float(avg_invoice),
                    "start_date": start_date,
                    "end_date": end_date,
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Error getting financial summary: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/reports/revenue-by-period", methods=["GET"])
@login_required
def get_revenue_by_period():
    """Get revenue grouped by period (daily, weekly, monthly)"""
    try:
        from .models import Invoice
        from sqlalchemy import func

        period = request.args.get("period", "monthly")  # daily, weekly, monthly
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        query = db.session.query(Invoice).filter(Invoice.status == "paid")

        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Invoice.invoice_date >= start_dt)

        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Invoice.invoice_date <= end_dt)

        if period == "daily":
            results = (
                query.with_entities(
                    func.date(Invoice.invoice_date).label("period"),
                    func.sum(Invoice.total_amount).label("revenue"),
                    func.count(Invoice.id).label("count"),
                )
                .group_by(func.date(Invoice.invoice_date))
                .order_by(func.date(Invoice.invoice_date))
                .all()
            )
        elif period == "monthly":
            results = (
                query.with_entities(
                    func.strftime("%Y-%m", Invoice.invoice_date).label("period"),
                    func.sum(Invoice.total_amount).label("revenue"),
                    func.count(Invoice.id).label("count"),
                )
                .group_by(func.strftime("%Y-%m", Invoice.invoice_date))
                .order_by(func.strftime("%Y-%m", Invoice.invoice_date))
                .all()
            )
        else:  # weekly
            results = (
                query.with_entities(
                    func.strftime("%Y-W%W", Invoice.invoice_date).label("period"),
                    func.sum(Invoice.total_amount).label("revenue"),
                    func.count(Invoice.id).label("count"),
                )
                .group_by(func.strftime("%Y-W%W", Invoice.invoice_date))
                .order_by(func.strftime("%Y-W%W", Invoice.invoice_date))
                .all()
            )

        data = [{"period": str(row.period), "revenue": float(row.revenue or 0), "count": row.count} for row in results]

        return jsonify({"period": period, "data": data}), 200

    except Exception as e:
        app.logger.error(f"Error getting revenue by period: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/reports/outstanding-balance", methods=["GET"])
@login_required
def get_outstanding_balance_report():
    """Get detailed outstanding balance report by client"""
    try:
        from .models import Invoice
        from sqlalchemy import func

        # Get all invoices with outstanding balance
        results = (
            db.session.query(
                Invoice.client_id,
                Client.name.label("client_name"),
                func.count(Invoice.id).label("invoice_count"),
                func.sum(Invoice.balance_due).label("total_outstanding"),
                func.min(Invoice.invoice_date).label("oldest_invoice_date"),
            )
            .join(Client, Invoice.client_id == Client.id)
            .filter(Invoice.status.in_(["sent", "partial_paid", "overdue"]))
            .filter(Invoice.balance_due > 0)
            .group_by(Invoice.client_id, Client.name)
            .order_by(func.sum(Invoice.balance_due).desc())
            .all()
        )

        data = [
            {
                "client_id": row.client_id,
                "client_name": row.client_name,
                "invoice_count": row.invoice_count,
                "total_outstanding": float(row.total_outstanding or 0),
                "oldest_invoice_date": row.oldest_invoice_date.isoformat() if row.oldest_invoice_date else None,
            }
            for row in results
        ]

        return jsonify({"data": data}), 200

    except Exception as e:
        app.logger.error(f"Error getting outstanding balance report: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/reports/payment-methods", methods=["GET"])
@login_required
def get_payment_method_breakdown():
    """Get payment breakdown by payment method"""
    try:
        from .models import Payment
        from sqlalchemy import func

        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        query = db.session.query(
            Payment.payment_method, func.sum(Payment.amount).label("total"), func.count(Payment.id).label("count")
        )

        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Payment.payment_date >= start_dt)

        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Payment.payment_date <= end_dt)

        results = query.group_by(Payment.payment_method).order_by(func.sum(Payment.amount).desc()).all()

        data = [
            {"payment_method": row.payment_method, "total": float(row.total or 0), "count": row.count}
            for row in results
        ]

        return jsonify({"data": data}), 200

    except Exception as e:
        app.logger.error(f"Error getting payment method breakdown: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/reports/service-revenue", methods=["GET"])
@login_required
def get_service_revenue_report():
    """Get revenue breakdown by service/product"""
    try:
        from .models import InvoiceItem, Service, Invoice
        from sqlalchemy import func

        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        query = (
            db.session.query(
                InvoiceItem.service_id,
                Service.name.label("service_name"),
                Service.service_type,
                func.sum(InvoiceItem.quantity).label("total_quantity"),
                func.sum(InvoiceItem.total_price).label("total_revenue"),
                func.count(InvoiceItem.id).label("times_sold"),
            )
            .join(Service, InvoiceItem.service_id == Service.id)
            .join(Invoice, InvoiceItem.invoice_id == Invoice.id)
        )

        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Invoice.invoice_date >= start_dt)

        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Invoice.invoice_date <= end_dt)

        results = (
            query.group_by(InvoiceItem.service_id, Service.name, Service.service_type)
            .order_by(func.sum(InvoiceItem.total_price).desc())
            .all()
        )

        data = [
            {
                "service_id": row.service_id,
                "service_name": row.service_name,
                "service_type": row.service_type,
                "total_quantity": float(row.total_quantity or 0),
                "total_revenue": float(row.total_revenue or 0),
                "times_sold": row.times_sold,
            }
            for row in results
        ]

        return jsonify({"data": data}), 200

    except Exception as e:
        app.logger.error(f"Error getting service revenue report: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400



# ============================================================================
# INVENTORY MANAGEMENT - Phase 3.1
# ============================================================================

# ------------------ VENDOR ENDPOINTS ------------------

@bp.route("/api/vendors", methods=["GET"])
@login_required
def get_vendors():
    """Get list of all vendors with optional filtering"""
    try:
        query = Vendor.query
        
        # Filter by active status
        is_active = request.args.get("is_active")
        if is_active is not None:
            query = query.filter(Vendor.is_active == (is_active.lower() == "true"))
        
        # Filter by preferred
        preferred = request.args.get("preferred")
        if preferred is not None:
            query = query.filter(Vendor.preferred_vendor == (preferred.lower() == "true"))
        
        # Search by company name
        search = request.args.get("search")
        if search:
            query = query.filter(Vendor.company_name.ilike(f"%{search}%"))
        
        vendors = query.order_by(Vendor.company_name).all()
        return jsonify({"vendors": [v.to_dict() for v in vendors], "total": len(vendors)}), 200
    
    except Exception as e:
        app.logger.error(f"Error getting vendors: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/vendors/<int:vendor_id>", methods=["GET"])
@login_required
def get_vendor(vendor_id):
    """Get single vendor by ID"""
    vendor = Vendor.query.get(vendor_id)
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404
    
    return jsonify(vendor.to_dict()), 200


@bp.route("/api/vendors", methods=["POST"])
@login_required
def create_vendor():
    """Create new vendor"""
    try:
        data = request.get_json()
        validated_data = vendor_schema.load(data)
        
        vendor = Vendor(**validated_data)
        db.session.add(vendor)
        db.session.commit()
        
        return jsonify(vendor.to_dict()), 201
    
    except MarshmallowValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating vendor: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/vendors/<int:vendor_id>", methods=["PUT"])
@login_required
def update_vendor(vendor_id):
    """Update vendor"""
    vendor = Vendor.query.get(vendor_id)
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404
    
    try:
        data = request.get_json()
        validated_data = vendor_schema.load(data, partial=True)
        
        for key, value in validated_data.items():
            setattr(vendor, key, value)
        
        db.session.commit()
        return jsonify(vendor.to_dict()), 200
    
    except MarshmallowValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating vendor: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/vendors/<int:vendor_id>", methods=["DELETE"])
@admin_required
def delete_vendor(vendor_id):
    """Delete vendor (soft delete by default, hard delete with ?hard=true)"""
    vendor = Vendor.query.get(vendor_id)
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404
    
    try:
        hard_delete = request.args.get("hard", "false").lower() == "true"
        
        if hard_delete:
            db.session.delete(vendor)
        else:
            vendor.is_active = False
        
        db.session.commit()
        return jsonify({"message": "Vendor deleted successfully"}), 200
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting vendor: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


# ------------------ PRODUCT ENDPOINTS ------------------

@bp.route("/api/products", methods=["GET"])
@login_required
def get_products():
    """Get list of all products with optional filtering"""
    try:
        query = Product.query
        
        # Filter by active status
        is_active = request.args.get("is_active")
        if is_active is not None:
            query = query.filter(Product.is_active == (is_active.lower() == "true"))
        
        # Filter by product type
        product_type = request.args.get("product_type")
        if product_type:
            query = query.filter(Product.product_type == product_type)
        
        # Filter by category
        category = request.args.get("category")
        if category:
            query = query.filter(Product.category == category)
        
        # Filter by vendor
        vendor_id = request.args.get("vendor_id")
        if vendor_id:
            query = query.filter(Product.vendor_id == int(vendor_id))
        
        # Filter by low stock
        low_stock = request.args.get("low_stock")
        if low_stock and low_stock.lower() == "true":
            query = query.filter(Product.stock_quantity <= Product.reorder_level)
        
        # Search by name or SKU
        search = request.args.get("search")
        if search:
            query = query.filter(
                db.or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.sku.ilike(f"%{search}%")
                )
            )
        
        products = query.order_by(Product.name).all()
        return jsonify({"products": [p.to_dict() for p in products], "total": len(products)}), 200
    
    except Exception as e:
        app.logger.error(f"Error getting products: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/products/low-stock", methods=["GET"])
@login_required
def get_low_stock_products():
    """Get products that need reordering"""
    try:
        products = Product.query.filter(
            Product.is_active == True,
            Product.stock_quantity <= Product.reorder_level
        ).order_by(Product.stock_quantity).all()
        
        return jsonify({
            "products": [p.to_dict() for p in products],
            "total": len(products)
        }), 200
    
    except Exception as e:
        app.logger.error(f"Error getting low stock products: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/products/<int:product_id>", methods=["GET"])
@login_required
def get_product(product_id):
    """Get single product by ID"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    return jsonify(product.to_dict()), 200


@bp.route("/api/products", methods=["POST"])
@login_required
def create_product():
    """Create new product"""
    try:
        data = request.get_json()
        validated_data = product_schema.load(data)
        
        product = Product(**validated_data)
        db.session.add(product)
        db.session.commit()
        
        return jsonify(product.to_dict()), 201
    
    except MarshmallowValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating product: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/products/<int:product_id>", methods=["PUT"])
@login_required
def update_product(product_id):
    """Update product"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    try:
        data = request.get_json()
        validated_data = product_schema.load(data, partial=True)
        
        for key, value in validated_data.items():
            setattr(product, key, value)
        
        db.session.commit()
        return jsonify(product.to_dict()), 200
    
    except MarshmallowValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating product: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/products/<int:product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id):
    """Delete product (soft delete by default)"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    try:
        hard_delete = request.args.get("hard", "false").lower() == "true"
        
        if hard_delete:
            db.session.delete(product)
        else:
            product.is_active = False
        
        db.session.commit()
        return jsonify({"message": "Product deleted successfully"}), 200
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting product: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


# ------------------ PURCHASE ORDER ENDPOINTS ------------------

@bp.route("/api/purchase-orders", methods=["GET"])
@login_required
def get_purchase_orders():
    """Get list of all purchase orders with optional filtering"""
    try:
        query = PurchaseOrder.query
        
        # Filter by status
        status = request.args.get("status")
        if status:
            query = query.filter(PurchaseOrder.status == status)
        
        # Filter by vendor
        vendor_id = request.args.get("vendor_id")
        if vendor_id:
            query = query.filter(PurchaseOrder.vendor_id == int(vendor_id))
        
        # Search by PO number
        search = request.args.get("search")
        if search:
            query = query.filter(PurchaseOrder.po_number.ilike(f"%{search}%"))
        
        pos = query.order_by(PurchaseOrder.order_date.desc()).all()
        return jsonify({"purchase_orders": [po.to_dict() for po in pos], "total": len(pos)}), 200
    
    except Exception as e:
        app.logger.error(f"Error getting purchase orders: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/purchase-orders/<int:po_id>", methods=["GET"])
@login_required
def get_purchase_order(po_id):
    """Get single purchase order by ID"""
    po = PurchaseOrder.query.get(po_id)
    if not po:
        return jsonify({"error": "Purchase order not found"}), 404
    
    return jsonify(po.to_dict()), 200


@bp.route("/api/purchase-orders", methods=["POST"])
@login_required
def create_purchase_order():
    """Create new purchase order"""
    try:
        data = request.get_json()
        validated_data = purchase_order_schema.load(data)
        
        # Generate PO number
        from datetime import datetime
        today = datetime.utcnow().strftime("%Y%m%d")
        count = PurchaseOrder.query.filter(PurchaseOrder.po_number.like(f"PO-{today}%")).count()
        po_number = f"PO-{today}-{count + 1:04d}"
        validated_data["po_number"] = po_number
        validated_data["created_by_id"] = current_user.id
        
        po = PurchaseOrder(**validated_data)
        db.session.add(po)
        db.session.commit()
        
        return jsonify(po.to_dict()), 201
    
    except MarshmallowValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating purchase order: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/purchase-orders/<int:po_id>", methods=["PUT"])
@login_required
def update_purchase_order(po_id):
    """Update purchase order"""
    po = PurchaseOrder.query.get(po_id)
    if not po:
        return jsonify({"error": "Purchase order not found"}), 404
    
    try:
        data = request.get_json()
        validated_data = purchase_order_schema.load(data, partial=True)
        
        for key, value in validated_data.items():
            if key != "po_number":  # Don't allow PO number changes
                setattr(po, key, value)
        
        db.session.commit()
        return jsonify(po.to_dict()), 200
    
    except MarshmallowValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating purchase order: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/purchase-orders/<int:po_id>/receive", methods=["POST"])
@login_required
def receive_purchase_order(po_id):
    """Mark purchase order as received and update inventory"""
    po = PurchaseOrder.query.get(po_id)
    if not po:
        return jsonify({"error": "Purchase order not found"}), 404
    
    if po.status == "received":
        return jsonify({"error": "Purchase order already received"}), 400
    
    try:
        from datetime import datetime
        
        # Mark PO as received
        po.status = "received"
        po.actual_delivery_date = datetime.utcnow().date()
        po.received_by_id = current_user.id
        
        # Update inventory for each item
        for item in po.items:
            product = Product.query.get(item.product_id)
            if product:
                quantity_before = product.stock_quantity
                product.stock_quantity += item.quantity_received
                quantity_after = product.stock_quantity
                
                # Create inventory transaction
                transaction = InventoryTransaction(
                    product_id=product.id,
                    purchase_order_id=po.id,
                    transaction_type="received",
                    quantity=item.quantity_received,
                    quantity_before=quantity_before,
                    quantity_after=quantity_after,
                    reason=f"Received from PO {po.po_number}",
                    reference_number=po.po_number,
                    performed_by_id=current_user.id
                )
                db.session.add(transaction)
        
        db.session.commit()
        return jsonify(po.to_dict()), 200
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error receiving purchase order: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/purchase-orders/<int:po_id>", methods=["DELETE"])
@admin_required
def delete_purchase_order(po_id):
    """Delete purchase order (only if status is draft)"""
    po = PurchaseOrder.query.get(po_id)
    if not po:
        return jsonify({"error": "Purchase order not found"}), 404
    
    if po.status != "draft":
        return jsonify({"error": "Can only delete draft purchase orders"}), 400
    
    try:
        db.session.delete(po)
        db.session.commit()
        return jsonify({"message": "Purchase order deleted successfully"}), 200
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting purchase order: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


# ------------------ INVENTORY TRANSACTION ENDPOINTS ------------------

@bp.route("/api/inventory-transactions", methods=["GET"])
@login_required
def get_inventory_transactions():
    """Get inventory transaction history with optional filtering"""
    try:
        query = InventoryTransaction.query
        
        # Filter by product
        product_id = request.args.get("product_id")
        if product_id:
            query = query.filter(InventoryTransaction.product_id == int(product_id))
        
        # Filter by transaction type
        transaction_type = request.args.get("transaction_type")
        if transaction_type:
            query = query.filter(InventoryTransaction.transaction_type == transaction_type)
        
        # Filter by date range
        start_date = request.args.get("start_date")
        if start_date:
            query = query.filter(InventoryTransaction.transaction_date >= start_date)
        
        end_date = request.args.get("end_date")
        if end_date:
            query = query.filter(InventoryTransaction.transaction_date <= end_date)
        
        transactions = query.order_by(InventoryTransaction.transaction_date.desc()).limit(100).all()
        return jsonify({
            "transactions": [t.to_dict() for t in transactions],
            "total": len(transactions)
        }), 200
    
    except Exception as e:
        app.logger.error(f"Error getting inventory transactions: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/inventory-transactions", methods=["POST"])
@login_required
def create_inventory_transaction():
    """Create manual inventory transaction (adjustment, damaged, expired, etc.)"""
    try:
        data = request.get_json()
        
        # Get product
        product_id = data.get("product_id")
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        # Prepare transaction data
        quantity_before = product.stock_quantity
        quantity = data.get("quantity", 0)
        quantity_after = quantity_before + quantity
        
        # Validate transaction
        validated_data = inventory_transaction_schema.load({
            **data,
            "quantity_before": quantity_before,
            "quantity_after": quantity_after,
            "performed_by_id": current_user.id
        })
        
        # Create transaction
        transaction = InventoryTransaction(**validated_data)
        
        # Update product stock
        product.stock_quantity = quantity_after
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify(transaction.to_dict()), 201
    
    except MarshmallowValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating inventory transaction: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/inventory-transactions/<int:transaction_id>", methods=["GET"])
@login_required
def get_inventory_transaction(transaction_id):
    """Get single inventory transaction by ID"""
    transaction = InventoryTransaction.query.get(transaction_id)
    if not transaction:
        return jsonify({"error": "Inventory transaction not found"}), 404
    
    return jsonify(transaction.to_dict()), 200


# ============================================================================
# STAFF MANAGEMENT API ENDPOINTS
# ============================================================================


@bp.route("/api/staff", methods=["GET"])
@login_required
def get_all_staff():
    """Get all staff members with optional filtering"""
    from .models import Staff

    # Get query parameters
    is_active = request.args.get("is_active")
    position = request.args.get("position")
    department = request.args.get("department")
    search = request.args.get("search")

    # Build query
    query = Staff.query

    # Apply filters
    if is_active is not None:
        is_active_bool = is_active.lower() == "true"
        query = query.filter(Staff.is_active == is_active_bool)

    if position:
        query = query.filter(Staff.position.ilike(f"%{position}%"))

    if department:
        query = query.filter(Staff.department.ilike(f"%{department}%"))

    if search:
        search_filter = db.or_(
            Staff.first_name.ilike(f"%{search}%"),
            Staff.last_name.ilike(f"%{search}%"),
            Staff.email.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    # Order by name
    staff_members = query.order_by(Staff.last_name, Staff.first_name).all()

    return jsonify({"staff": [s.to_dict() for s in staff_members]}), 200


@bp.route("/api/staff/<int:staff_id>", methods=["GET"])
@login_required
def get_staff(staff_id):
    """Get single staff member by ID"""
    from .models import Staff

    staff = Staff.query.get(staff_id)
    if not staff:
        return jsonify({"error": "Staff member not found"}), 404

    return jsonify(staff.to_dict()), 200


@bp.route("/api/staff", methods=["POST"])
@login_required
@admin_required
def create_staff():
    """Create new staff member (admin only)"""
    from .models import Staff
    from .schemas import staff_schema

    try:
        # Validate request data
        data = staff_schema.load(request.json)

        # Check for duplicate email
        existing_staff = Staff.query.filter_by(email=data["email"]).first()
        if existing_staff:
            return jsonify({"error": "Staff member with this email already exists"}), 400

        # Create new staff member
        staff = Staff(**data)
        db.session.add(staff)
        db.session.commit()

        app.logger.info(f"Created staff member: {staff.first_name} {staff.last_name}")
        return jsonify(staff.to_dict()), 201

    except MarshmallowValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating staff member: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/staff/<int:staff_id>", methods=["PUT"])
@login_required
@admin_required
def update_staff(staff_id):
    """Update existing staff member (admin only)"""
    from .models import Staff
    from .schemas import staff_schema

    staff = Staff.query.get(staff_id)
    if not staff:
        return jsonify({"error": "Staff member not found"}), 404

    try:
        # Validate request data
        data = staff_schema.load(request.json, partial=True)

        # Check for duplicate email (if email is being changed)
        if "email" in data and data["email"] != staff.email:
            existing_staff = Staff.query.filter_by(email=data["email"]).first()
            if existing_staff:
                return jsonify({"error": "Staff member with this email already exists"}), 400

        # Update staff member fields
        for key, value in data.items():
            setattr(staff, key, value)

        db.session.commit()

        app.logger.info(f"Updated staff member: {staff.first_name} {staff.last_name}")
        return jsonify(staff.to_dict()), 200

    except MarshmallowValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating staff member: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/staff/<int:staff_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_staff(staff_id):
    """Delete staff member (admin only) - soft delete by default"""
    from .models import Staff

    staff = Staff.query.get(staff_id)
    if not staff:
        return jsonify({"error": "Staff member not found"}), 404

    try:
        # Check if hard delete is requested
        hard_delete = request.args.get("hard", "false").lower() == "true"

        if hard_delete:
            # Hard delete - remove from database
            db.session.delete(staff)
            db.session.commit()
            app.logger.info(f"Hard deleted staff member: {staff.first_name} {staff.last_name}")
            return jsonify({"message": "Staff member permanently deleted"}), 200
        else:
            # Soft delete - mark as inactive
            staff.is_active = False
            db.session.commit()
            app.logger.info(f"Soft deleted staff member: {staff.first_name} {staff.last_name}")
            return jsonify({"message": "Staff member deactivated"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting staff member: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


# ============================================================================
# SCHEDULE MANAGEMENT API ENDPOINTS
# ============================================================================


@bp.route("/api/schedules", methods=["GET"])
@login_required
def get_all_schedules():
    """Get all schedules with optional filtering"""
    from .models import Schedule

    # Get query parameters
    staff_id = request.args.get("staff_id", type=int)
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    shift_type = request.args.get("shift_type")
    status = request.args.get("status")
    is_time_off = request.args.get("is_time_off")

    # Build query
    query = Schedule.query

    # Apply filters
    if staff_id:
        query = query.filter(Schedule.staff_id == staff_id)

    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(Schedule.shift_date >= start)
        except ValueError:
            return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(Schedule.shift_date <= end)
        except ValueError:
            return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}), 400

    if shift_type:
        query = query.filter(Schedule.shift_type == shift_type)

    if status:
        query = query.filter(Schedule.status == status)

    if is_time_off is not None:
        is_time_off_bool = is_time_off.lower() == "true"
        query = query.filter(Schedule.is_time_off == is_time_off_bool)

    # Order by date and start time
    schedules = query.order_by(Schedule.shift_date, Schedule.start_time).all()

    return jsonify({"schedules": [s.to_dict() for s in schedules]}), 200


@bp.route("/api/schedules/<int:schedule_id>", methods=["GET"])
@login_required
def get_schedule(schedule_id):
    """Get single schedule by ID"""
    from .models import Schedule

    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({"error": "Schedule not found"}), 404

    return jsonify(schedule.to_dict()), 200


@bp.route("/api/schedules", methods=["POST"])
@login_required
@admin_required
def create_schedule():
    """Create new schedule/shift (admin only)"""
    from .models import Schedule, Staff
    from .schemas import schedule_schema

    try:
        # Validate request data
        data = schedule_schema.load(request.json)

        # Verify staff member exists
        staff = Staff.query.get(data["staff_id"])
        if not staff:
            return jsonify({"error": "Staff member not found"}), 404

        # Validate end time is after start time
        if data["end_time"] <= data["start_time"]:
            return jsonify({"error": "End time must be after start time"}), 400

        # Create new schedule
        schedule = Schedule(**data)
        db.session.add(schedule)
        db.session.commit()

        app.logger.info(f"Created schedule for {staff.first_name} {staff.last_name} on {schedule.shift_date}")
        return jsonify(schedule.to_dict()), 201

    except MarshmallowValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating schedule: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/schedules/<int:schedule_id>", methods=["PUT"])
@login_required
@admin_required
def update_schedule(schedule_id):
    """Update existing schedule (admin only)"""
    from .models import Schedule
    from .schemas import schedule_schema

    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({"error": "Schedule not found"}), 404

    try:
        # Validate request data
        data = schedule_schema.load(request.json, partial=True)

        # If updating times, validate end time is after start time
        start_time = data.get("start_time", schedule.start_time)
        end_time = data.get("end_time", schedule.end_time)
        if end_time <= start_time:
            return jsonify({"error": "End time must be after start time"}), 400

        # Update schedule fields
        for key, value in data.items():
            setattr(schedule, key, value)

        db.session.commit()

        app.logger.info(f"Updated schedule ID {schedule_id}")
        return jsonify(schedule.to_dict()), 200

    except MarshmallowValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating schedule: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/schedules/<int:schedule_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_schedule(schedule_id):
    """Delete schedule (admin only)"""
    from .models import Schedule

    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({"error": "Schedule not found"}), 404

    try:
        db.session.delete(schedule)
        db.session.commit()

        app.logger.info(f"Deleted schedule ID {schedule_id}")
        return jsonify({"message": "Schedule deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting schedule: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/schedules/<int:schedule_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_time_off(schedule_id):
    """Approve time-off request (admin only)"""
    from .models import Schedule

    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({"error": "Schedule not found"}), 404

    if not schedule.is_time_off:
        return jsonify({"error": "This is not a time-off request"}), 400

    try:
        schedule.time_off_approved = True
        schedule.approved_by_id = current_user.id
        db.session.commit()

        app.logger.info(f"Approved time-off request ID {schedule_id}")
        return jsonify(schedule.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error approving time-off: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


# ============================================================================
# LABORATORY MANAGEMENT API ENDPOINTS
# ============================================================================

@bp.route("/api/lab-tests", methods=["GET"])
@login_required
def get_all_lab_tests():
    """Get all lab tests with optional filtering"""
    from .models import LabTest

    # Get query parameters
    is_active = request.args.get("is_active")
    category = request.args.get("category")
    external_lab = request.args.get("external_lab")
    search = request.args.get("search")

    # Build query with filters
    query = LabTest.query

    if is_active is not None:
        is_active_bool = is_active.lower() == "true"
        query = query.filter(LabTest.is_active == is_active_bool)

    if category:
        query = query.filter(LabTest.category == category)

    if external_lab is not None:
        external_lab_bool = external_lab.lower() == "true"
        query = query.filter(LabTest.external_lab == external_lab_bool)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                LabTest.test_name.ilike(search_term),
                LabTest.test_code.ilike(search_term),
                LabTest.description.ilike(search_term)
            )
        )

    lab_tests = query.order_by(LabTest.category, LabTest.test_name).all()

    return jsonify({"lab_tests": [test.to_dict() for test in lab_tests]}), 200


@bp.route("/api/lab-tests/<int:test_id>", methods=["GET"])
@login_required
def get_lab_test(test_id):
    """Get a specific lab test by ID"""
    from .models import LabTest

    lab_test = LabTest.query.get(test_id)
    if not lab_test:
        return jsonify({"error": "Lab test not found"}), 404

    return jsonify(lab_test.to_dict()), 200


@bp.route("/api/lab-tests", methods=["POST"])
@admin_required
def create_lab_test():
    """Create a new lab test (Admin only)"""
    from .models import LabTest
    from .schemas import LabTestSchema

    schema = LabTestSchema()
    try:
        data = schema.load(request.json)

        # Check for duplicate test code
        existing = LabTest.query.filter_by(test_code=data["test_code"]).first()
        if existing:
            return jsonify({"error": "Test code already exists"}), 400

        lab_test = LabTest(**data)
        db.session.add(lab_test)
        db.session.commit()

        app.logger.info(f"Lab test created: {lab_test.test_code} by user {current_user.username}")
        return jsonify(lab_test.to_dict()), 201

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating lab test: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/lab-tests/<int:test_id>", methods=["PUT"])
@admin_required
def update_lab_test(test_id):
    """Update a lab test (Admin only)"""
    from .models import LabTest
    from .schemas import LabTestSchema

    lab_test = LabTest.query.get(test_id)
    if not lab_test:
        return jsonify({"error": "Lab test not found"}), 404

    schema = LabTestSchema(partial=True)
    try:
        data = schema.load(request.json)

        # Check for duplicate test code if updating
        if "test_code" in data and data["test_code"] != lab_test.test_code:
            existing = LabTest.query.filter_by(test_code=data["test_code"]).first()
            if existing:
                return jsonify({"error": "Test code already exists"}), 400

        for key, value in data.items():
            setattr(lab_test, key, value)

        db.session.commit()

        app.logger.info(f"Lab test updated: {lab_test.test_code} by user {current_user.username}")
        return jsonify(lab_test.to_dict()), 200

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating lab test: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/lab-tests/<int:test_id>", methods=["DELETE"])
@admin_required
def delete_lab_test(test_id):
    """Soft delete a lab test (Admin only)"""
    from .models import LabTest

    lab_test = LabTest.query.get(test_id)
    if not lab_test:
        return jsonify({"error": "Lab test not found"}), 404

    try:
        lab_test.is_active = False
        db.session.commit()

        app.logger.info(f"Lab test deleted: {lab_test.test_code} by user {current_user.username}")
        return jsonify({"message": "Lab test deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting lab test: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


# ============================================================================
# LAB RESULTS API ENDPOINTS
# ============================================================================

@bp.route("/api/lab-results", methods=["GET"])
@login_required
def get_all_lab_results():
    """Get all lab results with optional filtering"""
    from .models import LabResult

    # Get query parameters
    patient_id = request.args.get("patient_id", type=int)
    visit_id = request.args.get("visit_id", type=int)
    test_id = request.args.get("test_id", type=int)
    status = request.args.get("status")
    is_abnormal = request.args.get("is_abnormal")
    reviewed = request.args.get("reviewed")

    # Build query with filters
    query = LabResult.query

    if patient_id:
        query = query.filter(LabResult.patient_id == patient_id)

    if visit_id:
        query = query.filter(LabResult.visit_id == visit_id)

    if test_id:
        query = query.filter(LabResult.test_id == test_id)

    if status:
        query = query.filter(LabResult.status == status)

    if is_abnormal is not None:
        is_abnormal_bool = is_abnormal.lower() == "true"
        query = query.filter(LabResult.is_abnormal == is_abnormal_bool)

    if reviewed is not None:
        reviewed_bool = reviewed.lower() == "true"
        query = query.filter(LabResult.reviewed == reviewed_bool)

    lab_results = query.order_by(LabResult.collection_date.desc()).all()

    return jsonify({"lab_results": [result.to_dict() for result in lab_results]}), 200


@bp.route("/api/lab-results/pending", methods=["GET"])
@login_required
def get_pending_lab_results():
    """Get all pending lab results"""
    from .models import LabResult

    pending_results = LabResult.query.filter_by(status="pending").order_by(LabResult.collection_date).all()

    return jsonify({"lab_results": [result.to_dict() for result in pending_results]}), 200


@bp.route("/api/lab-results/abnormal", methods=["GET"])
@login_required
def get_abnormal_lab_results():
    """Get all abnormal/flagged lab results"""
    from .models import LabResult

    # Get query parameters for filtering
    reviewed = request.args.get("reviewed")

    query = LabResult.query.filter(LabResult.is_abnormal == True)

    if reviewed is not None:
        reviewed_bool = reviewed.lower() == "true"
        query = query.filter(LabResult.reviewed == reviewed_bool)

    abnormal_results = query.order_by(LabResult.result_date.desc()).all()

    return jsonify({"lab_results": [result.to_dict() for result in abnormal_results]}), 200


@bp.route("/api/lab-results/<int:result_id>", methods=["GET"])
@login_required
def get_lab_result(result_id):
    """Get a specific lab result by ID"""
    from .models import LabResult

    lab_result = LabResult.query.get(result_id)
    if not lab_result:
        return jsonify({"error": "Lab result not found"}), 404

    return jsonify(lab_result.to_dict()), 200


@bp.route("/api/lab-results", methods=["POST"])
@login_required
def create_lab_result():
    """Create a new lab result"""
    from .models import LabResult, Patient, LabTest
    from .schemas import LabResultSchema

    schema = LabResultSchema()
    try:
        data = schema.load(request.json)

        # Verify patient exists
        patient = Patient.query.get(data["patient_id"])
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Verify lab test exists
        lab_test = LabTest.query.get(data["test_id"])
        if not lab_test:
            return jsonify({"error": "Lab test not found"}), 404

        lab_result = LabResult(**data)
        lab_result.ordered_by_id = current_user.id

        db.session.add(lab_result)
        db.session.commit()

        app.logger.info(f"Lab result created for patient {patient.name} by user {current_user.username}")
        return jsonify(lab_result.to_dict()), 201

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating lab result: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/lab-results/<int:result_id>", methods=["PUT"])
@login_required
def update_lab_result(result_id):
    """Update a lab result"""
    from .models import LabResult
    from .schemas import LabResultSchema

    lab_result = LabResult.query.get(result_id)
    if not lab_result:
        return jsonify({"error": "Lab result not found"}), 404

    schema = LabResultSchema(partial=True)
    try:
        data = schema.load(request.json)

        for key, value in data.items():
            setattr(lab_result, key, value)

        db.session.commit()

        app.logger.info(f"Lab result {result_id} updated by user {current_user.username}")
        return jsonify(lab_result.to_dict()), 200

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating lab result: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/lab-results/<int:result_id>/review", methods=["POST"])
@login_required
def review_lab_result(result_id):
    """Mark a lab result as reviewed"""
    from .models import LabResult

    lab_result = LabResult.query.get(result_id)
    if not lab_result:
        return jsonify({"error": "Lab result not found"}), 404

    try:
        lab_result.reviewed = True
        lab_result.reviewed_by_id = current_user.id
        lab_result.reviewed_date = datetime.now()

        db.session.commit()

        app.logger.info(f"Lab result {result_id} reviewed by user {current_user.username}")
        return jsonify(lab_result.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error reviewing lab result: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/lab-results/<int:result_id>", methods=["DELETE"])
@admin_required
def delete_lab_result(result_id):
    """Delete a lab result (Admin only)"""
    from .models import LabResult

    lab_result = LabResult.query.get(result_id)
    if not lab_result:
        return jsonify({"error": "Lab result not found"}), 404

    try:
        db.session.delete(lab_result)
        db.session.commit()

        app.logger.info(f"Lab result {result_id} deleted by user {current_user.username}")
        return jsonify({"message": "Lab result deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting lab result: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


# ============================================================================
# NOTIFICATION TEMPLATE API ENDPOINTS
# ============================================================================

@bp.route("/api/notification-templates", methods=["GET"])
@login_required
def get_all_notification_templates():
    """Get all notification templates with optional filtering"""
    from .models import NotificationTemplate

    # Get query parameters
    template_type = request.args.get("template_type")
    channel = request.args.get("channel")
    is_active = request.args.get("is_active")

    # Build query with filters
    query = NotificationTemplate.query

    if template_type:
        query = query.filter(NotificationTemplate.template_type == template_type)

    if channel:
        query = query.filter(NotificationTemplate.channel == channel)

    if is_active is not None:
        is_active_bool = is_active.lower() == "true"
        query = query.filter(NotificationTemplate.is_active == is_active_bool)

    templates = query.order_by(NotificationTemplate.template_type, NotificationTemplate.name).all()

    return jsonify({"templates": [t.to_dict() for t in templates]}), 200


@bp.route("/api/notification-templates/<int:template_id>", methods=["GET"])
@login_required
def get_notification_template(template_id):
    """Get a specific notification template by ID"""
    from .models import NotificationTemplate

    template = NotificationTemplate.query.get(template_id)
    if not template:
        return jsonify({"error": "Notification template not found"}), 404

    return jsonify(template.to_dict()), 200


@bp.route("/api/notification-templates", methods=["POST"])
@admin_required
def create_notification_template():
    """Create a new notification template (Admin only)"""
    from .models import NotificationTemplate
    from .schemas import NotificationTemplateSchema
    import json

    schema = NotificationTemplateSchema()
    try:
        data = schema.load(request.json)

        # Check for duplicate name
        existing = NotificationTemplate.query.filter_by(name=data["name"]).first()
        if existing:
            return jsonify({"error": "Template name already exists"}), 400

        # Convert variables list to JSON string for storage
        if "variables" in data and data["variables"]:
            data["variables"] = json.dumps(data["variables"])

        template = NotificationTemplate(**data)
        template.created_by_id = current_user.id

        db.session.add(template)
        db.session.commit()

        app.logger.info(f"Notification template created: {template.name} by user {current_user.username}")
        return jsonify(template.to_dict()), 201

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating notification template: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/notification-templates/<int:template_id>", methods=["PUT"])
@admin_required
def update_notification_template(template_id):
    """Update a notification template (Admin only)"""
    from .models import NotificationTemplate
    from .schemas import NotificationTemplateSchema
    import json

    template = NotificationTemplate.query.get(template_id)
    if not template:
        return jsonify({"error": "Notification template not found"}), 404

    schema = NotificationTemplateSchema(partial=True)
    try:
        data = schema.load(request.json)

        # Check for duplicate name if updating
        if "name" in data and data["name"] != template.name:
            existing = NotificationTemplate.query.filter_by(name=data["name"]).first()
            if existing:
                return jsonify({"error": "Template name already exists"}), 400

        # Convert variables list to JSON string for storage
        if "variables" in data and data["variables"]:
            data["variables"] = json.dumps(data["variables"])

        for key, value in data.items():
            setattr(template, key, value)

        db.session.commit()

        app.logger.info(f"Notification template updated: {template.name} by user {current_user.username}")
        return jsonify(template.to_dict()), 200

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating notification template: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/notification-templates/<int:template_id>", methods=["DELETE"])
@admin_required
def delete_notification_template(template_id):
    """Delete a notification template (Admin only)"""
    from .models import NotificationTemplate

    template = NotificationTemplate.query.get(template_id)
    if not template:
        return jsonify({"error": "Notification template not found"}), 404

    try:
        # Soft delete by marking as inactive
        template.is_active = False
        db.session.commit()

        app.logger.info(f"Notification template deleted: {template.name} by user {current_user.username}")
        return jsonify({"message": "Notification template deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting notification template: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


# ============================================================================
# CLIENT COMMUNICATION PREFERENCE API ENDPOINTS
# ============================================================================

@bp.route("/api/client-preferences", methods=["GET"])
@login_required
def get_all_client_preferences():
    """Get all client communication preferences"""
    from .models import ClientCommunicationPreference

    preferences = ClientCommunicationPreference.query.all()

    return jsonify({"preferences": [p.to_dict() for p in preferences]}), 200


@bp.route("/api/clients/<int:client_id>/preferences", methods=["GET"])
@login_required
def get_client_preferences(client_id):
    """Get or create communication preferences for a specific client"""
    from .models import ClientCommunicationPreference, Client

    # Verify client exists
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404

    # Get or create preferences
    preferences = ClientCommunicationPreference.query.filter_by(client_id=client_id).first()

    if not preferences:
        # Create default preferences
        preferences = ClientCommunicationPreference(client_id=client_id)
        db.session.add(preferences)
        db.session.commit()
        app.logger.info(f"Default communication preferences created for client {client_id}")

    return jsonify(preferences.to_dict()), 200


@bp.route("/api/clients/<int:client_id>/preferences", methods=["PUT"])
@login_required
def update_client_preferences(client_id):
    """Update communication preferences for a specific client"""
    from .models import ClientCommunicationPreference, Client
    from .schemas import ClientCommunicationPreferenceSchema

    # Verify client exists
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404

    # Get or create preferences
    preferences = ClientCommunicationPreference.query.filter_by(client_id=client_id).first()

    schema = ClientCommunicationPreferenceSchema(partial=True)
    try:
        data = schema.load(request.json)

        if not preferences:
            # Create new preferences
            data["client_id"] = client_id
            preferences = ClientCommunicationPreference(**data)
            db.session.add(preferences)
        else:
            # Update existing preferences
            for key, value in data.items():
                if key != "client_id":  # Don't update client_id
                    setattr(preferences, key, value)

        db.session.commit()

        app.logger.info(f"Communication preferences updated for client {client_id}")
        return jsonify(preferences.to_dict()), 200

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating client preferences: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


# ============================================================================
# REMINDER API ENDPOINTS
# ============================================================================

@bp.route("/api/reminders", methods=["GET"])
@login_required
def get_all_reminders():
    """Get all reminders with optional filtering"""
    from .models import Reminder

    # Get query parameters
    client_id = request.args.get("client_id", type=int)
    patient_id = request.args.get("patient_id", type=int)
    reminder_type = request.args.get("reminder_type")
    status = request.args.get("status")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    # Build query with filters
    query = Reminder.query

    if client_id:
        query = query.filter(Reminder.client_id == client_id)

    if patient_id:
        query = query.filter(Reminder.patient_id == patient_id)

    if reminder_type:
        query = query.filter(Reminder.reminder_type == reminder_type)

    if status:
        query = query.filter(Reminder.status == status)

    if from_date:
        query = query.filter(Reminder.scheduled_date >= from_date)

    if to_date:
        query = query.filter(Reminder.scheduled_date <= to_date)

    reminders = query.order_by(Reminder.send_at.desc()).all()

    return jsonify({"reminders": [r.to_dict() for r in reminders]}), 200


@bp.route("/api/reminders/pending", methods=["GET"])
@login_required
def get_pending_reminders():
    """Get all pending reminders"""
    from .models import Reminder

    pending_reminders = Reminder.query.filter_by(status="pending").order_by(Reminder.send_at).all()

    return jsonify({"reminders": [r.to_dict() for r in pending_reminders]}), 200


@bp.route("/api/reminders/upcoming", methods=["GET"])
@login_required
def get_upcoming_reminders():
    """Get upcoming reminders (pending, within next 7 days)"""
    from .models import Reminder
    from datetime import datetime, timedelta

    # Get reminders that are pending and scheduled within the next 7 days
    end_date = datetime.now() + timedelta(days=7)

    upcoming_reminders = (
        Reminder.query.filter_by(status="pending")
        .filter(Reminder.send_at <= end_date)
        .filter(Reminder.send_at >= datetime.now())
        .order_by(Reminder.send_at)
        .all()
    )

    return jsonify({"reminders": [r.to_dict() for r in upcoming_reminders]}), 200


@bp.route("/api/reminders/<int:reminder_id>", methods=["GET"])
@login_required
def get_reminder(reminder_id):
    """Get a specific reminder by ID"""
    from .models import Reminder

    reminder = Reminder.query.get(reminder_id)
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404

    return jsonify(reminder.to_dict()), 200


@bp.route("/api/reminders", methods=["POST"])
@login_required
def create_reminder():
    """Create a new reminder"""
    from .models import Reminder, Client, Patient, NotificationTemplate
    from .schemas import ReminderSchema

    schema = ReminderSchema()
    try:
        data = schema.load(request.json)

        # Verify client exists
        client = Client.query.get(data["client_id"])
        if not client:
            return jsonify({"error": "Client not found"}), 404

        # Verify patient exists if provided
        if data.get("patient_id"):
            patient = Patient.query.get(data["patient_id"])
            if not patient:
                return jsonify({"error": "Patient not found"}), 404

        # Verify template exists if provided
        if data.get("template_id"):
            template = NotificationTemplate.query.get(data["template_id"])
            if not template:
                return jsonify({"error": "Notification template not found"}), 404

        reminder = Reminder(**data)
        reminder.created_by_id = current_user.id

        db.session.add(reminder)
        db.session.commit()

        app.logger.info(f"Reminder created for client {client.name} by user {current_user.username}")
        return jsonify(reminder.to_dict()), 201

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating reminder: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/reminders/<int:reminder_id>", methods=["PUT"])
@login_required
def update_reminder(reminder_id):
    """Update a reminder"""
    from .models import Reminder
    from .schemas import ReminderSchema

    reminder = Reminder.query.get(reminder_id)
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404

    schema = ReminderSchema(partial=True)
    try:
        data = schema.load(request.json)

        for key, value in data.items():
            setattr(reminder, key, value)

        db.session.commit()

        app.logger.info(f"Reminder {reminder_id} updated by user {current_user.username}")
        return jsonify(reminder.to_dict()), 200

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating reminder: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/reminders/<int:reminder_id>/cancel", methods=["POST"])
@login_required
def cancel_reminder(reminder_id):
    """Cancel a pending reminder"""
    from .models import Reminder

    reminder = Reminder.query.get(reminder_id)
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404

    try:
        if reminder.status != "pending":
            return jsonify({"error": "Can only cancel pending reminders"}), 400

        reminder.status = "cancelled"
        db.session.commit()

        app.logger.info(f"Reminder {reminder_id} cancelled by user {current_user.username}")
        return jsonify(reminder.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error cancelling reminder: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/reminders/<int:reminder_id>", methods=["DELETE"])
@admin_required
def delete_reminder(reminder_id):
    """Delete a reminder (Admin only)"""
    from .models import Reminder

    reminder = Reminder.query.get(reminder_id)
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404

    try:
        db.session.delete(reminder)
        db.session.commit()

        app.logger.info(f"Reminder {reminder_id} deleted by user {current_user.username}")
        return jsonify({"message": "Reminder deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting reminder: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


# ============================================================================


@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def serve(path):
    static_folder = app.config.get("STATIC_FOLDER")
    if path != "" and os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)
    else:
        return send_from_directory(static_folder, "index.html")
