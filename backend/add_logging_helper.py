"""
Helper script to demonstrate how to add audit logging to all business operations

This script provides templates and patterns for adding comprehensive logging
to all CRUD operations in the application.

Usage:
    1. Use these templates as reference when manually adding logging
    2. Or adapt this script to programmatically add logging

Note: Manual addition is recommended for precision and code review
"""

# Template for CREATE operations
CREATE_TEMPLATE = """
# After successful creation and db.session.commit()

# Audit log: {Entity} created
log_audit_event(
    action='create',
    entity_type='{entity}',
    entity_id=new_{entity}.id,
    entity_data={{
        # Include key fields that identify the entity
        'name': new_{entity}.name,  # Adjust field names
        # Add other relevant fields
    }}
)
"""

# Template for UPDATE operations
UPDATE_TEMPLATE = """
# Before updating, capture old values
old_values = {{}}
for key in data.keys():
    if hasattr({entity}, key):
        old_values[key] = getattr({entity}, key)

# After updating fields
new_values = {{}}
for key, value in validated_data.items():
    setattr({entity}, key, value)
    new_values[key] = value

db.session.commit()

# Audit log: {Entity} updated
changed_old, changed_new = get_changed_fields(old_values, new_values)
if changed_old:  # Only log if there were actual changes
    log_audit_event(
        action='update',
        entity_type='{entity}',
        entity_id={entity}_id,
        old_values=changed_old,
        new_values=changed_new
    )
"""

# Template for DELETE operations
DELETE_TEMPLATE = """
# Capture entity data before delete
{entity}_data = {{
    'name': {entity}.name,  # Adjust field names
    # Add key identifying fields
}}

# For hard delete:
db.session.delete({entity})
db.session.commit()

log_audit_event(
    action='delete',
    entity_type='{entity}',
    entity_id={entity}_id,
    entity_data={entity}_data
)

# For soft delete/deactivate:
{entity}.is_active = False
db.session.commit()

log_business_operation(
    operation='{entity}_deactivated',
    entity_type='{entity}',
    entity_id={entity}_id,
    details={{'deactivated_by': current_user.username}}
)
"""

# Template for status change operations
STATUS_CHANGE_TEMPLATE = """
# Log status change
log_business_operation(
    operation='{entity}_status_change',
    entity_type='{entity}',
    entity_id={entity}_id,
    details={{
        'old_status': old_status,
        'new_status': new_status,
        'changed_by': current_user.username
    }}
)
"""

# Template for payment/financial operations
PAYMENT_TEMPLATE = """
# Log payment processed
log_business_operation(
    operation='payment_processed',
    entity_type='payment',
    entity_id=payment.id,
    details={{
        'amount': payment.amount,
        'method': payment.payment_method,
        'invoice_id': payment.invoice_id,
        'processed_by': current_user.username
    }}
)

# Also log the audit event
log_audit_event(
    action='create',
    entity_type='payment',
    entity_id=payment.id,
    entity_data={{
        'amount': payment.amount,
        'payment_method': payment.payment_method,
        'invoice_id': payment.invoice_id
    }}
)
"""

# List of entities that need logging
ENTITIES_TO_UPDATE = [
    # Core entities
    "patient",
    "appointment",
    "appointment_type",
    # Medical records
    "visit",
    "soap_note",
    "diagnosis",
    "vaccination",
    "prescription",
    # Financial
    "service",
    "invoice",
    "invoice_item",
    "payment",
    # Inventory
    "vendor",
    "product",
    "purchase_order",
    "inventory_transaction",
    # Portal
    "client_portal_user",
    "appointment_request",
    "document",
    # Treatment
    "protocol",
    "treatment_plan",
]

# Key operations that need specialized logging
SPECIAL_OPERATIONS = {
    "appointment": [
        "check_in",
        "start_appointment",
        "complete_appointment",
        "cancel_appointment",
        "status_change",
    ],
    "invoice": ["generate_invoice", "send_invoice", "mark_paid"],
    "payment": ["process_payment", "refund_payment"],
    "inventory": ["receive_order", "adjust_stock", "low_stock_alert"],
}

# Performance decorator - add to all endpoints
PERFORMANCE_DECORATOR = "@log_performance_decorator"


def print_instructions():
    """Print instructions for adding logging"""
    print("=" * 80)
    print("AUDIT LOGGING IMPLEMENTATION GUIDE")
    print("=" * 80)
    print()
    print("Step 1: Add performance decorator to all endpoints")
    print("----------------------------------------")
    print(PERFORMANCE_DECORATOR)
    print()
    print("Step 2: For CREATE operations:")
    print("----------------------------------------")
    print(CREATE_TEMPLATE.format(Entity="Client", entity="client"))
    print()
    print("Step 3: For UPDATE operations:")
    print("----------------------------------------")
    print(UPDATE_TEMPLATE.format(Entity="Client", entity="client"))
    print()
    print("Step 4: For DELETE operations:")
    print("----------------------------------------")
    print(DELETE_TEMPLATE.format(Entity="Client", entity="client"))
    print()
    print("Step 5: For Status Changes:")
    print("----------------------------------------")
    print(STATUS_CHANGE_TEMPLATE.format(Entity="Appointment", entity="appointment"))
    print()
    print("Step 6: For Payments:")
    print("----------------------------------------")
    print(PAYMENT_TEMPLATE)
    print()
    print("=" * 80)
    print(f"Total entities to update: {len(ENTITIES_TO_UPDATE)}")
    print("=" * 80)
    print()
    print("Entities:")
    for entity in ENTITIES_TO_UPDATE:
        print(f"  - {entity}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    print_instructions()
