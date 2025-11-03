# Security Architecture

This document outlines the security features and best practices implemented in the Lenox Cat Hospital veterinary management system.

## Security Overview

Following a comprehensive security audit (2025-11-02), all critical, high, and medium-priority vulnerabilities have been addressed through Phase 3.6 Security Hardening.

## Authentication & Authorization

### JWT-Based Portal Authentication
- **Implementation:** JWT tokens for all client portal endpoints
- **Token Storage:** sessionStorage (clears on browser close)
- **Token Expiry:** 24 hours
- **Session Management:** 8-hour sessions with 15-minute idle timeout
- **Decorator:** `@portal_auth_required` validates tokens and client_id matching

### Staff Authentication
- **Method:** Flask-Login with session-based authentication
- **Password Hashing:** bcrypt for all users
- **Account Lockout:** 5 failed attempts = 15-minute lockout
- **Tracking:** Failed attempts, last login timestamp

### PIN-Based Quick Unlock
- **Purpose:** Avoid repeated full logins during active sessions
- **Storage:** bcrypt-hashed 4-6 digit PIN
- **Trigger:** 15 minutes of inactivity
- **Session Limit:** 8 hours or browser close

## Password Security

### Password Policy
- **Minimum Length:** 8 characters
- **Complexity Requirements:**
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character
- **Maximum Length:** 100 characters

### Password Hashing
- **Algorithm:** bcrypt with salt
- **Work Factor:** Default bcrypt cost (auto-adjusts with library)
- **Migration:** Automatic upgrade from legacy Werkzeug hashes
- **Validation:** `password_validator.py` module

## Rate Limiting

### Global Limits
- **Default:** 200 requests/day, 50 requests/hour per IP
- **Implementation:** Flask-Limiter with memory storage (use Redis in production)

### Endpoint-Specific Limits
- **Login Endpoints:** 10 attempts per 5 minutes
- **Registration:** 5 attempts per hour
- **Email Verification Resend:** 3 attempts per hour
- **Password Reset:** 5 attempts per hour

## Cross-Site Protection

### CSRF Protection
- **Implementation:** Flask-WTF CSRFProtect
- **Coverage:** All session-based form endpoints
- **Exemptions:** JWT-authenticated API endpoints
- **Token Rotation:** Automatic per-session

### CORS Configuration
- **Method:** Flask-CORS with explicit origin whitelist
- **Allowed Origins:** Configurable via `CORS_ORIGINS` environment variable
- **Credentials:** Supported for authenticated requests
- **Default:** `http://localhost:3000` (development)

## Security Headers

Implemented via Flask-Talisman (production only):

### Content Security Policy (CSP)
- `default-src 'self'`
- `script-src 'self' 'unsafe-inline'` (for React)
- `style-src 'self' 'unsafe-inline'` (for MUI)
- `img-src 'self' data: https:`
- `font-src 'self' data:`
- `connect-src 'self'`

### HTTP Strict Transport Security (HSTS)
- **Enabled:** Production only
- **Duration:** Default (1 year)
- **Subdomains:** Included

### Additional Headers
- **X-Frame-Options:** DENY (prevents clickjacking)
- **X-Content-Type-Options:** nosniff
- **Referrer-Policy:** Configured via Talisman

## Email Verification

### Verification Flow
1. User registers with email address
2. System generates secure 32-character token
3. Verification email sent (stub implementation, integrate with SendGrid/Mailgun)
4. Token expires after 24 hours
5. User clicks link to verify email
6. Login blocked until email verified

### Token Generation
- **Method:** `secrets.token_urlsafe(32)`
- **Storage:** Database (`verification_token` field)
- **Expiry:** 24 hours (`reset_token_expiry` field)

## Error Handling & Information Disclosure

### Production Error Messages
- **Generic Responses:** No implementation details leaked
- **Error Types:**
  - Internal errors: "An unexpected error occurred"
  - Not found: "The requested resource was not found"
  - Validation: "Invalid request data"
  - Authentication: "Authentication failed"
  - Authorization: "You do not have permission"

### Development/Testing
- **Detailed Errors:** Full error messages and tracebacks
- **Detection:** Automatic based on `app.debug` and `app.testing` flags

### Error Handling Module
- **Location:** `backend/app/error_handlers.py`
- **Key Function:** `safe_error_response()` - context-aware error responses
- **Handlers:** Registered for ValidationError, NotFound, Unauthorized, Forbidden, SQLAlchemyError

## Security Monitoring

### Event Tracking
All security events are logged with:
- Timestamp (UTC)
- Event type
- User ID and username (if applicable)
- IP address
- Additional details
- Severity level (info, warning, error, critical)

### Monitored Events
- **Authentication:** Login success/failure, logout, account lockout
- **Session:** Session expiry, invalid tokens
- **PIN:** PIN setup, unlock success/failure
- **Access Control:** Unauthorized access attempts, CSRF failures
- **Rate Limiting:** Rate limit violations
- **Email:** Email verification events
- **Suspicious Activity:** Brute force attempts, repeated failures

### Brute Force Detection
- **Threshold:** 10 failed logins within 5 minutes per IP
- **Action:** IP marked as suspicious, event logged as critical
- **Tracking:** In-memory (use Redis/database in production)

### Security Monitor Module
- **Location:** `backend/app/security_monitor.py`
- **Class:** `SecurityMonitor` - singleton instance
- **Usage:** `get_security_monitor()` - access global instance

### Integration Points
- Staff login/logout endpoints
- Client portal authentication
- PIN verification endpoints
- Rate limit violations
- Unauthorized access attempts

## Secret Management

### SECRET_KEY
- **Requirement:** MUST be set in production (enforced at startup)
- **Generation:** `python -c 'import secrets; print(secrets.token_hex(32))'`
- **Storage:** Environment variable only, never in code
- **Development:** Default provided with warning
- **Testing:** Dedicated test key

### Database Credentials
- **Storage:** Environment variables
- **No Defaults:** Production requires explicit configuration

## SQL Injection Protection

- **ORM:** SQLAlchemy with parameterized queries
- **Input Validation:** Marshmallow schemas on all inputs
- **No Raw SQL:** All queries use ORM methods

## XSS Prevention

- **React:** Automatic escaping of user content
- **No Dangerous HTML:** No `dangerouslySetInnerHTML` usage
- **API:** JSON responses only, no HTML rendering

## Best Practices for Deployment

### Environment Variables Required
```bash
SECRET_KEY=<generate-secure-random-key>
DATABASE_URL=<production-database-url>
FLASK_ENV=production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Recommended Additional Steps
1. **Use HTTPS:** SSL/TLS certificates required
2. **Redis for Rate Limiting:** Replace memory storage
3. **Database Backups:** Automated daily backups
4. **Security Monitoring:** Integrate with Sentry, DataDog, or similar
5. **Email Service:** Configure SendGrid, Mailgun, or AWS SES
6. **Firewall:** Restrict database access to application servers only
7. **Regular Updates:** Keep dependencies up to date
8. **Penetration Testing:** Annual security audits recommended

### Security Headers Checklist
- ✅ HTTPS enforced
- ✅ HSTS enabled
- ✅ CSP configured
- ✅ X-Frame-Options set
- ✅ X-Content-Type-Options set
- ✅ CORS properly configured

## Incident Response

### Security Event Logs
- **Location:** `logs/vet_clinic.log`
- **Format:** Timestamped with severity levels
- **Rotation:** 10MB max, 10 backup files

### Monitoring Alerts
Security events at WARNING or CRITICAL levels should trigger alerts:
- Multiple failed login attempts
- Account lockouts
- Brute force detection
- Unauthorized access attempts
- Rate limit violations

### Response Procedures
1. **Identify:** Review security event logs
2. **Contain:** Lock affected accounts, block suspicious IPs
3. **Investigate:** Analyze patterns, identify root cause
4. **Remediate:** Apply fixes, update credentials if compromised
5. **Document:** Record incident details and response actions

## Compliance Notes

### Data Protection
- Passwords hashed with bcrypt (never stored in plaintext)
- Sensitive data encrypted in transit (HTTPS)
- Session tokens expire and rotate
- Email verification required for portal access

### HIPAA Considerations
While this system includes many security best practices, full HIPAA compliance requires:
- Business Associate Agreements (BAAs)
- Encryption at rest for database
- Comprehensive audit logging
- Physical security controls
- Regular risk assessments
- Staff training and policies

**Note:** Consult with legal and compliance experts for full HIPAA certification.

## Security Contact

For security concerns or to report vulnerabilities:
- Review code in: `backend/app/error_handlers.py`, `backend/app/security_monitor.py`
- Check security tests in: `backend/tests/test_security.py`
- Security audit findings: See ROADMAP.md Phase 3.6

---

**Last Updated:** 2025-11-03
**Security Audit Date:** 2025-11-02
**Phase 3.6 Completion:** 2025-11-03
