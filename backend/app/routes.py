import os
from flask import jsonify, send_from_directory, request, Blueprint
from flask import current_app as app
from .models import db, User, Patient, Pet, Appointment, Client
from .schemas import (
    client_schema,
    clients_schema,
    client_update_schema,
    patient_schema,
    patients_schema,
    patient_update_schema,
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
            abort(403)
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


@bp.route("/api/appointments", methods=["GET"])
@login_required
def get_appointments():
    appointments = Appointment.query.all()
    return jsonify(
        [
            {
                "id": apt.id,
                "title": apt.title,
                "start": apt.start_time.isoformat(),
                "end": apt.end_time.isoformat(),
                "description": apt.description,
            }
            for apt in appointments
        ]
    )


@bp.route("/api/appointments", methods=["POST"])
@login_required
def create_appointment():
    data = request.get_json()
    start_time = datetime.fromisoformat(data["start"])
    end_time = datetime.fromisoformat(data["end"])

    new_appointment = Appointment(
        title=data["title"],
        start_time=start_time,
        end_time=end_time,
        description=data.get("description"),
    )
    db.session.add(new_appointment)
    db.session.commit()

    return jsonify({"message": "Appointment created successfully"}), 201


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
            from datetime import datetime

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


@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def serve(path):
    static_folder = app.config.get("STATIC_FOLDER")
    if path != "" and os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)
    else:
        return send_from_directory(static_folder, "index.html")
