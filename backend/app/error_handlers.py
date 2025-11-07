"""
Centralized Error Handling and Security Monitoring

Provides generic error messages for production while logging detailed
errors server-side. Implements security event tracking and monitoring.
"""

from flask import current_app, jsonify
from datetime import datetime
import traceback
from functools import wraps


# Generic error messages for production (no implementation details leaked)
GENERIC_ERRORS = {
    "internal_error": "An unexpected error occurred. Please try again later.",
    "not_found": "The requested resource was not found.",
    "validation_error": "Invalid request data. Please check your input.",
    "auth_error": "Authentication failed. Please check your credentials.",
    "permission_error": "You do not have permission to perform this action.",
    "rate_limit": "Too many requests. Please try again later.",
    "database_error": "A database error occurred. Please try again later.",
}


class SecurityEvent:
    """Security event types for monitoring"""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CSRF_TOKEN_MISMATCH = "csrf_token_mismatch"
    INVALID_TOKEN = "invalid_token"
    SESSION_EXPIRED = "session_expired"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    EMAIL_VERIFICATION = "email_verification"
    PIN_SET = "pin_set"
    PIN_UNLOCK_SUCCESS = "pin_unlock_success"
    PIN_UNLOCK_FAILURE = "pin_unlock_failure"


def log_security_event(
    event_type, user_id=None, username=None, ip_address=None, details=None, severity="info"
):
    """
    Log security events for monitoring and audit trail

    Args:
        event_type: Type of security event (use SecurityEvent constants)
        user_id: User ID if applicable
        username: Username if applicable
        ip_address: Client IP address
        details: Additional details about the event
        severity: Event severity (info, warning, error, critical)
    """
    event_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "username": username,
        "ip_address": ip_address,
        "details": details,
        "severity": severity,
    }

    # Log with appropriate level
    log_method = getattr(current_app.logger, severity, current_app.logger.info)
    log_method(f"[SECURITY] {event_type}: {event_data}")

    # In production, this would also send to a security monitoring service
    # (e.g., Sentry, DataDog, CloudWatch, Splunk)

    return event_data


def safe_error_response(error, error_type="internal_error", status_code=500, include_details=None):
    """
    Return a safe error response that doesn't leak implementation details
    in production, but provides useful info in development.

    Args:
        error: The exception or error object
        error_type: Key from GENERIC_ERRORS dict
        status_code: HTTP status code
        include_details: Override to force include/exclude details

    Returns:
        tuple: (jsonify response, status_code)
    """
    # Log full error details server-side
    current_app.logger.error(f"Error ({error_type}): {str(error)}", exc_info=True)

    # Determine if we should include details
    show_details = (
        include_details
        if include_details is not None
        else (current_app.debug or current_app.testing)
    )

    # Build response
    response = {"error": GENERIC_ERRORS.get(error_type, GENERIC_ERRORS["internal_error"])}

    # Include details only in development/testing
    if show_details:
        response["error_details"] = str(error)
        response["error_type"] = error_type

        # Include traceback in debug mode
        if current_app.debug:
            response["traceback"] = traceback.format_exc()

    return jsonify(response), status_code


def handle_validation_error(error):
    """Handle Marshmallow validation errors"""
    return safe_error_response(error, error_type="validation_error", status_code=400)


def handle_not_found_error(error):
    """Handle resource not found errors"""
    return safe_error_response(error, error_type="not_found", status_code=404)


def handle_auth_error(error):
    """Handle authentication errors"""
    log_security_event(SecurityEvent.LOGIN_FAILURE, details=str(error), severity="warning")
    return safe_error_response(error, error_type="auth_error", status_code=401)


def handle_permission_error(error):
    """Handle authorization/permission errors"""
    log_security_event(SecurityEvent.UNAUTHORIZED_ACCESS, details=str(error), severity="warning")
    return safe_error_response(error, error_type="permission_error", status_code=403)


def handle_database_error(error):
    """Handle database errors"""
    return safe_error_response(error, error_type="database_error", status_code=500)


def monitor_endpoint(f):
    """
    Decorator to add automatic security monitoring to endpoints
    Tracks suspicious patterns and repeated failures
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)

            # Monitor for suspicious response patterns
            if isinstance(result, tuple) and len(result) >= 2:
                response, status_code = result[0], result[1]

                # Log repeated authentication failures
                if status_code in [401, 403]:
                    log_security_event(
                        SecurityEvent.UNAUTHORIZED_ACCESS,
                        details=f"Endpoint: {f.__name__}",
                        severity="warning",
                    )

            return result

        except Exception as e:
            # Log unexpected errors
            current_app.logger.error(f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            return safe_error_response(e)

    return decorated_function


# Error message sanitizers for specific scenarios
def sanitize_database_error(error):
    """
    Sanitize database errors to not reveal schema details
    """
    error_str = str(error).lower()

    # Don't reveal table names, column names, etc.
    if any(
        word in error_str
        for word in ["table", "column", "constraint", "foreign key", "unique", "null"]
    ):
        return "A database constraint was violated."

    return GENERIC_ERRORS["database_error"]


def sanitize_validation_error(error):
    """
    Sanitize validation errors to not reveal internal field names
    """
    # Allow basic validation errors but sanitize field names
    error_str = str(error)

    # In production, consider mapping internal field names to user-friendly names
    # For now, just return the generic message
    if not (current_app.debug or current_app.testing):
        return GENERIC_ERRORS["validation_error"]

    return error_str
