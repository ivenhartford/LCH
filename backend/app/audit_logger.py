"""
Audit Logging and Performance Monitoring System

Provides comprehensive audit trail and performance logging for all business operations.

Features:
- Audit trail for data modifications (create, update, delete)
- Performance monitoring for endpoints
- Structured logging with JSON format
- Request timing and slow query detection
"""

import logging
import json
import time
from datetime import datetime, date
from decimal import Decimal
from functools import wraps
from flask import current_app, request, g
from flask_login import current_user


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


class StructuredLogger:
    """
    Structured logging with JSON format for better log parsing and analysis.

    Usage:
        structured_logger = StructuredLogger()
        structured_logger.log_event('info', 'client_created', 'New client created',
                                   client_id=123, user_id=1)
    """

    def __init__(self, logger=None):
        self._logger = logger

    @property
    def logger(self):
        """Lazy-load logger to avoid accessing current_app at import time"""
        if self._logger:
            return self._logger
        return current_app.logger

    def log_event(self, level, event_type, message, **kwargs):
        """
        Log a structured event with JSON format

        Args:
            level: Log level (debug, info, warning, error)
            event_type: Type of event (e.g., 'client_created', 'payment_processed')
            message: Human-readable message
            **kwargs: Additional context data
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.upper(),
            "event_type": event_type,
            "message": message,
            **kwargs,
        }

        # Add request context if available
        if request:
            log_entry["request"] = {
                "method": request.method,
                "endpoint": request.endpoint,
                "path": request.path,
                "ip_address": request.remote_addr,
                "user_agent": request.headers.get("User-Agent", "Unknown"),
            }

        # Add user context if available
        if current_user and current_user.is_authenticated:
            log_entry["user"] = {
                "id": current_user.id,
                "username": current_user.username,
                "role": current_user.role,
            }

        # Log as JSON
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(json.dumps(log_entry, default=json_serial))

        return log_entry


# Global structured logger instance
structured_logger = StructuredLogger()


def log_audit_event(
    action,
    entity_type,
    entity_id,
    entity_data=None,
    old_values=None,
    new_values=None,
    user_id=None,
    ip_address=None,
):
    """
    Log an audit trail event for data modifications

    Args:
        action: Action performed (create, update, delete)
        entity_type: Type of entity (client, patient, appointment, etc.)
        entity_id: ID of the entity
        entity_data: Full entity data (for creates)
        old_values: Previous values (for updates)
        new_values: New values (for updates)
        user_id: ID of user who performed action
        ip_address: IP address of request

    Example:
        log_audit_event(
            action='update',
            entity_type='client',
            entity_id=123,
            old_values={'email': 'old@example.com'},
            new_values={'email': 'new@example.com'}
        )
    """
    # Get user from context if not provided
    if user_id is None and current_user and current_user.is_authenticated:
        user_id = current_user.id

    # Get IP from request if not provided
    if ip_address is None and request:
        ip_address = request.remote_addr

    audit_data = {
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_id": user_id,
        "ip_address": ip_address,
    }

    # Add data based on action type
    if action == "create" and entity_data:
        audit_data["entity_data"] = entity_data
    elif action == "update":
        if old_values:
            audit_data["old_values"] = old_values
        if new_values:
            audit_data["new_values"] = new_values
    elif action == "delete":
        if entity_data:
            audit_data["deleted_entity"] = entity_data

    # Log with structured logger
    message = f"{action.upper()} {entity_type} #{entity_id}"
    structured_logger.log_event("info", f"{entity_type}_{action}", message, **audit_data)

    # Also log to regular logger for backwards compatibility
    current_app.logger.info(f"[AUDIT] {message}: {audit_data}")


def log_business_operation(operation, entity_type, entity_id=None, details=None, success=True):
    """
    Log a business operation (non-CRUD operations like status changes, calculations)

    Args:
        operation: Operation performed (e.g., 'appointment_checked_in', 'payment_processed')
        entity_type: Type of entity involved
        entity_id: ID of the entity
        details: Additional operation details
        success: Whether operation was successful

    Example:
        log_business_operation(
            operation='appointment_status_change',
            entity_type='appointment',
            entity_id=456,
            details={'old_status': 'pending', 'new_status': 'confirmed'}
        )
    """
    level = "info" if success else "warning"
    message = f"{operation.replace('_', ' ').title()}"

    if entity_id:
        message += f" for {entity_type} #{entity_id}"

    log_data = {
        "operation": operation,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "success": success,
    }

    if details:
        log_data["details"] = details

    structured_logger.log_event(level, operation, message, **log_data)
    current_app.logger.info(f"[BUSINESS] {message}: {log_data}")


def log_performance(endpoint_name, duration_ms, warning_threshold=1000):
    """
    Log endpoint performance metrics

    Args:
        endpoint_name: Name of the endpoint
        duration_ms: Request duration in milliseconds
        warning_threshold: Threshold for slow request warning (default 1000ms)
    """
    is_slow = duration_ms > warning_threshold
    level = "warning" if is_slow else "debug"

    message = (
        f"{'SLOW ' if is_slow else ''}Request: {endpoint_name} completed in {duration_ms:.2f}ms"
    )

    structured_logger.log_event(
        level,
        "performance_metric",
        message,
        endpoint=endpoint_name,
        duration_ms=duration_ms,
        is_slow=is_slow,
        threshold=warning_threshold,
    )


def log_performance_decorator(f):
    """
    Decorator to automatically log endpoint performance

    Usage:
        @bp.route('/api/clients')
        @log_performance_decorator
        def get_clients():
            ...
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Record start time
        start_time = time.time()

        try:
            # Execute the function
            result = f(*args, **kwargs)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log performance
            log_performance(f.__name__, duration_ms)

            # Store in g for potential use
            g.request_duration = duration_ms

            return result

        except Exception as e:
            # Log failed request
            duration_ms = (time.time() - start_time) * 1000
            current_app.logger.error(
                f"Request {f.__name__} failed after {duration_ms:.2f}ms: {str(e)}"
            )
            raise

    return decorated_function


def log_api_call(method, endpoint, status_code, duration_ms=None, error=None):
    """
    Log API call details

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Endpoint path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        error: Error message if applicable
    """
    is_error = status_code >= 400
    level = "error" if status_code >= 500 else ("warning" if is_error else "info")

    message = f"API {method} {endpoint} -> {status_code}"

    log_data = {"method": method, "endpoint": endpoint, "status_code": status_code}

    if duration_ms:
        log_data["duration_ms"] = duration_ms
        message += f" ({duration_ms:.2f}ms)"

    if error:
        log_data["error"] = error

    structured_logger.log_event(level, "api_call", message, **log_data)


def log_data_access(entity_type, entity_id, access_type="read", granted=True, reason=None):
    """
    Log data access for security and compliance

    Args:
        entity_type: Type of entity accessed
        entity_id: ID of the entity
        access_type: Type of access (read, write, delete)
        granted: Whether access was granted
        reason: Reason for denial if not granted
    """
    level = "info" if granted else "warning"
    message = (
        f"{'Granted' if granted else 'Denied'} {access_type} access to {entity_type} #{entity_id}"
    )

    log_data = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "access_type": access_type,
        "granted": granted,
    }

    if not granted and reason:
        log_data["denial_reason"] = reason
        message += f": {reason}"

    structured_logger.log_event(level, "data_access", message, **log_data)


def get_changed_fields(old_data, new_data):
    """
    Compare two dictionaries and return only the changed fields

    Args:
        old_data: Original data dictionary
        new_data: Updated data dictionary

    Returns:
        tuple: (old_values, new_values) containing only changed fields
    """
    changed_old = {}
    changed_new = {}

    for key in new_data:
        if key in old_data and old_data[key] != new_data[key]:
            changed_old[key] = old_data[key]
            changed_new[key] = new_data[key]

    return changed_old, changed_new


# Export commonly used functions
__all__ = [
    "structured_logger",
    "log_audit_event",
    "log_business_operation",
    "log_performance",
    "log_performance_decorator",
    "log_api_call",
    "log_data_access",
    "get_changed_fields",
]
