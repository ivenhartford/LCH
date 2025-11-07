"""
Authentication utilities for JWT token management and portal authentication
"""

import jwt
from datetime import datetime, timedelta
from flask import request, jsonify, current_app
from functools import wraps
from .models import ClientPortalUser


def generate_portal_token(portal_user):
    """
    Generate JWT token for client portal user

    Args:
        portal_user: ClientPortalUser model instance

    Returns:
        str: JWT token
    """
    payload = {
        "portal_user_id": portal_user.id,
        "client_id": portal_user.client_id,
        "username": portal_user.username,
        "exp": datetime.utcnow() + timedelta(hours=24),  # Token expires in 24 hours
        "iat": datetime.utcnow(),  # Issued at
        "type": "portal_access",
    }

    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
    return token


def verify_portal_token(token):
    """
    Verify and decode JWT token for client portal

    Args:
        token: JWT token string

    Returns:
        dict: Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])

        # Verify this is a portal access token
        if payload.get("type") != "portal_access":
            return None

        return payload
    except jwt.ExpiredSignatureError:
        current_app.logger.warning("Portal token expired")
        return None
    except jwt.InvalidTokenError as e:
        current_app.logger.warning(f"Invalid portal token: {str(e)}")
        return None


def portal_auth_required(f):
    """
    Decorator to require portal authentication for routes

    Verifies JWT token and ensures the user can only access their own data
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401

        # Expected format: "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return (
                jsonify({"error": "Invalid authorization header format. Use: Bearer <token>"}),
                401,
            )

        token = parts[1]

        # Verify token
        payload = verify_portal_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Get the authenticated user's client_id from token
        authenticated_client_id = payload.get("client_id")

        # If the route has a client_id parameter, verify it matches
        url_client_id = kwargs.get("client_id")
        if url_client_id and url_client_id != authenticated_client_id:
            current_app.logger.warning(
                f"Authorization violation: User {authenticated_client_id} "
                f"attempted to access client {url_client_id}"
            )
            return (
                jsonify(
                    {
                        "error": "Unauthorized access. You can only access your own data.",
                    }
                ),
                403,
            )

        # Add portal user info to kwargs for the route function to use if needed
        kwargs["authenticated_client_id"] = authenticated_client_id
        kwargs["portal_user_id"] = payload.get("portal_user_id")

        return f(*args, **kwargs)

    return decorated_function
