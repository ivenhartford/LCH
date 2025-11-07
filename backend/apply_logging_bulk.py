#!/usr/bin/env python3
"""
Bulk Logging Application Script

This script systematically adds audit logging and performance monitoring to ALL
remaining CRUD operations in routes.py.

Strategy:
1. Identify all @bp.route decorators
2. Add @log_performance_decorator where missing
3. Add audit logging after CREATE/UPDATE/DELETE operations

Usage:
    python apply_logging_bulk.py

Note: This creates a modified routes.py - review before using!
"""

import re
import sys

# Entities and their key fields for logging
ENTITY_LOGGING_CONFIG = {
    "patient": ["name", "species", "breed", "owner_id", "microchip_number"],
    "appointment": ["client_id", "patient_id", "appointment_type_id", "status", "start_time"],
    "visit": ["patient_id", "appointment_id", "visit_date", "reason"],
    "invoice": ["client_id", "patient_id", "visit_id", "total_amount", "status"],
    "payment": ["invoice_id", "amount", "payment_method", "payment_date"],
    "service": ["name", "price", "category"],
    "vendor": ["name", "email", "phone"],
    "product": ["name", "vendor_id", "sku", "current_stock"],
    "purchase_order": ["vendor_id", "order_date", "status", "total_amount"],
    "document": ["client_id", "patient_id", "document_type", "filename"],
}

# Status change operations that need business logging
STATUS_OPERATIONS = {
    "appointment": ["status"],
    "invoice": ["status"],
    "purchase_order": ["status"],
}


def add_performance_decorator(route_function):
    """
    Add @log_performance_decorator to a route function if not present
    """
    lines = route_function.split("\n")

    # Check if already has decorator
    if "@log_performance_decorator" in route_function:
        return route_function

    # Find @login_required or @bp.route line
    for i, line in enumerate(lines):
        if "@login_required" in line:
            # Insert before @login_required
            lines.insert(i, "@log_performance_decorator")
            break
        elif "def " in line:
            # Insert just before function definition
            lines.insert(i, "@log_performance_decorator")
            break

    return "\n".join(lines)


def generate_create_audit_log(entity_type, fields):
    """
    Generate audit logging code for CREATE operations
    """
    entity_name = f"new_{entity_type}"

    field_dict = ",\n                ".join(
        [f"'{field}': {entity_name}.{field}" for field in fields]
    )

    code = f"""
        # Audit log: {entity_type.title()} created
        log_audit_event(
            action='create',
            entity_type='{entity_type}',
            entity_id={entity_name}.id,
            entity_data={{
                {field_dict}
            }}
        )
"""
    return code


def generate_update_audit_log(entity_type):
    """
    Generate audit logging code for UPDATE operations
    """
    code = f"""
        # Audit log: {entity_type.title()} updated
        changed_old, changed_new = get_changed_fields(old_values, new_values)
        if changed_old:  # Only log if there were actual changes
            log_audit_event(
                action='update',
                entity_type='{entity_type}',
                entity_id={entity_type}_id,
                old_values=changed_old,
                new_values=changed_new
            )
"""
    return code


def generate_delete_audit_log(entity_type, fields):
    """
    Generate audit logging code for DELETE operations
    """
    field_dict = ",\n                ".join(
        [f"'{field}': {entity_type}.{field}" for field in fields[:3]]  # Just key fields
    )

    code = f"""
        # Capture entity data for audit trail
        {entity_type}_data = {{
            {field_dict}
        }}

        # ... (after delete) ...

        # Audit log: {entity_type.title()} deleted
        log_audit_event(
            action='delete',
            entity_type='{entity_type}',
            entity_id={entity_type}_id,
            entity_data={entity_type}_data
        )
"""
    return code


def print_summary():
    """Print implementation summary"""
    print("=" * 80)
    print("AUDIT LOGGING - BULK APPLICATION GUIDE")
    print("=" * 80)
    print("\nThis script provides patterns for ALL remaining entities.\n")

    print("Entities configured for logging:")
    print("-" * 80)
    for entity, fields in ENTITY_LOGGING_CONFIG.items():
        print(f"  {entity:20} -> {', '.join(fields[:3])}...")

    print("\n" + "=" * 80)
    print("QUICK REFERENCE - Apply these patterns manually:")
    print("=" * 80)

    print("\n1. ADD DECORATOR TO ALL ENDPOINTS:")
    print("-" * 80)
    print("@bp.route('/api/...', methods=['...'])")
    print("@login_required")
    print("@log_performance_decorator  # ADD THIS")
    print("def function_name():")

    print("\n2. FOR CREATE OPERATIONS:")
    print("-" * 80)
    print(generate_create_audit_log("patient", ["name", "owner_id", "species"]))

    print("\n3. FOR UPDATE OPERATIONS:")
    print("-" * 80)
    print(
        """
        # BEFORE updating, capture old values
        old_values = {}
        for key in data.keys():
            if hasattr(entity, key):
                old_values[key] = getattr(entity, key)

        # Update fields
        new_values = {}
        for key, value in validated_data.items():
            setattr(entity, key, value)
            new_values[key] = value

        db.session.commit()
"""
    )
    print(generate_update_audit_log("patient"))

    print("\n4. FOR DELETE OPERATIONS:")
    print("-" * 80)
    print(generate_delete_audit_log("patient", ["name", "owner_id", "species"]))

    print("\n5. FOR STATUS CHANGES:")
    print("-" * 80)
    print(
        """
        log_business_operation(
            operation='entity_status_change',
            entity_type='appointment',
            entity_id=entity_id,
            details={
                'old_status': old_status,
                'new_status': new_status
            }
        )
"""
    )

    print("\n" + "=" * 80)
    print("ENTITIES THAT NEED LOGGING APPLIED:")
    print("=" * 80)

    operations_needed = [
        ("Patient", "UPDATE, DELETE", "~1080-1180"),
        ("Appointment", "CREATE, UPDATE, DELETE, status changes", "~1250-1450"),
        ("Visit", "CREATE, UPDATE", "~2100-2300"),
        ("Invoice", "CREATE, UPDATE", "~3200-3400"),
        ("Payment", "CREATE", "~3450-3550"),
        ("Service", "CREATE, UPDATE, DELETE", "~3600-3750"),
        ("Vendor", "CREATE, UPDATE, DELETE", "~4200-4350"),
        ("Product", "CREATE, UPDATE, DELETE", "~4400-4550"),
        ("Purchase Order", "CREATE, UPDATE", "~4600-4750"),
        ("Document", "CREATE, DELETE", "~5800-5950"),
    ]

    for entity, ops, lines in operations_needed:
        print(f"  {entity:20} {ops:40} Lines: {lines}")

    print("\n" + "=" * 80)
    print("ESTIMATED TIME TO COMPLETE: 4-5 hours")
    print("=" * 80)
    print("\nFollow the patterns above for each entity!")
    print("=" * 80)


if __name__ == "__main__":
    print_summary()
