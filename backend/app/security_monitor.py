"""
Security Monitoring and Alert System

Tracks authentication failures, suspicious patterns, and security events.
Provides real-time monitoring and alerting capabilities.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from flask import current_app, request
from .error_handlers import SecurityEvent, log_security_event
import threading


class SecurityMonitor:
    """
    In-memory security event tracker with pattern detection

    In production, this should be replaced with a proper security
    monitoring service (Sentry, DataDog, Splunk, etc.)
    """

    def __init__(self):
        self.events = []
        self.failed_logins = defaultdict(list)  # IP -> list of timestamps
        self.suspicious_ips = set()
        self.lock = threading.Lock()

        # Thresholds for detection
        self.FAILED_LOGIN_THRESHOLD = 10  # failures per window
        self.FAILED_LOGIN_WINDOW = 300  # 5 minutes
        self.RATE_LIMIT_THRESHOLD = 100  # requests per minute
        self.SUSPICIOUS_PATTERN_THRESHOLD = 5  # suspicious events

    def track_failed_login(self, ip_address, username=None):
        """Track failed login attempts and detect brute force"""
        with self.lock:
            now = datetime.utcnow()
            self.failed_logins[ip_address].append(now)

            # Clean old entries
            cutoff = now - timedelta(seconds=self.FAILED_LOGIN_WINDOW)
            self.failed_logins[ip_address] = [
                t for t in self.failed_logins[ip_address] if t > cutoff
            ]

            # Check if threshold exceeded
            if len(self.failed_logins[ip_address]) >= self.FAILED_LOGIN_THRESHOLD:
                self.mark_suspicious(ip_address)
                log_security_event(
                    SecurityEvent.SUSPICIOUS_ACTIVITY,
                    ip_address=ip_address,
                    username=username,
                    details=f"Brute force detected: {len(self.failed_logins[ip_address])} failed logins in {self.FAILED_LOGIN_WINDOW}s",
                    severity="critical",
                )
                return True

        return False

    def track_successful_login(self, ip_address, username, user_id):
        """Track successful logins and clear failure count"""
        with self.lock:
            # Clear failed login history for this IP
            if ip_address in self.failed_logins:
                del self.failed_logins[ip_address]

        log_security_event(
            SecurityEvent.LOGIN_SUCCESS,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            severity="info",
        )

    def track_logout(self, username, user_id, ip_address):
        """Track logout events"""
        log_security_event(
            SecurityEvent.LOGOUT,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            severity="info",
        )

    def track_account_lockout(self, username, user_id, ip_address):
        """Track account lockout events"""
        log_security_event(
            SecurityEvent.ACCOUNT_LOCKED,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details="Account locked due to failed login attempts",
            severity="warning",
        )

    def track_unauthorized_access(self, endpoint, user_id=None, username=None, ip_address=None):
        """Track unauthorized access attempts"""
        log_security_event(
            SecurityEvent.UNAUTHORIZED_ACCESS,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details=f"Attempted access to: {endpoint}",
            severity="warning",
        )

    def track_rate_limit_exceeded(self, endpoint, ip_address):
        """Track rate limit violations"""
        log_security_event(
            SecurityEvent.RATE_LIMIT_EXCEEDED,
            ip_address=ip_address,
            details=f"Rate limit exceeded for: {endpoint}",
            severity="warning",
        )

    def track_invalid_token(self, token_type, ip_address):
        """Track invalid token attempts"""
        log_security_event(
            SecurityEvent.INVALID_TOKEN,
            ip_address=ip_address,
            details=f"Invalid {token_type} token",
            severity="warning",
        )

    def track_session_expired(self, user_id, username):
        """Track session expiry events"""
        log_security_event(
            SecurityEvent.SESSION_EXPIRED, user_id=user_id, username=username, severity="info"
        )

    def track_pin_unlock(self, success, user_id, username, ip_address):
        """Track PIN unlock attempts"""
        event_type = (
            SecurityEvent.PIN_UNLOCK_SUCCESS if success else SecurityEvent.PIN_UNLOCK_FAILURE
        )
        severity = "info" if success else "warning"

        log_security_event(
            event_type, user_id=user_id, username=username, ip_address=ip_address, severity=severity
        )

    def mark_suspicious(self, ip_address):
        """Mark an IP address as suspicious"""
        self.suspicious_ips.add(ip_address)
        current_app.logger.warning(f"[SECURITY] IP {ip_address} marked as suspicious")

    def is_suspicious(self, ip_address):
        """Check if an IP is marked suspicious"""
        return ip_address in self.suspicious_ips

    def get_client_ip(self):
        """Get client IP address from request"""
        # Check for X-Forwarded-For header (when behind proxy)
        if request.headers.get("X-Forwarded-For"):
            return request.headers.get("X-Forwarded-For").split(",")[0].strip()
        # Check for X-Real-IP header
        elif request.headers.get("X-Real-IP"):
            return request.headers.get("X-Real-IP")
        # Fallback to remote_addr
        return request.remote_addr

    def get_statistics(self):
        """Get security monitoring statistics"""
        with self.lock:
            return {
                "failed_login_attempts": {
                    ip: len(timestamps) for ip, timestamps in self.failed_logins.items()
                },
                "suspicious_ips": list(self.suspicious_ips),
                "total_events": len(self.events),
            }

    def clear_suspicious_ip(self, ip_address):
        """Clear an IP from suspicious list (admin action)"""
        with self.lock:
            self.suspicious_ips.discard(ip_address)
            if ip_address in self.failed_logins:
                del self.failed_logins[ip_address]

        log_security_event(
            "security_event_cleared",
            details=f"IP {ip_address} cleared from suspicious list",
            severity="info",
        )


# Global security monitor instance
security_monitor = SecurityMonitor()


def get_security_monitor():
    """Get the global security monitor instance"""
    return security_monitor
