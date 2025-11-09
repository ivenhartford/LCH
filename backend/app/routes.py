import os
import uuid
from io import BytesIO
from werkzeug.utils import secure_filename
from flask import jsonify, send_from_directory, send_file, request, Blueprint
from flask import current_app as app
from .pdf_generator import (
    VaccinationCertificateGenerator,
    HealthCertificateGenerator,
    MedicalRecordSummaryGenerator,
)
from .models import (
    db,
    User,
    Patient,
    Pet,
    Appointment,
    AppointmentType,
    Client,
    Visit,
    VitalSigns,
    SOAPNote,
    Diagnosis,
    Vaccination,
    Medication,
    Prescription,
    Service,
    Invoice,
    InvoiceItem,
    Payment,
    Vendor,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    InventoryTransaction,
    ClientPortalUser,
    AppointmentRequest,
    Document,
    Protocol,
    ProtocolStep,
    TreatmentPlan,
    TreatmentPlanStep,
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
    client_portal_user_schema,
    client_portal_users_schema,
    client_portal_user_registration_schema,
    client_portal_user_login_schema,
    client_portal_user_update_schema,
    appointment_request_schema,
    appointment_requests_schema,
    appointment_request_create_schema,
    appointment_request_review_schema,
    document_schema,
    documents_schema,
    document_update_schema,
    protocol_schema,
    protocols_schema,
    protocol_create_schema,
    protocol_update_schema,
    treatment_plan_schema,
    treatment_plans_schema,
    treatment_plan_create_schema,
    treatment_plan_update_schema,
    treatment_plan_step_update_schema,
)
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from functools import wraps
from flask import abort
from marshmallow import ValidationError, ValidationError as MarshmallowValidationError
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from .auth import generate_portal_token, portal_auth_required, verify_portal_token
from .email_verification import generate_verification_token, send_verification_email, is_token_valid
from . import limiter
from .audit_logger import (
    log_audit_event,
    log_business_operation,
    log_performance_decorator,
    get_changed_fields,
)

bp = Blueprint("main", __name__)


def admin_required(f):
    """Decorator that requires user to be logged in AND be an administrator"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        # Check if user is administrator
        if current_user.role != "administrator":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)

    # Apply login_required to the decorated function
    return login_required(decorated_function)


@bp.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint for Docker and monitoring."""
    try:
        # Check database connection
        db.session.execute("SELECT 1")
        return (
            jsonify({"status": "healthy", "service": "Lenox Cat Hospital API", "database": "connected"}),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "service": "Lenox Cat Hospital API",
                    "database": "disconnected",
                    "error": str(e),
                }
            ),
            503,
        )


@bp.route("/api/register", methods=["POST"])
@limiter.limit("5 per hour")
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
@limiter.limit("10 per 5 minutes")
def login():
    from .security_monitor import get_security_monitor

    security_monitor = get_security_monitor()
    ip_address = security_monitor.get_client_ip()

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = User.query.filter_by(username=username).first()

    if not user:
        # Track failed login for unknown user
        security_monitor.track_failed_login(ip_address, username)
        app.logger.warning(f"Failed login attempt for unknown username: {username} from {ip_address}")
        return jsonify({"message": "Invalid credentials"}), 401

    # Check if account is locked
    if user.account_locked_until and user.account_locked_until > datetime.utcnow():
        app.logger.warning(f"Login attempt for locked account: {username} from {ip_address}")
        return jsonify({"error": "Account is locked. Please contact administrator."}), 403

    # Verify password
    if user.check_password(password):
        # Successful login - reset failed attempts
        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Track successful login
        security_monitor.track_successful_login(ip_address, username, user.id)

        login_user(user)
        app.logger.info(f"User {username} logged in successfully from {ip_address}")
        return jsonify({"message": "Logged in successfully"}), 200
    else:
        # Track failed login attempt
        security_monitor.track_failed_login(ip_address, username)

        # Failed login - increment counter
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

        # Lock account after 5 failed attempts for 15 minutes
        if user.failed_login_attempts >= 5:
            from datetime import timedelta

            user.account_locked_until = datetime.utcnow() + timedelta(minutes=15)
            db.session.commit()

            # Track account lockout event
            security_monitor.track_account_lockout(username, user.id, ip_address)

            app.logger.warning(
                f"Account locked for user {username} after {user.failed_login_attempts} failed attempts from {ip_address}"
            )
            return (
                jsonify({"error": "Account locked due to multiple failed login attempts. Try again in 15 minutes."}),
                403,
            )

        db.session.commit()
        app.logger.warning(
            f"Failed login attempt for username: {username} from {ip_address}. "
            f"Attempts: {user.failed_login_attempts}/5"
        )
        return jsonify({"message": "Invalid credentials"}), 401


@bp.route("/api/check_session")
def check_session():
    if current_user.is_authenticated:
        return jsonify({"id": current_user.id, "username": current_user.username, "role": current_user.role})
    return jsonify({}), 401


@bp.route("/api/logout")
@login_required
def logout():
    from .security_monitor import get_security_monitor

    security_monitor = get_security_monitor()
    ip_address = security_monitor.get_client_ip()

    # Track logout event
    security_monitor.track_logout(current_user.username, current_user.id, ip_address)

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

        return (
            jsonify(
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
            ),
            200,
        )

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
@log_performance_decorator
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

        # Audit log: Appointment created
        log_audit_event(
            action="create",
            entity_type="appointment",
            entity_id=appointment.id,
            entity_data={
                "title": appointment.title,
                "client_id": appointment.client_id,
                "patient_id": appointment.patient_id,
                "start_time": (appointment.start_time.isoformat() if appointment.start_time else None),
                "status": appointment.status,
                "appointment_type_id": appointment.appointment_type_id,
            },
        )

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
@log_performance_decorator
def update_appointment(appointment_id):
    """Update an appointment"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        data = request.get_json()
        validated_data = appointment_schema.load(data, partial=True)

        # Capture old values for audit trail
        old_values = {}
        for key in validated_data.keys():
            if hasattr(appointment, key):
                old_value = getattr(appointment, key)
                # Convert datetime to ISO format for JSON serialization
                if isinstance(old_value, datetime):
                    old_value = old_value.isoformat()
                old_values[key] = old_value

        # Track old status for business operation logging
        old_status = appointment.status

        # Update fields
        new_values = {}
        for key, value in validated_data.items():
            if hasattr(appointment, key) and key not in ["id", "created_at", "created_by_id"]:
                setattr(appointment, key, value)
                # Convert datetime to ISO format for logging
                if isinstance(value, datetime):
                    value = value.isoformat()
                new_values[key] = value

        # Handle status workflow timestamps
        if "status" in validated_data:
            new_status = validated_data["status"]
            if new_status == "checked_in" and not appointment.check_in_time:
                appointment.check_in_time = datetime.utcnow()
            elif new_status == "in_progress" and not appointment.actual_start_time:
                appointment.actual_start_time = datetime.utcnow()
            elif new_status == "completed" and not appointment.actual_end_time:
                appointment.actual_end_time = datetime.utcnow()
            elif new_status == "cancelled" and not appointment.cancelled_at:
                appointment.cancelled_at = datetime.utcnow()
                appointment.cancelled_by_id = current_user.id

        db.session.commit()

        # Audit log: Appointment updated (only changed fields)
        changed_old, changed_new = get_changed_fields(old_values, new_values)
        if changed_old:
            log_audit_event(
                action="update",
                entity_type="appointment",
                entity_id=appointment_id,
                old_values=changed_old,
                new_values=changed_new,
            )

        # Business operation log: Status change
        if "status" in validated_data and old_status != validated_data["status"]:
            log_business_operation(
                operation="appointment_status_change",
                entity_type="appointment",
                entity_id=appointment_id,
                details={
                    "old_status": old_status,
                    "new_status": validated_data["status"],
                    "changed_by": current_user.username,
                },
            )

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
@log_performance_decorator
def delete_appointment(appointment_id):
    """Delete an appointment (admin only)"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)

        # Capture appointment data for audit trail
        appointment_data = {
            "title": appointment.title,
            "client_id": appointment.client_id,
            "patient_id": appointment.patient_id,
            "start_time": appointment.start_time.isoformat() if appointment.start_time else None,
            "status": appointment.status,
        }

        db.session.delete(appointment)
        db.session.commit()

        # Audit log: Appointment deleted
        log_audit_event(
            action="delete",
            entity_type="appointment",
            entity_id=appointment_id,
            entity_data=appointment_data,
        )
        log_business_operation(
            operation="appointment_deleted",
            entity_type="appointment",
            entity_id=appointment_id,
            details={"deleted_by": current_user.username, "title": appointment_data["title"]},
        )

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
@log_performance_decorator
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

        # Audit log: Client created
        log_audit_event(
            action="create",
            entity_type="client",
            entity_id=new_client.id,
            entity_data={
                "first_name": new_client.first_name,
                "last_name": new_client.last_name,
                "email": new_client.email,
                "phone_primary": new_client.phone_primary,
            },
        )

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
@log_performance_decorator
def update_client(client_id):
    """Update an existing client"""
    try:
        data = request.get_json()

        app.logger.info(f"PUT /api/clients/{client_id} - User: {current_user.username}")

        client = Client.query.get_or_404(client_id)

        # Capture old values for audit trail
        old_values = {}
        for key in data.keys():
            if hasattr(client, key):
                old_values[key] = getattr(client, key)

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
        new_values = {}
        for key, value in validated_data.items():
            setattr(client, key, value)
            new_values[key] = value

        db.session.commit()

        app.logger.info(f"Updated client {client_id}: {client.first_name} {client.last_name}")

        # Audit log: Client updated
        changed_old, changed_new = get_changed_fields(old_values, new_values)
        if changed_old:  # Only log if there were actual changes
            log_audit_event(
                action="update",
                entity_type="client",
                entity_id=client_id,
                old_values=changed_old,
                new_values=changed_new,
            )

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
@log_performance_decorator
def delete_client(client_id):
    """
    Soft delete a client (sets is_active to False)
    Use ?hard=true query param for hard delete (requires admin)
    """
    try:
        hard_delete = request.args.get("hard", "false").lower() == "true"

        app.logger.info(f"DELETE /api/clients/{client_id} - User: {current_user.username}, Hard: {hard_delete}")

        client = Client.query.get_or_404(client_id)

        # Capture client data for audit trail
        client_data = {
            "first_name": client.first_name,
            "last_name": client.last_name,
            "email": client.email,
            "phone_primary": client.phone_primary,
        }

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

            # Audit log: Hard delete
            log_audit_event(action="delete", entity_type="client", entity_id=client_id, entity_data=client_data)
            log_business_operation(
                operation="client_hard_delete",
                entity_type="client",
                entity_id=client_id,
                details={"admin": current_user.username},
            )

            return jsonify({"message": "Client permanently deleted"}), 200
        else:
            # Soft delete
            client.is_active = False
            db.session.commit()
            app.logger.info(f"Soft deleted (deactivated) client {client_id}: {client.first_name} {client.last_name}")

            # Audit log: Soft delete
            log_business_operation(
                operation="client_deactivated",
                entity_type="client",
                entity_id=client_id,
                details={"deactivated_by": current_user.username},
            )

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
@log_performance_decorator
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

        # Audit log: Patient created
        log_audit_event(
            action="create",
            entity_type="patient",
            entity_id=new_patient.id,
            entity_data={
                "name": new_patient.name,
                "species": new_patient.species,
                "breed": new_patient.breed,
                "owner_id": new_patient.owner_id,
                "microchip_number": new_patient.microchip_number,
            },
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
@log_performance_decorator
def update_patient(patient_id):
    """Update an existing patient"""
    try:
        data = request.get_json()

        app.logger.info(f"PUT /api/patients/{patient_id} - User: {current_user.username}")

        patient = Patient.query.get_or_404(patient_id)

        # Capture old values for audit trail
        old_values = {}
        for key in data.keys():
            if hasattr(patient, key):
                old_values[key] = getattr(patient, key)

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

        # Update patient fields and track new values
        new_values = {}
        for key, value in validated_data.items():
            setattr(patient, key, value)
            new_values[key] = value

        db.session.commit()

        # Audit log: Patient updated (only changed fields)
        changed_old, changed_new = get_changed_fields(old_values, new_values)
        if changed_old:
            log_audit_event(
                action="update",
                entity_type="patient",
                entity_id=patient_id,
                old_values=changed_old,
                new_values=changed_new,
            )

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
@log_performance_decorator
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

        # Capture patient data for audit trail
        patient_data = {
            "name": patient.name,
            "species": patient.species,
            "breed": patient.breed,
            "owner_id": patient.owner_id,
            "microchip_number": patient.microchip_number,
            "status": patient.status,
        }

        if hard_delete:
            # Hard delete requires admin role
            if current_user.role != "administrator":
                app.logger.warning(
                    f"Non-admin user {current_user.username} attempted hard delete of patient {patient_id}"
                )
                return jsonify({"error": "Admin access required for hard delete"}), 403

            db.session.delete(patient)
            db.session.commit()

            # Audit log: Patient hard deleted
            log_audit_event(
                action="delete",
                entity_type="patient",
                entity_id=patient_id,
                entity_data=patient_data,
            )
            log_business_operation(
                operation="patient_hard_delete",
                entity_type="patient",
                entity_id=patient_id,
                details={"deleted_by": current_user.username, "patient_name": patient_data["name"]},
            )

            app.logger.info(f"Hard deleted patient {patient_id}: {patient_data['name']}")
            return jsonify({"message": "Patient permanently deleted"}), 200
        else:
            # Soft delete - set to inactive
            patient.status = "Inactive"
            db.session.commit()

            # Business operation log: Patient deactivated
            log_business_operation(
                operation="patient_deactivated",
                entity_type="patient",
                entity_id=patient_id,
                details={
                    "deactivated_by": current_user.username,
                    "patient_name": patient.name,
                    "previous_status": patient_data["status"],
                },
            )

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
@log_performance_decorator
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

        # Audit log: Visit created (HIPAA-sensitive medical record)
        log_audit_event(
            action="create",
            entity_type="visit",
            entity_id=visit.id,
            entity_data={
                "patient_id": visit.patient_id,
                "visit_type": visit.visit_type,
                "visit_date": visit.visit_date.isoformat() if visit.visit_date else None,
                "veterinarian_id": visit.veterinarian_id,
                "appointment_id": visit.appointment_id,
                "status": visit.status,
            },
        )

        app.logger.info(f"Created visit {visit.id} for patient {patient.name}")
        return jsonify(visit.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating visit: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/visits/<int:visit_id>", methods=["PUT"])
@login_required
@log_performance_decorator
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

        # Capture old values for audit trail
        old_values = {}
        for key in validated_data.keys():
            if hasattr(visit, key):
                old_value = getattr(visit, key)
                if isinstance(old_value, datetime):
                    old_value = old_value.isoformat()
                old_values[key] = old_value

        # Track old status for business operation logging
        old_status = visit.status

        # Update fields
        new_values = {}
        for key, value in validated_data.items():
            if hasattr(visit, key):
                setattr(visit, key, value)
                if isinstance(value, datetime):
                    value = value.isoformat()
                new_values[key] = value

        # If marking as completed, set completed_at
        if validated_data.get("status") == "completed" and not visit.completed_at:
            visit.completed_at = datetime.utcnow()

        db.session.commit()

        # Audit log: Visit updated (only changed fields)
        changed_old, changed_new = get_changed_fields(old_values, new_values)
        if changed_old:
            log_audit_event(
                action="update",
                entity_type="visit",
                entity_id=visit_id,
                old_values=changed_old,
                new_values=changed_new,
            )

        # Business operation log: Status change
        if "status" in validated_data and old_status != validated_data["status"]:
            log_business_operation(
                operation="visit_status_change",
                entity_type="visit",
                entity_id=visit_id,
                details={
                    "old_status": old_status,
                    "new_status": validated_data["status"],
                    "patient_id": visit.patient_id,
                    "changed_by": current_user.username,
                },
            )

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
@log_performance_decorator
def delete_visit(visit_id):
    """Delete a visit"""
    try:
        from .models import Visit

        visit = Visit.query.get_or_404(visit_id)

        app.logger.info(f"DELETE /api/visits/{visit_id} - User: {current_user.username}")

        # Capture visit data for audit trail (HIPAA-sensitive)
        visit_data = {
            "patient_id": visit.patient_id,
            "visit_type": visit.visit_type,
            "visit_date": visit.visit_date.isoformat() if visit.visit_date else None,
            "veterinarian_id": visit.veterinarian_id,
            "appointment_id": visit.appointment_id,
            "status": visit.status,
        }

        db.session.delete(visit)
        db.session.commit()

        # Audit log: Visit deleted (HIPAA-sensitive medical record)
        log_audit_event(action="delete", entity_type="visit", entity_id=visit_id, entity_data=visit_data)
        log_business_operation(
            operation="visit_deleted",
            entity_type="visit",
            entity_id=visit_id,
            details={
                "deleted_by": current_user.username,
                "patient_id": visit_data["patient_id"],
                "visit_type": visit_data["visit_type"],
            },
        )

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
        return (
            jsonify({"medications": [med.to_dict() for med in medications], "total": len(medications)}),
            200,
        )

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
        return (
            jsonify(
                {
                    "prescriptions": [rx.to_dict() for rx in prescriptions],
                    "total": len(prescriptions),
                }
            ),
            200,
        )

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
            if hasattr(prescription, key) and key not in [
                "patient_id",
                "medication_id",
                "prescribed_by_id",
            ]:
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
@log_performance_decorator
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

        # Audit log: Invoice created
        log_audit_event(
            action="create",
            entity_type="invoice",
            entity_id=invoice.id,
            entity_data={
                "invoice_number": invoice.invoice_number,
                "client_id": invoice.client_id,
                "patient_id": invoice.patient_id,
                "total_amount": float(invoice.total_amount),
                "status": invoice.status,
                "item_count": len(items_data),
            },
        )
        log_business_operation(
            operation="invoice_generated",
            entity_type="invoice",
            entity_id=invoice.id,
            details={
                "invoice_number": invoice.invoice_number,
                "total_amount": float(invoice.total_amount),
                "created_by": current_user.username,
            },
        )

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
@log_performance_decorator
def update_invoice(invoice_id):
    """Update an invoice"""
    try:
        from .models import Invoice, InvoiceItem
        from .schemas import invoice_schema
        from decimal import Decimal

        invoice = Invoice.query.get_or_404(invoice_id)
        data = request.get_json()
        validated_data = invoice_schema.load(data, partial=True)

        # Capture old values for audit trail
        old_values = {}
        for key in validated_data.keys():
            if hasattr(invoice, key):
                old_value = getattr(invoice, key)
                # Convert Decimal to float for JSON serialization
                if isinstance(old_value, Decimal):
                    old_value = float(old_value)
                elif isinstance(old_value, datetime):
                    old_value = old_value.isoformat()
                old_values[key] = old_value

        # Track old status for business operation logging
        old_status = invoice.status

        # Update basic fields
        new_values = {}
        for key in [
            "patient_id",
            "visit_id",
            "invoice_date",
            "due_date",
            "status",
            "notes",
            "discount_amount",
        ]:
            if key in validated_data:
                setattr(invoice, key, validated_data[key])
                value = validated_data[key]
                if isinstance(value, Decimal):
                    value = float(value)
                elif isinstance(value, datetime):
                    value = value.isoformat()
                new_values[key] = value

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

        # Audit log: Invoice updated (only changed fields)
        changed_old, changed_new = get_changed_fields(old_values, new_values)
        if changed_old:
            log_audit_event(
                action="update",
                entity_type="invoice",
                entity_id=invoice_id,
                old_values=changed_old,
                new_values=changed_new,
            )

        # Business operation log: Status change
        if "status" in validated_data and old_status != validated_data["status"]:
            log_business_operation(
                operation="invoice_status_change",
                entity_type="invoice",
                entity_id=invoice_id,
                details={
                    "old_status": old_status,
                    "new_status": validated_data["status"],
                    "invoice_number": invoice.invoice_number,
                    "changed_by": current_user.username,
                },
            )

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
@log_performance_decorator
def delete_invoice(invoice_id):
    """Delete an invoice"""
    try:
        from .models import Invoice
        from decimal import Decimal

        invoice = Invoice.query.get_or_404(invoice_id)

        # Capture invoice data for audit trail
        invoice_data = {
            "invoice_number": invoice.invoice_number,
            "client_id": invoice.client_id,
            "patient_id": invoice.patient_id,
            "total_amount": (
                float(invoice.total_amount) if isinstance(invoice.total_amount, Decimal) else invoice.total_amount
            ),
            "status": invoice.status,
            "amount_paid": (
                float(invoice.amount_paid) if isinstance(invoice.amount_paid, Decimal) else invoice.amount_paid
            ),
        }

        db.session.delete(invoice)
        db.session.commit()

        # Audit log: Invoice deleted
        log_audit_event(action="delete", entity_type="invoice", entity_id=invoice_id, entity_data=invoice_data)
        log_business_operation(
            operation="invoice_deleted",
            entity_type="invoice",
            entity_id=invoice_id,
            details={
                "deleted_by": current_user.username,
                "invoice_number": invoice_data["invoice_number"],
                "total_amount": invoice_data["total_amount"],
            },
        )

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
@log_performance_decorator
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

        # Track old invoice status for business operation logging
        old_invoice_status = invoice.status

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

        # Audit log: Payment created
        log_audit_event(
            action="create",
            entity_type="payment",
            entity_id=payment.id,
            entity_data={
                "invoice_id": payment.invoice_id,
                "client_id": payment.client_id,
                "amount": float(payment.amount),
                "payment_method": payment.payment_method,
                "reference_number": payment.reference_number,
            },
        )

        # Business operation log: Payment processed
        log_business_operation(
            operation="payment_processed",
            entity_type="payment",
            entity_id=payment.id,
            details={
                "amount": float(payment.amount),
                "payment_method": payment.payment_method,
                "invoice_id": payment.invoice_id,
                "invoice_number": invoice.invoice_number,
                "processed_by": current_user.username,
                "old_invoice_status": old_invoice_status,
                "new_invoice_status": invoice.status,
            },
        )

        app.logger.info(f"Created payment {payment.id} for invoice {invoice.invoice_number}")
        return jsonify(payment.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating payment: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/payments/<int:payment_id>", methods=["DELETE"])
@login_required
@log_performance_decorator
def delete_payment(payment_id):
    """Delete a payment and update invoice"""
    try:
        from .models import Payment
        from decimal import Decimal

        payment = Payment.query.get_or_404(payment_id)
        invoice = payment.invoice

        # Capture payment data for audit trail
        payment_data = {
            "invoice_id": payment.invoice_id,
            "client_id": payment.client_id,
            "amount": float(payment.amount),
            "payment_method": payment.payment_method,
            "reference_number": payment.reference_number,
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
        }

        # Track old invoice status
        old_invoice_status = invoice.status

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

        # Audit log: Payment deleted (refund/reversal)
        log_audit_event(action="delete", entity_type="payment", entity_id=payment_id, entity_data=payment_data)

        # Business operation log: Payment refund/reversal
        log_business_operation(
            operation="payment_refunded",
            entity_type="payment",
            entity_id=payment_id,
            details={
                "amount": payment_data["amount"],
                "payment_method": payment_data["payment_method"],
                "invoice_id": payment_data["invoice_id"],
                "invoice_number": invoice.invoice_number,
                "processed_by": current_user.username,
                "old_invoice_status": old_invoice_status,
                "new_invoice_status": invoice.status,
            },
        )

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
                "oldest_invoice_date": (row.oldest_invoice_date.isoformat() if row.oldest_invoice_date else None),
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
            Payment.payment_method,
            func.sum(Payment.amount).label("total"),
            func.count(Payment.id).label("count"),
        )

        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Payment.payment_date >= start_dt)

        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Payment.payment_date <= end_dt)

        results = query.group_by(Payment.payment_method).order_by(func.sum(Payment.amount).desc()).all()

        data = [
            {
                "payment_method": row.payment_method,
                "total": float(row.total or 0),
                "count": row.count,
            }
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
# ADVANCED ANALYTICS - Phase 4.3
# ============================================================================


@bp.route("/api/analytics/revenue-trends", methods=["GET"])
@login_required
def get_revenue_trends():
    """
    Get revenue trends over time for charting
    Query params: period (day|week|month), start_date, end_date
    Returns time-series data suitable for line/bar charts
    """
    try:
        period = request.args.get("period", "month")  # day, week, month
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        # Default to last 12 months if not specified
        if not end_date_str:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        if not start_date_str:
            if period == "day":
                start_date = end_date - timedelta(days=30)
            elif period == "week":
                start_date = end_date - timedelta(weeks=12)
            else:  # month
                start_date = end_date - timedelta(days=365)
        else:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")

        # Build query based on period
        if period == "day":
            # Group by day
            trend_data = (
                db.session.query(
                    func.date(Invoice.invoice_date).label("period"),
                    func.sum(Invoice.total_amount).label("revenue"),
                    func.count(Invoice.id).label("invoice_count"),
                )
                .filter(Invoice.invoice_date.between(start_date, end_date))
                .filter(Invoice.status.in_(["paid", "partial_paid"]))
                .group_by(func.date(Invoice.invoice_date))
                .order_by(func.date(Invoice.invoice_date))
                .all()
            )
        elif period == "week":
            # Group by week
            trend_data = (
                db.session.query(
                    func.strftime("%Y-W%W", Invoice.invoice_date).label("period"),
                    func.sum(Invoice.total_amount).label("revenue"),
                    func.count(Invoice.id).label("invoice_count"),
                )
                .filter(Invoice.invoice_date.between(start_date, end_date))
                .filter(Invoice.status.in_(["paid", "partial_paid"]))
                .group_by(func.strftime("%Y-W%W", Invoice.invoice_date))
                .order_by(func.strftime("%Y-W%W", Invoice.invoice_date))
                .all()
            )
        else:  # month
            # Group by month
            trend_data = (
                db.session.query(
                    func.strftime("%Y-%m", Invoice.invoice_date).label("period"),
                    func.sum(Invoice.total_amount).label("revenue"),
                    func.count(Invoice.id).label("invoice_count"),
                )
                .filter(Invoice.invoice_date.between(start_date, end_date))
                .filter(Invoice.status.in_(["paid", "partial_paid"]))
                .group_by(func.strftime("%Y-%m", Invoice.invoice_date))
                .order_by(func.strftime("%Y-%m", Invoice.invoice_date))
                .all()
            )

        data = [
            {
                "period": str(row.period),
                "revenue": float(row.revenue or 0),
                "invoice_count": row.invoice_count,
            }
            for row in trend_data
        ]

        return jsonify({"data": data, "period": period}), 200

    except Exception as e:
        app.logger.error(f"Error getting revenue trends: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/analytics/client-retention", methods=["GET"])
@login_required
def get_client_retention():
    """
    Get client retention metrics
    Returns: new clients, returning clients, retention rate, churn rate
    """
    try:
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        # Default to last 12 months
        if not end_date_str:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        if not start_date_str:
            start_date = end_date - timedelta(days=365)
        else:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")

        # Get all clients created during the period
        new_clients = Client.query.filter(Client.created_at.between(start_date, end_date)).count()

        # Get returning clients (clients with appointments in this period who were created before this period)
        returning_clients = (
            db.session.query(func.count(func.distinct(Appointment.client_id)))
            .join(Client)
            .filter(Appointment.appointment_date.between(start_date, end_date))
            .filter(Client.created_at < start_date)
            .scalar()
        )

        # Total active clients with appointments in period
        active_clients = (
            db.session.query(func.count(func.distinct(Appointment.client_id)))
            .filter(Appointment.appointment_date.between(start_date, end_date))
            .scalar()
        )

        # Total clients at start of period
        total_clients_at_start = Client.query.filter(Client.created_at < start_date).count()

        # Calculate retention rate (returning clients / clients at start)
        retention_rate = (returning_clients / total_clients_at_start * 100) if total_clients_at_start > 0 else 0

        # Calculate churn rate
        churn_rate = 100 - retention_rate

        # Get monthly breakdown
        monthly_breakdown = (
            db.session.query(
                func.strftime("%Y-%m", Client.created_at).label("month"),
                func.count(Client.id).label("count"),
            )
            .filter(Client.created_at.between(start_date, end_date))
            .group_by(func.strftime("%Y-%m", Client.created_at))
            .order_by(func.strftime("%Y-%m", Client.created_at))
            .all()
        )

        monthly_data = [{"month": str(row.month), "new_clients": row.count} for row in monthly_breakdown]

        return (
            jsonify(
                {
                    "new_clients": new_clients,
                    "returning_clients": returning_clients,
                    "active_clients": active_clients,
                    "retention_rate": round(retention_rate, 2),
                    "churn_rate": round(churn_rate, 2),
                    "monthly_breakdown": monthly_data,
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Error getting client retention: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/analytics/appointment-trends", methods=["GET"])
@login_required
def get_appointment_trends():
    """
    Get appointment volume and trends
    Returns: appointment counts by status, type, and over time
    """
    try:
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        # Default to last 90 days
        if not end_date_str:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        if not start_date_str:
            start_date = end_date - timedelta(days=90)
        else:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")

        # Appointments by status
        by_status = (
            db.session.query(Appointment.status, func.count(Appointment.id).label("count"))
            .filter(Appointment.appointment_date.between(start_date, end_date))
            .group_by(Appointment.status)
            .all()
        )

        status_data = [{"status": row.status, "count": row.count} for row in by_status]

        # Appointments by type
        by_type = (
            db.session.query(
                AppointmentType.name,
                AppointmentType.color,
                func.count(Appointment.id).label("count"),
            )
            .join(Appointment, Appointment.appointment_type_id == AppointmentType.id)
            .filter(Appointment.appointment_date.between(start_date, end_date))
            .group_by(AppointmentType.id, AppointmentType.name, AppointmentType.color)
            .order_by(func.count(Appointment.id).desc())
            .all()
        )

        type_data = [{"type": row.name, "color": row.color, "count": row.count} for row in by_type]

        # Daily appointment volume
        daily_volume = (
            db.session.query(
                func.date(Appointment.appointment_date).label("date"),
                func.count(Appointment.id).label("count"),
            )
            .filter(Appointment.appointment_date.between(start_date, end_date))
            .group_by(func.date(Appointment.appointment_date))
            .order_by(func.date(Appointment.appointment_date))
            .all()
        )

        volume_data = [{"date": str(row.date), "count": row.count} for row in daily_volume]

        # Completion rate
        total_appointments = Appointment.query.filter(
            Appointment.appointment_date.between(start_date, end_date)
        ).count()

        completed_appointments = Appointment.query.filter(
            Appointment.appointment_date.between(start_date, end_date),
            Appointment.status == "completed",
        ).count()

        completion_rate = (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0

        return (
            jsonify(
                {
                    "by_status": status_data,
                    "by_type": type_data,
                    "daily_volume": volume_data,
                    "total_appointments": total_appointments,
                    "completed_appointments": completed_appointments,
                    "completion_rate": round(completion_rate, 2),
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Error getting appointment trends: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/analytics/procedure-volume", methods=["GET"])
@login_required
def get_procedure_volume():
    """
    Get procedure/service volume and trends
    Returns: top procedures, trends over time
    """
    try:
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        limit = request.args.get("limit", 10, type=int)

        # Default to last 6 months
        if not end_date_str:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        if not start_date_str:
            start_date = end_date - timedelta(days=180)
        else:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")

        # Top procedures by volume
        top_procedures = (
            db.session.query(
                Service.name,
                Service.service_type,
                func.sum(InvoiceItem.quantity).label("total_quantity"),
                func.sum(InvoiceItem.line_total).label("total_revenue"),
                func.count(InvoiceItem.id).label("times_performed"),
            )
            .join(InvoiceItem, InvoiceItem.service_id == Service.id)
            .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
            .filter(Invoice.invoice_date.between(start_date, end_date))
            .group_by(Service.id, Service.name, Service.service_type)
            .order_by(func.count(InvoiceItem.id).desc())
            .limit(limit)
            .all()
        )

        procedure_data = [
            {
                "name": row.name,
                "type": row.service_type,
                "quantity": float(row.total_quantity or 0),
                "revenue": float(row.total_revenue or 0),
                "times_performed": row.times_performed,
            }
            for row in top_procedures
        ]

        # Monthly trend for top 5 procedures
        top_5_service_ids = (
            db.session.query(Service.id)
            .join(InvoiceItem, InvoiceItem.service_id == Service.id)
            .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
            .filter(Invoice.invoice_date.between(start_date, end_date))
            .group_by(Service.id)
            .order_by(func.count(InvoiceItem.id).desc())
            .limit(5)
            .all()
        )

        monthly_trends = []
        for (service_id,) in top_5_service_ids:
            service = Service.query.get(service_id)
            trend = (
                db.session.query(
                    func.strftime("%Y-%m", Invoice.invoice_date).label("month"),
                    func.count(InvoiceItem.id).label("count"),
                )
                .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
                .filter(InvoiceItem.service_id == service_id)
                .filter(Invoice.invoice_date.between(start_date, end_date))
                .group_by(func.strftime("%Y-%m", Invoice.invoice_date))
                .order_by(func.strftime("%Y-%m", Invoice.invoice_date))
                .all()
            )

            monthly_trends.append(
                {
                    "service_name": service.name,
                    "service_id": service_id,
                    "trend": [{"month": str(row.month), "count": row.count} for row in trend],
                }
            )

        return jsonify({"top_procedures": procedure_data, "monthly_trends": monthly_trends}), 200

    except Exception as e:
        app.logger.error(f"Error getting procedure volume: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/analytics/patient-demographics", methods=["GET"])
@login_required
def get_patient_demographics():
    """
    Get patient demographic breakdowns
    Returns: age distribution, breed distribution, gender distribution
    """
    try:
        # Get all active patients
        active_patients = Patient.query.filter(Patient.status == "active").all()

        # Calculate age distribution
        age_groups = {
            "0-1 years": 0,
            "1-3 years": 0,
            "3-7 years": 0,
            "7-10 years": 0,
            "10+ years": 0,
        }

        for patient in active_patients:
            if patient.date_of_birth:
                age_years = (datetime.now().date() - patient.date_of_birth).days / 365.25
                if age_years < 1:
                    age_groups["0-1 years"] += 1
                elif age_years < 3:
                    age_groups["1-3 years"] += 1
                elif age_years < 7:
                    age_groups["3-7 years"] += 1
                elif age_years < 10:
                    age_groups["7-10 years"] += 1
                else:
                    age_groups["10+ years"] += 1

        # Get breed distribution (top 10)
        breed_counts = (
            db.session.query(Patient.breed, func.count(Patient.id).label("count"))
            .filter(Patient.status == "active")
            .group_by(Patient.breed)
            .order_by(func.count(Patient.id).desc())
            .limit(10)
            .all()
        )

        breed_data = [{"breed": row.breed or "Unknown", "count": row.count} for row in breed_counts]

        # Get gender distribution
        gender_counts = (
            db.session.query(Patient.sex, func.count(Patient.id).label("count"))
            .filter(Patient.status == "active")
            .group_by(Patient.sex)
            .all()
        )

        gender_data = [{"gender": row.sex or "Unknown", "count": row.count} for row in gender_counts]

        # Get reproductive status
        spay_neuter_count = Patient.query.filter(
            Patient.status == "active", Patient.reproductive_status.in_(["spayed", "neutered"])
        ).count()

        total_patients = len(active_patients)
        spay_neuter_rate = (spay_neuter_count / total_patients * 100) if total_patients > 0 else 0

        return (
            jsonify(
                {
                    "age_distribution": [{"age_group": k, "count": v} for k, v in age_groups.items()],
                    "breed_distribution": breed_data,
                    "gender_distribution": gender_data,
                    "total_patients": total_patients,
                    "spay_neuter_rate": round(spay_neuter_rate, 2),
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Error getting patient demographics: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/analytics/dashboard-summary", methods=["GET"])
@login_required
def get_dashboard_summary():
    """
    Get high-level KPIs for analytics dashboard
    Returns: key metrics for display on dashboard
    """
    try:
        # Get today's date and calculate time ranges
        today = datetime.now().date()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = this_month_start - timedelta(days=1)
        this_year_start = today.replace(month=1, day=1)

        # Revenue this month
        revenue_this_month = (
            db.session.query(func.sum(Invoice.total_amount))
            .filter(Invoice.invoice_date >= this_month_start)
            .filter(Invoice.status.in_(["paid", "partial_paid"]))
            .scalar()
            or 0
        )

        # Revenue last month
        revenue_last_month = (
            db.session.query(func.sum(Invoice.total_amount))
            .filter(Invoice.invoice_date.between(last_month_start, last_month_end))
            .filter(Invoice.status.in_(["paid", "partial_paid"]))
            .scalar()
            or 0
        )

        # Revenue growth percentage
        revenue_growth = (
            ((revenue_this_month - revenue_last_month) / revenue_last_month * 100) if revenue_last_month > 0 else 0
        )

        # Active patients
        active_patients = Patient.query.filter(Patient.status == "active").count()

        # New patients this month
        new_patients_this_month = Patient.query.filter(Patient.created_at >= this_month_start).count()

        # Appointments this month
        appointments_this_month = Appointment.query.filter(Appointment.appointment_date >= this_month_start).count()

        # Completed appointments this month
        completed_appointments = Appointment.query.filter(
            Appointment.appointment_date >= this_month_start, Appointment.status == "completed"
        ).count()

        # Average revenue per appointment
        avg_revenue_per_appointment = (revenue_this_month / completed_appointments) if completed_appointments > 0 else 0

        # Outstanding balance
        outstanding_balance = (
            db.session.query(func.sum(Invoice.balance_due))
            .filter(Invoice.status.in_(["sent", "partial_paid", "overdue"]))
            .scalar()
            or 0
        )

        return (
            jsonify(
                {
                    "revenue_this_month": float(revenue_this_month),
                    "revenue_last_month": float(revenue_last_month),
                    "revenue_growth": round(revenue_growth, 2),
                    "active_patients": active_patients,
                    "new_patients_this_month": new_patients_this_month,
                    "appointments_this_month": appointments_this_month,
                    "completed_appointments": completed_appointments,
                    "avg_revenue_per_appointment": round(float(avg_revenue_per_appointment), 2),
                    "outstanding_balance": float(outstanding_balance),
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Error getting dashboard summary: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


# ============================================================================
# PDF DOCUMENT GENERATION - Phase 4.4
# ============================================================================


@bp.route("/api/pdf/vaccination-certificate/<int:vaccination_id>", methods=["GET"])
@login_required
def generate_vaccination_certificate(vaccination_id):
    """
    Generate a vaccination certificate PDF
    Returns PDF file for download
    """
    try:
        # Get vaccination record
        vaccination = Vaccination.query.get_or_404(vaccination_id)
        patient = Patient.query.get_or_404(vaccination.patient_id)
        owner = Client.query.get_or_404(patient.owner_id)

        # Prepare data for PDF
        patient_data = {
            "name": patient.name,
            "breed": patient.breed,
            "color": patient.color,
            "sex": patient.sex,
            "date_of_birth": (patient.date_of_birth.strftime("%m/%d/%Y") if patient.date_of_birth else "N/A"),
            "microchip_number": patient.microchip_number or "N/A",
            "weight": patient.weight or "N/A",
        }

        vaccination_data = {
            "id": vaccination.id,
            "vaccine_name": vaccination.vaccine_name,
            "manufacturer": vaccination.manufacturer or "N/A",
            "lot_number": vaccination.lot_number or "N/A",
            "administered_date": (
                vaccination.administered_date.strftime("%m/%d/%Y") if vaccination.administered_date else "N/A"
            ),
            "expiration_date": (
                vaccination.expiration_date.strftime("%m/%d/%Y") if vaccination.expiration_date else "N/A"
            ),
            "next_due_date": (vaccination.next_due_date.strftime("%m/%d/%Y") if vaccination.next_due_date else "N/A"),
            "administered_by": vaccination.administered_by or "N/A",
            "notes": vaccination.notes or "",
        }

        owner_data = {
            "name": f"{owner.first_name} {owner.last_name}",
            "phone": owner.phone_primary,
            "email": owner.email or "N/A",
            "address": f"{owner.address_line1 or ''}, {owner.city or ''}, {owner.state or ''} {owner.zip_code or ''}".strip(
                ", "
            ),
        }

        # Generate PDF
        generator = VaccinationCertificateGenerator()
        pdf_buffer = generator.generate(patient_data, vaccination_data, owner_data)

        # Return PDF file
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"vaccination_certificate_{patient.name}_{vaccination.id}.pdf",
        )

    except Exception as e:
        app.logger.error(f"Error generating vaccination certificate: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/pdf/health-certificate/<int:patient_id>", methods=["POST"])
@login_required
def generate_health_certificate(patient_id):
    """
    Generate a health certificate PDF
    Expects JSON body with exam data
    Returns PDF file for download
    """
    try:
        # Get patient and owner
        patient = Patient.query.get_or_404(patient_id)
        owner = Client.query.get_or_404(patient.owner_id)

        # Get exam data from request
        exam_data = request.get_json() or {}

        # Calculate age if date_of_birth exists
        age = "N/A"
        if patient.date_of_birth:
            from datetime import datetime

            today = datetime.now().date()
            age_years = (today - patient.date_of_birth).days // 365
            age = f"{age_years} years"

        # Prepare data for PDF
        patient_data = {
            "name": patient.name,
            "breed": patient.breed,
            "color": patient.color,
            "sex": patient.sex,
            "age": age,
            "microchip_number": patient.microchip_number or "N/A",
            "weight": patient.weight or "N/A",
        }

        # Generate certificate number
        cert_number = f"HC-{patient_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        exam_data_formatted = {
            "certificate_number": cert_number,
            "purpose": exam_data.get("purpose", "General Health Assessment"),
            "exam_date": exam_data.get("exam_date", datetime.now().strftime("%m/%d/%Y")),
            "temperature": exam_data.get("temperature", "N/A"),
            "heart_rate": exam_data.get("heart_rate", "N/A"),
            "respiratory_rate": exam_data.get("respiratory_rate", "N/A"),
            "weight": exam_data.get("weight", patient.weight or "N/A"),
            "findings": exam_data.get("findings", "Patient appears healthy with no abnormalities detected."),
            "health_status": exam_data.get("health_status", "HEALTHY"),
            "examined_by": exam_data.get(
                "examined_by",
                "Dr. " + (request.user.username if hasattr(request, "user") else "N/A"),
            ),
        }

        owner_data = {
            "name": f"{owner.first_name} {owner.last_name}",
            "phone": owner.phone_primary,
            "email": owner.email or "N/A",
            "address": f"{owner.address_line1 or ''}, {owner.city or ''}, {owner.state or ''} {owner.zip_code or ''}".strip(
                ", "
            ),
        }

        # Generate PDF
        generator = HealthCertificateGenerator()
        pdf_buffer = generator.generate(patient_data, exam_data_formatted, owner_data)

        # Return PDF file
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"health_certificate_{patient.name}_{cert_number}.pdf",
        )

    except Exception as e:
        app.logger.error(f"Error generating health certificate: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/pdf/medical-record-summary/<int:patient_id>", methods=["GET"])
@login_required
def generate_medical_record_summary(patient_id):
    """
    Generate a comprehensive medical record summary PDF
    Returns PDF file for download
    """
    try:
        # Get patient and owner
        patient = Patient.query.get_or_404(patient_id)
        owner = Client.query.get_or_404(patient.owner_id)

        # Calculate age
        age = "N/A"
        if patient.date_of_birth:
            from datetime import datetime

            today = datetime.now().date()
            age_years = (today - patient.date_of_birth).days // 365
            age = f"{age_years} years"

        # Prepare patient data
        patient_data = {
            "id": patient.id,
            "name": patient.name,
            "breed": patient.breed,
            "color": patient.color,
            "sex": patient.sex,
            "reproductive_status": patient.reproductive_status or "N/A",
            "date_of_birth": (patient.date_of_birth.strftime("%m/%d/%Y") if patient.date_of_birth else "N/A"),
            "age": age,
            "microchip_number": patient.microchip_number or "N/A",
            "weight": patient.weight or "N/A",
            "allergies": patient.allergies or "None",
            "medical_conditions": patient.special_needs or "None",
        }

        owner_data = {
            "name": f"{owner.first_name} {owner.last_name}",
            "phone": owner.phone_primary,
            "email": owner.email or "N/A",
            "address": f"{owner.address_line1 or ''}, {owner.city or ''}, {owner.state or ''} {owner.zip_code or ''}".strip(
                ", "
            ),
        }

        # Get vaccination history (most recent 10)
        vaccinations = (
            Vaccination.query.filter_by(patient_id=patient_id)
            .order_by(Vaccination.administered_date.desc())
            .limit(10)
            .all()
        )

        vaccinations_data = [
            {
                "administered_date": (v.administered_date.strftime("%m/%d/%Y") if v.administered_date else "N/A"),
                "vaccine_name": v.vaccine_name,
                "manufacturer": v.manufacturer or "N/A",
                "next_due_date": v.next_due_date.strftime("%m/%d/%Y") if v.next_due_date else "N/A",
            }
            for v in vaccinations
        ]

        # Get visit history (most recent 5)
        visits = Visit.query.filter_by(patient_id=patient_id).order_by(Visit.visit_date.desc()).limit(5).all()

        visits_data = []
        for visit in visits:
            soap_note = SOAPNote.query.filter_by(visit_id=visit.id).first()

            visits_data.append(
                {
                    "visit_date": (visit.visit_date.strftime("%m/%d/%Y") if visit.visit_date else "N/A"),
                    "visit_type": visit.visit_type or "N/A",
                    "chief_complaint": soap_note.subjective if soap_note else "N/A",
                    "diagnosis": soap_note.assessment if soap_note else "N/A",
                    "treatment": soap_note.plan if soap_note else "N/A",
                }
            )

        # Generate PDF
        generator = MedicalRecordSummaryGenerator()
        pdf_buffer = generator.generate(patient_data, owner_data, visits_data, vaccinations_data)

        # Return PDF file
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"medical_record_summary_{patient.name}_{patient.id}.pdf",
        )

    except Exception as e:
        app.logger.error(f"Error generating medical record summary: {str(e)}", exc_info=True)
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
            query = query.filter(db.or_(Product.name.ilike(f"%{search}%"), Product.sku.ilike(f"%{search}%")))

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
        products = (
            Product.query.filter(Product.is_active == True, Product.stock_quantity <= Product.reorder_level)
            .order_by(Product.stock_quantity)
            .all()
        )

        return jsonify({"products": [p.to_dict() for p in products], "total": len(products)}), 200

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
                    performed_by_id=current_user.id,
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
        return (
            jsonify({"transactions": [t.to_dict() for t in transactions], "total": len(transactions)}),
            200,
        )

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
        validated_data = inventory_transaction_schema.load(
            {
                **data,
                "quantity_before": quantity_before,
                "quantity_after": quantity_after,
                "performed_by_id": current_user.id,
            }
        )

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
            Staff.email.ilike(f"%{search}%"),
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
                LabTest.description.ilike(search_term),
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
# Phase 3.5 - Client Portal Routes
# ============================================================================


# Client Portal Authentication
@bp.route("/api/portal/register", methods=["POST"])
@limiter.limit("5 per hour")
def portal_register():
    """Register a new client portal user"""
    try:
        data = client_portal_user_registration_schema.load(request.json)

        # Verify passwords match
        if data["password"] != data["password_confirm"]:
            return jsonify({"error": "Passwords do not match"}), 400

        # Verify client exists
        client = Client.query.get(data["client_id"])
        if not client:
            return jsonify({"error": "Client not found"}), 404

        # Check if client already has a portal account
        existing = ClientPortalUser.query.filter_by(client_id=data["client_id"]).first()
        if existing:
            return jsonify({"error": "Portal account already exists for this client"}), 400

        # Check if username/email already taken
        if ClientPortalUser.query.filter_by(username=data["username"]).first():
            return jsonify({"error": "Username already taken"}), 400
        if ClientPortalUser.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already registered"}), 400

        # Create portal user
        portal_user = ClientPortalUser(
            client_id=data["client_id"],
            username=data["username"],
            email=data["email"],
            is_verified=False,  # Require email verification
        )
        portal_user.set_password(data["password"])

        # Generate email verification token
        portal_user.verification_token = generate_verification_token()
        portal_user.reset_token_expiry = datetime.utcnow() + timedelta(hours=24)  # Token valid for 24 hours

        db.session.add(portal_user)
        db.session.commit()

        # Send verification email
        send_verification_email(portal_user.email, portal_user.verification_token, portal_user.username)

        app.logger.info(f"Client portal user registered: {portal_user.username}")
        return (
            jsonify(
                {
                    "message": "Registration successful! Please check your email to verify your account.",
                    "user": {"id": portal_user.id, "username": portal_user.username},
                    "requires_verification": True,
                }
            ),
            201,
        )

    except MarshmallowValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error registering portal user: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/portal/login", methods=["POST"])
@limiter.limit("10 per 5 minutes")
def portal_login():
    """Login to client portal"""
    try:
        data = client_portal_user_login_schema.load(request.json)

        # Find user by username or email
        portal_user = ClientPortalUser.query.filter(
            (ClientPortalUser.username == data["username"]) | (ClientPortalUser.email == data["username"])
        ).first()

        if not portal_user or not portal_user.check_password(data["password"]):
            return jsonify({"error": "Invalid username/email or password"}), 401

        # Check if account is active
        if not portal_user.is_active:
            return jsonify({"error": "Account is inactive"}), 403

        # Check if email is verified (Phase 3.6 security requirement)
        if not portal_user.is_verified:
            return (
                jsonify(
                    {
                        "error": "Email not verified. Please check your email for verification link.",
                        "requires_verification": True,
                    }
                ),
                403,
            )

        # Check if account is locked
        if portal_user.account_locked_until and portal_user.account_locked_until > datetime.utcnow():
            return jsonify({"error": "Account is locked. Please try again later"}), 403

        # Update login tracking
        portal_user.last_login = datetime.utcnow()
        portal_user.failed_login_attempts = 0
        portal_user.account_locked_until = None

        # Set session management (8-hour session)
        portal_user.session_expires_at = datetime.utcnow() + timedelta(hours=8)
        portal_user.last_activity_at = datetime.utcnow()

        db.session.commit()

        # Generate JWT token
        token = generate_portal_token(portal_user)

        # Get client info
        client = Client.query.get(portal_user.client_id)

        app.logger.info(f"Client portal login: {portal_user.username}")
        return (
            jsonify(
                {
                    "message": "Login successful",
                    "token": token,  # JWT token for authentication
                    "user": {
                        "id": portal_user.id,
                        "username": portal_user.username,
                        "email": portal_user.email,
                        "client_id": portal_user.client_id,
                        "client_name": (f"{client.first_name} {client.last_name}" if client else None),
                        "has_pin": portal_user.pin_hash is not None,
                    },
                }
            ),
            200,
        )

    except MarshmallowValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        app.logger.error(f"Error during portal login: {str(e)}", exc_info=True)
        return jsonify({"error": "Login failed"}), 400


@bp.route("/api/portal/dashboard/<int:client_id>", methods=["GET"])
@portal_auth_required
def portal_dashboard(client_id, **kwargs):
    """Get client portal dashboard data"""
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({"error": "Client not found"}), 404

        # Get client's patients
        patients = Patient.query.filter_by(owner_id=client_id, status="Active").all()

        # Get upcoming appointments (next 30 days)
        from datetime import timedelta

        upcoming_appointments = (
            Appointment.query.filter(
                Appointment.client_id == client_id,
                Appointment.start_time >= datetime.utcnow(),
                Appointment.start_time <= datetime.utcnow() + timedelta(days=30),
                Appointment.status.in_(["scheduled", "confirmed"]),
            )
            .order_by(Appointment.start_time)
            .limit(5)
            .all()
        )

        # Get recent invoices
        recent_invoices = (
            Invoice.query.filter_by(client_id=client_id).order_by(Invoice.invoice_date.desc()).limit(5).all()
        )

        # Get pending appointment requests
        pending_requests = (
            AppointmentRequest.query.filter_by(client_id=client_id, status="pending")
            .order_by(AppointmentRequest.created_at.desc())
            .all()
        )

        return (
            jsonify(
                {
                    "client": client_schema.dump(client),
                    "patients": patients_schema.dump(patients),
                    "upcoming_appointments": [
                        {
                            "id": apt.id,
                            "title": apt.title,
                            "start_time": apt.start_time.isoformat() if apt.start_time else None,
                            "end_time": apt.end_time.isoformat() if apt.end_time else None,
                            "status": apt.status,
                            "patient_id": apt.patient_id,
                        }
                        for apt in upcoming_appointments
                    ],
                    "recent_invoices": [
                        {
                            "id": inv.id,
                            "invoice_number": inv.invoice_number,
                            "invoice_date": (inv.invoice_date.isoformat() if inv.invoice_date else None),
                            "total_amount": str(inv.total_amount),
                            "balance_due": str(inv.balance_due),
                            "status": inv.status,
                        }
                        for inv in recent_invoices
                    ],
                    "pending_requests": appointment_requests_schema.dump(pending_requests),
                    "account_balance": (str(client.account_balance) if client.account_balance else "0.00"),
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Error fetching dashboard data: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/portal/patients/<int:client_id>", methods=["GET"])
@portal_auth_required
def portal_patients(client_id, **kwargs):
    """Get all patients for a client"""
    try:
        patients = Patient.query.filter_by(owner_id=client_id, status="Active").all()
        return jsonify(patients_schema.dump(patients)), 200
    except Exception as e:
        app.logger.error(f"Error fetching patients: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/portal/patients/<int:client_id>/<int:patient_id>", methods=["GET"])
@portal_auth_required
def portal_patient_detail(client_id, patient_id, **kwargs):
    """Get patient details (read-only for portal)"""
    try:
        patient = Patient.query.filter_by(id=patient_id, owner_id=client_id).first()
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        return jsonify(patient_schema.dump(patient)), 200
    except Exception as e:
        app.logger.error(f"Error fetching patient details: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/portal/appointments/<int:client_id>", methods=["GET"])
@portal_auth_required
def portal_appointments(client_id, **kwargs):
    """Get appointment history for client"""
    try:
        # Get all appointments for client's patients
        appointments = Appointment.query.filter_by(client_id=client_id).order_by(Appointment.start_time.desc()).all()

        result = []
        for apt in appointments:
            apt_data = {
                "id": apt.id,
                "title": apt.title,
                "start_time": apt.start_time.isoformat() if apt.start_time else None,
                "end_time": apt.end_time.isoformat() if apt.end_time else None,
                "status": apt.status,
                "patient_id": apt.patient_id,
                "description": apt.description,
            }
            result.append(apt_data)

        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error fetching appointments: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/portal/invoices/<int:client_id>", methods=["GET"])
@portal_auth_required
def portal_invoices(client_id, **kwargs):
    """Get invoice history for client"""
    try:
        invoices = Invoice.query.filter_by(client_id=client_id).order_by(Invoice.invoice_date.desc()).all()

        result = []
        for inv in invoices:
            inv_data = {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "total_amount": str(inv.total_amount),
                "amount_paid": str(inv.amount_paid),
                "balance_due": str(inv.balance_due),
                "status": inv.status,
                "patient_id": inv.patient_id,
            }
            result.append(inv_data)

        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error fetching invoices: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/portal/invoices/<int:client_id>/<int:invoice_id>", methods=["GET"])
@portal_auth_required
def portal_invoice_detail(client_id, invoice_id, **kwargs):
    """Get specific invoice details"""
    try:
        invoice = Invoice.query.filter_by(id=invoice_id, client_id=client_id).first()
        if not invoice:
            return jsonify({"error": "Invoice not found"}), 404

        # Get invoice items
        items = InvoiceItem.query.filter_by(invoice_id=invoice_id).all()

        return (
            jsonify(
                {
                    "invoice": {
                        "id": invoice.id,
                        "invoice_number": invoice.invoice_number,
                        "invoice_date": (invoice.invoice_date.isoformat() if invoice.invoice_date else None),
                        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                        "subtotal": str(invoice.subtotal),
                        "tax_amount": str(invoice.tax_amount),
                        "discount_amount": str(invoice.discount_amount),
                        "total_amount": str(invoice.total_amount),
                        "amount_paid": str(invoice.amount_paid),
                        "balance_due": str(invoice.balance_due),
                        "status": invoice.status,
                        "notes": invoice.notes,
                    },
                    "items": [
                        {
                            "description": item.description,
                            "quantity": str(item.quantity),
                            "unit_price": str(item.unit_price),
                            "total_price": str(item.total_price),
                        }
                        for item in items
                    ],
                }
            ),
            200,
        )
    except Exception as e:
        app.logger.error(f"Error fetching invoice details: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


# Appointment Requests
@bp.route("/api/portal/appointment-requests", methods=["POST"])
@portal_auth_required
def create_appointment_request(**kwargs):
    """Create a new appointment request from client portal"""
    try:
        data = appointment_request_create_schema.load(request.json)

        # Ensure the authenticated user can only create requests for themselves
        authenticated_client_id = kwargs.get("authenticated_client_id")
        if data["client_id"] != authenticated_client_id:
            return (
                jsonify({"error": "Unauthorized: You can only create requests for yourself"}),
                403,
            )

        # Verify client and patient exist and are linked
        client = Client.query.get(data["client_id"])
        if not client:
            return jsonify({"error": "Client not found"}), 404

        patient = Patient.query.filter_by(id=data["patient_id"], owner_id=data["client_id"]).first()
        if not patient:
            return jsonify({"error": "Patient not found or does not belong to this client"}), 404

        # Create appointment request
        apt_request = AppointmentRequest(
            client_id=data["client_id"],
            patient_id=data["patient_id"],
            appointment_type_id=data.get("appointment_type_id"),
            requested_date=data["requested_date"],
            requested_time=data.get("requested_time"),
            alternate_date_1=data.get("alternate_date_1"),
            alternate_date_2=data.get("alternate_date_2"),
            reason=data["reason"],
            is_urgent=data.get("is_urgent", False),
            notes=data.get("notes"),
            status="pending",
            priority="urgent" if data.get("is_urgent") else "normal",
        )

        db.session.add(apt_request)
        db.session.commit()

        app.logger.info(f"Appointment request created by client {data['client_id']}")

        # Return full data with related info
        result = apt_request.to_dict()
        result["client_name"] = f"{client.first_name} {client.last_name}"
        result["patient_name"] = patient.name

        return jsonify(result), 201

    except MarshmallowValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating appointment request: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/portal/appointment-requests/<int:client_id>", methods=["GET"])
@portal_auth_required
def get_client_appointment_requests(client_id, **kwargs):
    """Get all appointment requests for a client"""
    try:
        requests = (
            AppointmentRequest.query.filter_by(client_id=client_id).order_by(AppointmentRequest.created_at.desc()).all()
        )

        result = []
        for req in requests:
            req_data = req.to_dict()

            # Add related names
            client = Client.query.get(req.client_id)
            req_data["client_name"] = f"{client.first_name} {client.last_name}" if client else None

            patient = Patient.query.get(req.patient_id)
            req_data["patient_name"] = patient.name if patient else None

            if req.appointment_type_id:
                apt_type = AppointmentType.query.get(req.appointment_type_id)
                req_data["appointment_type_name"] = apt_type.name if apt_type else None

            result.append(req_data)

        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error fetching appointment requests: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/portal/appointment-requests/<int:client_id>/<int:request_id>", methods=["GET"])
@portal_auth_required
def get_appointment_request_detail(client_id, request_id, **kwargs):
    """Get specific appointment request details"""
    try:
        req = AppointmentRequest.query.filter_by(id=request_id, client_id=client_id).first()
        if not req:
            return jsonify({"error": "Appointment request not found"}), 404

        req_data = req.to_dict()

        # Add related names
        client = Client.query.get(req.client_id)
        req_data["client_name"] = f"{client.first_name} {client.last_name}" if client else None

        patient = Patient.query.get(req.patient_id)
        req_data["patient_name"] = patient.name if patient else None

        if req.appointment_type_id:
            apt_type = AppointmentType.query.get(req.appointment_type_id)
            req_data["appointment_type_name"] = apt_type.name if apt_type else None

        return jsonify(req_data), 200
    except Exception as e:
        app.logger.error(f"Error fetching appointment request: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/portal/appointment-requests/<int:client_id>/<int:request_id>/cancel", methods=["POST"])
@portal_auth_required
def cancel_appointment_request(client_id, request_id, **kwargs):
    """Cancel a pending appointment request"""
    try:
        req = AppointmentRequest.query.filter_by(id=request_id, client_id=client_id).first()
        if not req:
            return jsonify({"error": "Appointment request not found"}), 404

        if req.status != "pending":
            return jsonify({"error": "Can only cancel pending requests"}), 400

        req.status = "cancelled"
        db.session.commit()

        app.logger.info(f"Appointment request {request_id} cancelled by client {client_id}")
        return jsonify(req.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error cancelling appointment request: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


# Email Verification Endpoints
@bp.route("/api/portal/verify-email", methods=["POST"])
def verify_email():
    """Verify user email with token"""
    try:
        token = request.json.get("token")
        if not token:
            return jsonify({"error": "Verification token required"}), 400

        # Find user by verification token
        portal_user = ClientPortalUser.query.filter_by(verification_token=token).first()

        if not portal_user:
            return jsonify({"error": "Invalid verification token"}), 400

        # Check if token is still valid (24 hours)
        if not is_token_valid(portal_user.reset_token_expiry):
            return jsonify({"error": "Verification token expired. Please request a new one."}), 400

        # Verify the account
        portal_user.is_verified = True
        portal_user.verification_token = None
        portal_user.reset_token_expiry = None
        db.session.commit()

        app.logger.info(f"Email verified for user: {portal_user.username}")
        return jsonify({"message": "Email verified successfully! You can now log in."}), 200

    except Exception as e:
        app.logger.error(f"Error verifying email: {str(e)}", exc_info=True)
        return jsonify({"error": "Verification failed"}), 400


@bp.route("/api/portal/resend-verification", methods=["POST"])
@limiter.limit("3 per hour")
def resend_verification():
    """Resend verification email"""
    try:
        email = request.json.get("email")
        if not email:
            return jsonify({"error": "Email required"}), 400

        portal_user = ClientPortalUser.query.filter_by(email=email).first()

        if not portal_user:
            # Don't reveal if email exists for security
            return (
                jsonify({"message": "If the email exists, a verification link has been sent."}),
                200,
            )

        if portal_user.is_verified:
            return jsonify({"error": "Email already verified"}), 400

        # Generate new token
        portal_user.verification_token = generate_verification_token()
        portal_user.reset_token_expiry = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()

        # Send verification email
        send_verification_email(portal_user.email, portal_user.verification_token, portal_user.username)

        app.logger.info(f"Verification email resent to: {email}")
        return jsonify({"message": "Verification email sent. Please check your inbox."}), 200

    except Exception as e:
        app.logger.error(f"Error resending verification: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to send verification email"}), 400


@bp.route("/api/portal/set-pin", methods=["POST"])
@portal_auth_required
def portal_set_pin():
    """Set or update PIN for quick re-authentication"""
    try:
        # Get authenticated user from token
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        payload = verify_portal_token(token)

        if not payload:
            return jsonify({"error": "Invalid token"}), 401

        portal_user = ClientPortalUser.query.get(payload["portal_user_id"])
        if not portal_user:
            return jsonify({"error": "User not found"}), 404

        # Get PIN from request
        pin = request.json.get("pin")
        if not pin:
            return jsonify({"error": "PIN required"}), 400

        # Validate and set PIN
        try:
            portal_user.set_pin(pin)
            db.session.commit()

            app.logger.info(f"PIN set for portal user: {portal_user.username}")
            return jsonify({"message": "PIN set successfully"}), 200

        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    except Exception as e:
        app.logger.error(f"Error setting PIN: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to set PIN"}), 400


@bp.route("/api/portal/verify-pin", methods=["POST"])
@portal_auth_required
def portal_verify_pin():
    """Verify PIN to unlock session after idle timeout"""
    try:
        # Get authenticated user from token
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        payload = verify_portal_token(token)

        if not payload:
            return jsonify({"error": "Invalid token"}), 401

        portal_user = ClientPortalUser.query.get(payload["portal_user_id"])
        if not portal_user:
            return jsonify({"error": "User not found"}), 404

        # Check if session has expired (8 hours)
        if portal_user.session_expires_at and portal_user.session_expires_at < datetime.utcnow():
            return (
                jsonify({"error": "Session expired. Please log in again.", "session_expired": True}),
                401,
            )

        # Get PIN from request
        pin = request.json.get("pin")
        if not pin:
            return jsonify({"error": "PIN required"}), 400

        # Verify PIN
        if not portal_user.check_pin(pin):
            return jsonify({"error": "Invalid PIN"}), 401

        # Update last activity
        portal_user.last_activity_at = datetime.utcnow()
        db.session.commit()

        app.logger.info(f"PIN verified for portal user: {portal_user.username}")
        return (
            jsonify(
                {
                    "message": "PIN verified successfully",
                    "user": {
                        "id": portal_user.id,
                        "username": portal_user.username,
                        "client_id": portal_user.client_id,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Error verifying PIN: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to verify PIN"}), 400


@bp.route("/api/portal/check-session", methods=["GET"])
@portal_auth_required
def portal_check_session():
    """Check if session is active and if PIN is required"""
    try:
        # Get authenticated user from token
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        payload = verify_portal_token(token)

        if not payload:
            return jsonify({"error": "Invalid token"}), 401

        portal_user = ClientPortalUser.query.get(payload["portal_user_id"])
        if not portal_user:
            return jsonify({"error": "User not found"}), 404

        # Check if session has expired (8 hours)
        if portal_user.session_expires_at and portal_user.session_expires_at < datetime.utcnow():
            return (
                jsonify(
                    {
                        "session_expired": True,
                        "requires_login": True,
                        "message": "Session expired. Please log in again.",
                    }
                ),
                200,
            )

        # Check if idle timeout has occurred (15 minutes)
        requires_pin = False
        if portal_user.last_activity_at:
            idle_time = datetime.utcnow() - portal_user.last_activity_at
            if idle_time.total_seconds() > 900:  # 15 minutes
                requires_pin = True

        # Update activity if no PIN required
        if not requires_pin:
            portal_user.last_activity_at = datetime.utcnow()
            db.session.commit()

        return (
            jsonify(
                {
                    "session_expired": False,
                    "requires_pin": requires_pin,
                    "has_pin": portal_user.pin_hash is not None,
                    "requires_login": False,
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Error checking session: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to check session"}), 400


# Staff-side Appointment Request Management
@bp.route("/api/appointment-requests", methods=["GET"])
@login_required
def get_all_appointment_requests():
    """Get all appointment requests (staff view)"""
    try:
        # Get filter parameters
        status = request.args.get("status")
        priority = request.args.get("priority")

        query = AppointmentRequest.query

        if status:
            query = query.filter_by(status=status)
        if priority:
            query = query.filter_by(priority=priority)

        requests = query.order_by(AppointmentRequest.priority.desc(), AppointmentRequest.created_at).all()

        result = []
        for req in requests:
            req_data = req.to_dict()

            # Add related names
            client = Client.query.get(req.client_id)
            req_data["client_name"] = f"{client.first_name} {client.last_name}" if client else None

            patient = Patient.query.get(req.patient_id)
            req_data["patient_name"] = patient.name if patient else None

            if req.appointment_type_id:
                apt_type = AppointmentType.query.get(req.appointment_type_id)
                req_data["appointment_type_name"] = apt_type.name if apt_type else None

            if req.reviewed_by_id:
                reviewer = User.query.get(req.reviewed_by_id)
                req_data["reviewed_by_name"] = reviewer.username if reviewer else None

            result.append(req_data)

        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error fetching appointment requests: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/appointment-requests/<int:request_id>", methods=["GET"])
@login_required
def get_appointment_request(request_id):
    """Get specific appointment request (staff view)"""
    try:
        req = AppointmentRequest.query.get(request_id)
        if not req:
            return jsonify({"error": "Appointment request not found"}), 404

        req_data = req.to_dict()

        # Add related names
        client = Client.query.get(req.client_id)
        req_data["client_name"] = f"{client.first_name} {client.last_name}" if client else None

        patient = Patient.query.get(req.patient_id)
        req_data["patient_name"] = patient.name if patient else None

        if req.appointment_type_id:
            apt_type = AppointmentType.query.get(req.appointment_type_id)
            req_data["appointment_type_name"] = apt_type.name if apt_type else None

        if req.reviewed_by_id:
            reviewer = User.query.get(req.reviewed_by_id)
            req_data["reviewed_by_name"] = reviewer.username if reviewer else None

        return jsonify(req_data), 200
    except Exception as e:
        app.logger.error(f"Error fetching appointment request: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/appointment-requests/<int:request_id>/review", methods=["PUT"])
@login_required
def review_appointment_request(request_id):
    """Review/approve/reject an appointment request (staff only)"""
    try:
        req = AppointmentRequest.query.get(request_id)
        if not req:
            return jsonify({"error": "Appointment request not found"}), 404

        data = appointment_request_review_schema.load(request.json)

        # Update request
        req.status = data["status"]
        if "priority" in data:
            req.priority = data["priority"]
        if "staff_notes" in data:
            req.staff_notes = data["staff_notes"]
        if "rejection_reason" in data:
            req.rejection_reason = data["rejection_reason"]
        if "appointment_id" in data:
            req.appointment_id = data["appointment_id"]

        req.reviewed_by_id = current_user.id
        req.reviewed_at = datetime.utcnow()

        db.session.commit()

        app.logger.info(f"Appointment request {request_id} reviewed by {current_user.username}: {data['status']}")
        return jsonify(req.to_dict()), 200

    except MarshmallowValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error reviewing appointment request: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


# ============================================================================
# DOCUMENT MANAGEMENT ROUTES
# ============================================================================


def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config.get("ALLOWED_EXTENSIONS", set())


@bp.route("/api/documents", methods=["POST"])
@login_required
def upload_document():
    """
    Upload a new document
    Expects multipart/form-data with:
    - file: The document file
    - category: Document category
    - patient_id: (optional) Patient ID
    - visit_id: (optional) Visit ID
    - client_id: (optional) Client ID
    - description: (optional) Document description
    - tags: (optional) Comma-separated tags
    - is_consent_form: (optional) Boolean
    - consent_type: (optional) Consent form type
    - signed_date: (optional) Signed date
    """
    try:
        # Check if file is present
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400

        # Get form data
        category = request.form.get("category", "general")
        patient_id = request.form.get("patient_id", type=int)
        visit_id = request.form.get("visit_id", type=int)
        client_id = request.form.get("client_id", type=int)
        description = request.form.get("description")
        tags = request.form.get("tags")
        is_consent_form = request.form.get("is_consent_form", "false").lower() == "true"
        consent_type = request.form.get("consent_type")
        signed_date_str = request.form.get("signed_date")

        # Validate at least one relationship is provided
        if not patient_id and not visit_id and not client_id:
            return jsonify({"error": "Document must be linked to a patient, visit, or client"}), 400

        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit(".", 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"

        # Save file
        upload_folder = app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)

        # Get file size
        file_size = os.path.getsize(file_path)

        # Parse signed date if provided
        signed_date = None
        if signed_date_str:
            try:
                signed_date = datetime.fromisoformat(signed_date_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Create document record
        document = Document(
            filename=unique_filename,
            original_filename=original_filename,
            file_path=file_path,
            file_type=file.content_type or "application/octet-stream",
            file_size=file_size,
            category=category,
            tags=tags,
            description=description,
            is_consent_form=is_consent_form,
            consent_type=consent_type if is_consent_form else None,
            signed_date=signed_date,
            patient_id=patient_id,
            visit_id=visit_id,
            client_id=client_id,
            uploaded_by_id=current_user.id,
        )

        db.session.add(document)
        db.session.commit()

        app.logger.info(f"Document uploaded: {original_filename} (ID: {document.id}) by {current_user.username}")

        return jsonify(document.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/documents", methods=["GET"])
@login_required
def get_documents():
    """
    Get list of documents with optional filtering
    Query params:
        - page: Page number (default 1)
        - per_page: Items per page (default 50)
        - patient_id: Filter by patient
        - visit_id: Filter by visit
        - client_id: Filter by client
        - category: Filter by category
        - is_consent_form: Filter consent forms (true/false)
        - is_archived: Include archived documents (true/false, default false)
        - search: Search in filename or description
    """
    try:
        # Get query parameters
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        patient_id = request.args.get("patient_id", type=int)
        visit_id = request.args.get("visit_id", type=int)
        client_id = request.args.get("client_id", type=int)
        category = request.args.get("category")
        is_consent_form = request.args.get("is_consent_form")
        is_archived = request.args.get("is_archived", "false").lower() == "true"
        search = request.args.get("search", "").strip()

        # Build query
        query = Document.query

        # Apply filters
        if patient_id:
            query = query.filter_by(patient_id=patient_id)
        if visit_id:
            query = query.filter_by(visit_id=visit_id)
        if client_id:
            query = query.filter_by(client_id=client_id)
        if category:
            query = query.filter_by(category=category)
        if is_consent_form is not None:
            consent_bool = is_consent_form.lower() == "true"
            query = query.filter_by(is_consent_form=consent_bool)
        if not is_archived:
            query = query.filter_by(is_archived=False)

        # Search in filename or description
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Document.original_filename.ilike(search_pattern),
                    Document.description.ilike(search_pattern),
                )
            )

        # Order by creation date (newest first)
        query = query.order_by(Document.created_at.desc())

        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "documents": [doc.to_dict() for doc in paginated.items],
                    "total": paginated.total,
                    "pages": paginated.pages,
                    "current_page": page,
                    "per_page": per_page,
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Error fetching documents: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/documents/<int:document_id>", methods=["GET"])
@login_required
def get_document(document_id):
    """Get a specific document's metadata by ID"""
    try:
        document = Document.query.get_or_404(document_id)
        return jsonify(document.to_dict()), 200
    except Exception as e:
        app.logger.error(f"Error getting document {document_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Document not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/documents/<int:document_id>/download", methods=["GET"])
@login_required
def download_document(document_id):
    """Download a document file"""
    try:
        document = Document.query.get_or_404(document_id)

        # Check if file exists
        if not os.path.exists(document.file_path):
            app.logger.error(f"Document file not found: {document.file_path}")
            return jsonify({"error": "Document file not found on server"}), 404

        app.logger.info(
            f"Document downloaded: {document.original_filename} (ID: {document_id}) by {current_user.username}"
        )

        return send_file(
            document.file_path,
            mimetype=document.file_type,
            as_attachment=True,
            download_name=document.original_filename,
        )

    except Exception as e:
        app.logger.error(f"Error downloading document {document_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Document not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/documents/<int:document_id>", methods=["PUT"])
@login_required
def update_document(document_id):
    """Update document metadata (file cannot be changed)"""
    try:
        document = Document.query.get_or_404(document_id)
        data = document_update_schema.load(request.get_json())

        # Update fields
        if "category" in data:
            document.category = data["category"]
        if "tags" in data:
            document.tags = ",".join(data["tags"]) if data["tags"] else None
        if "description" in data:
            document.description = data["description"]
        if "notes" in data:
            document.notes = data["notes"]
        if "is_consent_form" in data:
            document.is_consent_form = data["is_consent_form"]
        if "consent_type" in data:
            document.consent_type = data["consent_type"]
        if "signed_date" in data:
            document.signed_date = data["signed_date"]
        if "patient_id" in data:
            document.patient_id = data["patient_id"]
        if "visit_id" in data:
            document.visit_id = data["visit_id"]
        if "client_id" in data:
            document.client_id = data["client_id"]
        if "is_archived" in data:
            document.is_archived = data["is_archived"]

        db.session.commit()

        app.logger.info(
            f"Document updated: {document.original_filename} (ID: {document_id}) by {current_user.username}"
        )

        return jsonify(document.to_dict()), 200

    except MarshmallowValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating document {document_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Document not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/documents/<int:document_id>", methods=["DELETE"])
@login_required
def delete_document(document_id):
    """Delete a document (soft delete - archive by default, hard delete with force=true)"""
    try:
        document = Document.query.get_or_404(document_id)
        force_delete = request.args.get("force", "false").lower() == "true"

        if force_delete:
            # Hard delete - remove file and database record
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
                app.logger.info(f"Document file deleted: {document.file_path}")

            db.session.delete(document)
            db.session.commit()

            app.logger.info(
                f"Document permanently deleted: {document.original_filename} (ID: {document_id}) by {current_user.username}"
            )

            return jsonify({"message": "Document permanently deleted"}), 200
        else:
            # Soft delete - archive
            document.is_archived = True
            db.session.commit()

            app.logger.info(
                f"Document archived: {document.original_filename} (ID: {document_id}) by {current_user.username}"
            )

            return jsonify({"message": "Document archived", "document": document.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting document {document_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Document not found"}), 404
        return jsonify({"error": str(e)}), 400


# ============================================================================
# Phase 4.2: Treatment Plans & Protocols API Endpoints
# ============================================================================


@bp.route("/api/protocols", methods=["GET"])
@login_required
def get_protocols():
    """Get list of all protocols with optional filtering"""
    try:
        # Query parameters
        category = request.args.get("category")
        is_active = request.args.get("is_active")
        search = request.args.get("search")

        query = Protocol.query

        # Apply filters
        if category:
            query = query.filter(Protocol.category == category)

        if is_active is not None:
            active_bool = is_active.lower() == "true"
            query = query.filter(Protocol.is_active == active_bool)

        if search:
            search_term = f"%{search}%"
            query = query.filter(db.or_(Protocol.name.ilike(search_term), Protocol.description.ilike(search_term)))

        protocols = query.order_by(Protocol.name).all()
        return jsonify([p.to_dict() for p in protocols]), 200

    except Exception as e:
        app.logger.error(f"Error fetching protocols: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/protocols/<int:protocol_id>", methods=["GET"])
@login_required
def get_protocol(protocol_id):
    """Get a single protocol with steps"""
    try:
        protocol = Protocol.query.get_or_404(protocol_id)
        return jsonify(protocol.to_dict(include_steps=True)), 200

    except Exception as e:
        app.logger.error(f"Error fetching protocol {protocol_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Protocol not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/protocols", methods=["POST"])
@login_required
def create_protocol():
    """Create a new protocol with steps"""
    try:
        data = protocol_create_schema.load(request.json)

        # Create protocol
        protocol = Protocol(
            name=data["name"],
            description=data.get("description"),
            category=data.get("category"),
            is_active=data.get("is_active", True),
            default_duration_days=data.get("default_duration_days"),
            estimated_cost=data.get("estimated_cost"),
            notes=data.get("notes"),
            created_by_id=current_user.id,
        )

        db.session.add(protocol)
        db.session.flush()  # Get protocol ID

        # Create protocol steps
        steps_data = data.get("steps", [])
        for step_data in steps_data:
            step = ProtocolStep(
                protocol_id=protocol.id,
                step_number=step_data["step_number"],
                title=step_data["title"],
                description=step_data.get("description"),
                day_offset=step_data.get("day_offset", 0),
                estimated_cost=step_data.get("estimated_cost"),
                notes=step_data.get("notes"),
            )
            db.session.add(step)

        db.session.commit()

        app.logger.info(f"Protocol created: {protocol.name} (ID: {protocol.id}) by {current_user.username}")

        return jsonify(protocol.to_dict(include_steps=True)), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating protocol: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/protocols/<int:protocol_id>", methods=["PUT"])
@login_required
def update_protocol(protocol_id):
    """Update a protocol (does not update steps - use separate endpoint)"""
    try:
        protocol = Protocol.query.get_or_404(protocol_id)
        data = protocol_update_schema.load(request.json)

        # Update fields
        if "name" in data:
            protocol.name = data["name"]
        if "description" in data:
            protocol.description = data["description"]
        if "category" in data:
            protocol.category = data["category"]
        if "is_active" in data:
            protocol.is_active = data["is_active"]
        if "default_duration_days" in data:
            protocol.default_duration_days = data["default_duration_days"]
        if "estimated_cost" in data:
            protocol.estimated_cost = data["estimated_cost"]
        if "notes" in data:
            protocol.notes = data["notes"]

        db.session.commit()

        app.logger.info(f"Protocol updated: {protocol.name} (ID: {protocol_id}) by {current_user.username}")

        return jsonify(protocol.to_dict(include_steps=True)), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating protocol {protocol_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Protocol not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/protocols/<int:protocol_id>", methods=["DELETE"])
@login_required
def delete_protocol(protocol_id):
    """Delete a protocol (soft delete by default, hard delete with ?permanent=true)"""
    try:
        protocol = Protocol.query.get_or_404(protocol_id)
        permanent = request.args.get("permanent", "false").lower() == "true"

        if permanent:
            # Hard delete - remove from database
            db.session.delete(protocol)
            db.session.commit()

            app.logger.info(
                f"Protocol permanently deleted: {protocol.name} (ID: {protocol_id}) by {current_user.username}"
            )

            return jsonify({"message": "Protocol permanently deleted"}), 200
        else:
            # Soft delete - mark as inactive
            protocol.is_active = False
            db.session.commit()

            app.logger.info(f"Protocol deactivated: {protocol.name} (ID: {protocol_id}) by {current_user.username}")

            return jsonify({"message": "Protocol deactivated", "protocol": protocol.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting protocol {protocol_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Protocol not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/protocols/<int:protocol_id>/apply", methods=["POST"])
@login_required
def apply_protocol_to_patient(protocol_id):
    """Apply a protocol to a patient, creating a new treatment plan"""
    try:
        data = request.json
        patient_id = data.get("patient_id")
        visit_id = data.get("visit_id")
        start_date = data.get("start_date")

        if not patient_id:
            return jsonify({"error": "patient_id is required"}), 400

        # Get protocol with steps
        protocol = Protocol.query.get_or_404(protocol_id)
        patient = Patient.query.get_or_404(patient_id)

        # Create treatment plan from protocol
        treatment_plan = TreatmentPlan(
            name=f"{protocol.name} - {patient.name}",
            description=protocol.description,
            patient_id=patient_id,
            visit_id=visit_id,
            protocol_id=protocol_id,
            status="draft",
            start_date=datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None,
            total_estimated_cost=protocol.estimated_cost or 0,
            created_by_id=current_user.id,
        )

        # Calculate end date from protocol duration
        if treatment_plan.start_date and protocol.default_duration_days:
            treatment_plan.end_date = treatment_plan.start_date + timedelta(days=protocol.default_duration_days)

        db.session.add(treatment_plan)
        db.session.flush()  # Get treatment plan ID

        # Copy protocol steps to treatment plan steps
        protocol_steps = protocol.steps.order_by(ProtocolStep.step_number).all()
        for proto_step in protocol_steps:
            step = TreatmentPlanStep(
                treatment_plan_id=treatment_plan.id,
                step_number=proto_step.step_number,
                title=proto_step.title,
                description=proto_step.description,
                status="pending",
                estimated_cost=proto_step.estimated_cost,
                notes=proto_step.notes,
            )

            # Calculate scheduled date from day offset
            if treatment_plan.start_date:
                step.scheduled_date = treatment_plan.start_date + timedelta(days=proto_step.day_offset)

            db.session.add(step)

        db.session.commit()

        app.logger.info(
            f"Protocol {protocol.name} applied to patient {patient.name} (Treatment Plan ID: {treatment_plan.id}) by {current_user.username}"
        )

        return jsonify(treatment_plan.to_dict(include_steps=True)), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error applying protocol {protocol_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Protocol or patient not found"}), 404
        return jsonify({"error": str(e)}), 400


# ============================================================================
# Treatment Plan Endpoints
# ============================================================================


@bp.route("/api/treatment-plans", methods=["GET"])
@login_required
def get_treatment_plans():
    """Get list of treatment plans with optional filtering"""
    try:
        # Query parameters
        patient_id = request.args.get("patient_id", type=int)
        status = request.args.get("status")
        search = request.args.get("search")

        query = TreatmentPlan.query

        # Apply filters
        if patient_id:
            query = query.filter(TreatmentPlan.patient_id == patient_id)

        if status:
            query = query.filter(TreatmentPlan.status == status)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    TreatmentPlan.name.ilike(search_term),
                    TreatmentPlan.description.ilike(search_term),
                )
            )

        treatment_plans = query.order_by(TreatmentPlan.created_at.desc()).all()
        return jsonify([tp.to_dict() for tp in treatment_plans]), 200

    except Exception as e:
        app.logger.error(f"Error fetching treatment plans: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/treatment-plans/<int:plan_id>", methods=["GET"])
@login_required
def get_treatment_plan(plan_id):
    """Get a single treatment plan with steps"""
    try:
        treatment_plan = TreatmentPlan.query.get_or_404(plan_id)
        return jsonify(treatment_plan.to_dict(include_steps=True)), 200

    except Exception as e:
        app.logger.error(f"Error fetching treatment plan {plan_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Treatment plan not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/treatment-plans", methods=["POST"])
@login_required
def create_treatment_plan():
    """Create a new treatment plan with steps"""
    try:
        data = treatment_plan_create_schema.load(request.json)

        # Validate patient exists
        if data.get("patient_id"):
            patient = Patient.query.get(data["patient_id"])
            if not patient:
                return jsonify({"error": "Patient not found"}), 400

        # Create treatment plan
        treatment_plan = TreatmentPlan(
            name=data["name"],
            description=data.get("description"),
            patient_id=data["patient_id"],
            visit_id=data.get("visit_id"),
            protocol_id=data.get("protocol_id"),
            status=data.get("status", "draft"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            notes=data.get("notes"),
            created_by_id=current_user.id,
        )

        db.session.add(treatment_plan)
        db.session.flush()  # Get treatment plan ID

        # Create treatment plan steps
        steps_data = data.get("steps", [])
        total_estimated = 0
        for step_data in steps_data:
            step = TreatmentPlanStep(
                treatment_plan_id=treatment_plan.id,
                step_number=step_data["step_number"],
                title=step_data["title"],
                description=step_data.get("description"),
                status=step_data.get("status", "pending"),
                scheduled_date=step_data.get("scheduled_date"),
                estimated_cost=step_data.get("estimated_cost"),
                notes=step_data.get("notes"),
            )
            db.session.add(step)

            if step.estimated_cost:
                total_estimated += float(step.estimated_cost)

        # Update total estimated cost
        treatment_plan.total_estimated_cost = total_estimated

        db.session.commit()

        app.logger.info(
            f"Treatment plan created: {treatment_plan.name} (ID: {treatment_plan.id}) by {current_user.username}"
        )

        return jsonify(treatment_plan.to_dict(include_steps=True)), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating treatment plan: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@bp.route("/api/treatment-plans/<int:plan_id>", methods=["PUT"])
@login_required
def update_treatment_plan(plan_id):
    """Update a treatment plan (does not update steps - use separate endpoint)"""
    try:
        treatment_plan = TreatmentPlan.query.get_or_404(plan_id)
        data = treatment_plan_update_schema.load(request.json)

        # Update fields
        if "name" in data:
            treatment_plan.name = data["name"]
        if "description" in data:
            treatment_plan.description = data["description"]
        if "status" in data:
            treatment_plan.status = data["status"]

            # If marking as completed, set completed_date
            if data["status"] == "completed" and not treatment_plan.completed_date:
                treatment_plan.completed_date = datetime.utcnow().date()
        if "start_date" in data:
            treatment_plan.start_date = data["start_date"]
        if "end_date" in data:
            treatment_plan.end_date = data["end_date"]
        if "completed_date" in data:
            treatment_plan.completed_date = data["completed_date"]
        if "total_estimated_cost" in data:
            treatment_plan.total_estimated_cost = data["total_estimated_cost"]
        if "total_actual_cost" in data:
            treatment_plan.total_actual_cost = data["total_actual_cost"]
        if "notes" in data:
            treatment_plan.notes = data["notes"]
        if "cancellation_reason" in data:
            treatment_plan.cancellation_reason = data["cancellation_reason"]

        db.session.commit()

        app.logger.info(f"Treatment plan updated: {treatment_plan.name} (ID: {plan_id}) by {current_user.username}")

        return jsonify(treatment_plan.to_dict(include_steps=True)), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating treatment plan {plan_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Treatment plan not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/treatment-plans/<int:plan_id>", methods=["DELETE"])
@login_required
def delete_treatment_plan(plan_id):
    """Delete a treatment plan"""
    try:
        treatment_plan = TreatmentPlan.query.get_or_404(plan_id)

        # Delete treatment plan (cascade will delete steps)
        db.session.delete(treatment_plan)
        db.session.commit()

        app.logger.info(f"Treatment plan deleted: {treatment_plan.name} (ID: {plan_id}) by {current_user.username}")

        return jsonify({"message": "Treatment plan deleted"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting treatment plan {plan_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Treatment plan not found"}), 404
        return jsonify({"error": str(e)}), 400


@bp.route("/api/treatment-plans/<int:plan_id>/steps/<int:step_id>", methods=["PATCH"])
@login_required
def update_treatment_plan_step(plan_id, step_id):
    """Update a single treatment plan step"""
    try:
        treatment_plan = TreatmentPlan.query.get_or_404(plan_id)
        step = TreatmentPlanStep.query.get_or_404(step_id)

        # Verify step belongs to this treatment plan
        if step.treatment_plan_id != plan_id:
            return jsonify({"error": "Step does not belong to this treatment plan"}), 400

        data = treatment_plan_step_update_schema.load(request.json)

        # Update fields
        if "title" in data:
            step.title = data["title"]
        if "description" in data:
            step.description = data["description"]
        if "status" in data:
            step.status = data["status"]

            # If marking as completed, set completed_date and performed_by
            if data["status"] == "completed" and not step.completed_date:
                step.completed_date = datetime.utcnow().date()
                if not step.performed_by_id:
                    step.performed_by_id = current_user.id
        if "scheduled_date" in data:
            step.scheduled_date = data["scheduled_date"]
        if "completed_date" in data:
            step.completed_date = data["completed_date"]
        if "estimated_cost" in data:
            step.estimated_cost = data["estimated_cost"]
        if "actual_cost" in data:
            step.actual_cost = data["actual_cost"]
        if "notes" in data:
            step.notes = data["notes"]
        if "performed_by_id" in data:
            step.performed_by_id = data["performed_by_id"]

        # Recalculate treatment plan total costs
        if "actual_cost" in data:
            total_actual = sum(float(s.actual_cost) for s in treatment_plan.steps if s.actual_cost)
            treatment_plan.total_actual_cost = total_actual

        db.session.commit()

        app.logger.info(f"Treatment plan step updated: {step.title} (ID: {step_id}) by {current_user.username}")

        return jsonify(step.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating treatment plan step {step_id}: {str(e)}", exc_info=True)
        if "not found" in str(e).lower():
            return jsonify({"error": "Treatment plan or step not found"}), 404
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
