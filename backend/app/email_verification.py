"""
Email verification utilities
Handles email verification token generation and validation
"""

import secrets
from datetime import datetime, timedelta
from flask import current_app


def generate_verification_token():
    """
    Generate a secure random verification token

    Returns:
        str: Random token (32 hex characters)
    """
    return secrets.token_urlsafe(32)


def send_verification_email(email, token, username):
    """
    Send verification email to user

    Args:
        email (str): User's email address
        token (str): Verification token
        username (str): User's username

    Returns:
        bool: True if email sent successfully

    Note: This is a stub implementation. In production, integrate with
    email service like SendGrid, Mailgun, or AWS SES.
    """
    # TODO: Integrate with email service
    verification_url = f"{current_app.config.get('APP_URL', 'http://localhost:3000')}/portal/verify-email?token={token}"

    # For now, just log the verification URL
    current_app.logger.info(
        f"Email verification for {username} ({email}): {verification_url}"
    )

    # In production, send actual email:
    # Example with SendGrid:
    # from sendgrid import SendGridAPIClient
    # from sendgrid.helpers.mail import Mail
    #
    # message = Mail(
    #     from_email='noreply@lenoxcathospital.com',
    #     to_emails=email,
    #     subject='Verify Your Email - Lenox Cat Hospital',
    #     html_content=f'''
    #         <h2>Welcome to Lenox Cat Hospital Client Portal!</h2>
    #         <p>Hello {username},</p>
    #         <p>Please verify your email address by clicking the link below:</p>
    #         <p><a href="{verification_url}">Verify Email Address</a></p>
    #         <p>This link will expire in 24 hours.</p>
    #         <p>If you didn't create this account, please ignore this email.</p>
    #     '''
    # )
    # try:
    #     sg = SendGridAPIClient(current_app.config['SENDGRID_API_KEY'])
    #     response = sg.send(message)
    #     return response.status_code == 202
    # except Exception as e:
    #     current_app.logger.error(f"Failed to send verification email: {str(e)}")
    #     return False

    return True  # Stub returns True


def send_password_reset_email(email, token, username):
    """
    Send password reset email to user

    Args:
        email (str): User's email address
        token (str): Reset token
        username (str): User's username

    Returns:
        bool: True if email sent successfully

    Note: This is a stub implementation.
    """
    reset_url = f"{current_app.config.get('APP_URL', 'http://localhost:3000')}/portal/reset-password?token={token}"

    # For now, just log the reset URL
    current_app.logger.info(
        f"Password reset for {username} ({email}): {reset_url}"
    )

    return True  # Stub returns True


def is_token_valid(token_expiry):
    """
    Check if verification token is still valid

    Args:
        token_expiry (datetime): Token expiration datetime

    Returns:
        bool: True if token is still valid
    """
    if not token_expiry:
        return False

    return datetime.utcnow() < token_expiry
