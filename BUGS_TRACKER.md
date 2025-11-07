# Application Bugs Tracker

## Status Legend
- 🔴 CRITICAL - Blocking functionality
- 🟡 HIGH - Major functionality impaired
- 🟢 MEDIUM - Minor issues
- ⚪ LOW - Cosmetic/test issues

---

## 🔴 CRITICAL BUGS

### 1. Marshmallow Schema - Password Validation Error
**Status:** 🔴 CRITICAL - BLOCKING PORTAL REGISTRATION
**Error:** `ClientPortalUserRegistrationSchema.validate_password_complexity() got an unexpected keyword argument 'data_key'`
**Location:** `backend/app/schemas.py` - ClientPortalUserRegistrationSchema
**Impact:** All portal user registration attempts fail
**Tests Affected:** 7 tests in test_client_portal_api.py, 4 tests in test_security.py
**Fix Required:** Remove invalid `data_key` argument from validation decorator

### 2. JSON Serialization - Decimal/Date Not Serializable
**Status:** 🔴 CRITICAL - BREAKING PATIENT UPDATES
**Error:** `Object of type Decimal is not JSON serializable`
**Location:** `backend/app/audit_logger.py:80` - log_event method
**Impact:** Patient updates fail with 500 error
**Tests Affected:** 3 tests in test_patient_api.py
**Fix Required:** Add custom JSON encoder for Decimal and date objects

---

## 🟡 HIGH PRIORITY BUGS

### 3. Missing Test Fixtures - Treatment Protocol API
**Status:** ✅ FIXED
**Error:** `fixture 'auth_headers' not found`
**Location:** `backend/tests/conftest.py`
**Impact:** Entire treatment protocol test suite fails
**Tests Affected:** All 35 tests in test_treatment_protocol_api.py
**Fix Applied:** Added missing fixtures to conftest.py:
- `test_user`: Creates authenticated user
- `auth_headers`: Logs in user and returns empty dict for session-based auth
- `test_patient`: Creates patient with owner
- `session`: Provides db.session within app context
- Disabled CSRF for testing with `WTF_CSRF_ENABLED: False`
**Result:** 35 tests now passing, 2 minor test-specific failures remain

### 4. SQLAlchemy DetachedInstanceError
**Status:** 🟡 HIGH
**Error:** `Instance <ClientPortalUser> is not bound to a Session`
**Location:** Multiple test files accessing objects outside app context
**Impact:** 9 security tests failing
**Tests Affected:** test_security.py JWT and authorization tests
**Fix Required:** Refresh objects within app context or eager load attributes

### 5. Model Schema Mismatch - PurchaseOrderItem
**Status:** 🟡 HIGH
**Error:** `'unit_price' is an invalid keyword argument for PurchaseOrderItem`
**Location:** `backend/app/models.py` - PurchaseOrderItem model
**Impact:** Purchase order receiving fails
**Tests Affected:** test_inventory_api.py::test_receive_purchase_order
**Fix Required:** Add unit_price column to PurchaseOrderItem model or fix test

---

## 🟢 MEDIUM PRIORITY BUGS

### 6. Schema Validation - Unknown Fields
**Status:** 🟢 MEDIUM
**Errors:**
- Client: `{'address_street': ['Unknown field.']}`
- Patient: `{'sex': ['Must be one of: Male, Female.'], 'status': ['Must be one of: Active, Inactive, Deceased.']}`
**Location:** `backend/app/schemas.py`
**Impact:** Integration tests fail, case sensitivity issues
**Tests Affected:** test_integration_workflows.py
**Fix Required:** Fix schema field definitions or make case-insensitive

### 7. Portal Authentication - Login Failures
**Status:** 🟢 MEDIUM
**Error:** Portal login returning 403 instead of 200
**Location:** `backend/app/routes.py` - portal_login endpoint
**Impact:** Portal users cannot log in
**Tests Affected:** 15+ portal authentication tests
**Fix Required:** Debug authentication logic, password hashing mismatch?

### 8. Document API - Missing Authentication
**Status:** 🟢 MEDIUM - SECURITY ISSUE
**Error:** Endpoints returning 200 instead of 401 for unauthenticated requests
**Location:** `backend/app/routes.py` - document endpoints
**Impact:** Security vulnerability - documents accessible without auth
**Tests Affected:** 4 tests in test_document_api.py
**Fix Required:** Add @login_required decorator to document endpoints

### 9. Admin Authorization - Delete Operations
**Status:** 🟢 MEDIUM
**Error:** Admin delete operations returning 403 instead of 200
**Location:** `backend/app/routes.py` - vendor/product delete endpoints
**Impact:** Admins cannot delete vendors/products
**Tests Affected:** 6 tests in test_inventory_api.py
**Fix Required:** Check role-based authorization decorators

---

## ⚪ LOW PRIORITY ISSUES

### 10. Test Assertion Mismatches
**Status:** ⚪ LOW
**Issues:**
- Email verification message: `'Email verified successfully! You can now log in.'` vs `'Email verified successfully'`
- Invalid token message: `'Invalid verification token'` vs `'Invalid or expired'`
- Staff lockout: returning 403 instead of 401
**Location:** Various test files
**Impact:** Test assertions don't match actual responses
**Fix Required:** Update test assertions to match actual messages

### 11. Inventory Transaction Validation
**Status:** ⚪ LOW
**Error:** Creating inventory transaction returns 400
**Location:** `backend/app/routes.py` - inventory transaction endpoint
**Impact:** Manual inventory adjustments fail
**Tests Affected:** 1 test in test_inventory_api.py
**Fix Required:** Debug validation schema

---

## Fix Priority Order

1. 🔴 Bug #1: Marshmallow schema password validation
2. 🔴 Bug #2: JSON serialization in audit logger
3. 🟡 Bug #3: Missing test fixtures
4. 🟡 Bug #4: SQLAlchemy detached instances
5. 🟡 Bug #5: PurchaseOrderItem schema
6. 🟢 Bug #6-9: Schema validations and auth issues
7. ⚪ Bug #10-11: Test assertion updates

---

## Test Summary
- **Total Tests:** 366
- **Passed:** 314 (85.8%)
- **Failed:** 58 (15.8%)
- **Errors:** 35 (9.6%)
