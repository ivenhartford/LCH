"""
Seed script to populate default data for the Lenox Cat Hospital database.

This script adds commonly used appointment types to help get started quickly.
Run with: python seed_data.py
"""

from app import create_app, db
from app.models import AppointmentType
import sys

def seed_appointment_types():
    """Create default appointment types for a cat hospital."""

    appointment_types = [
        {
            'name': 'Wellness Exam',
            'description': 'Annual wellness checkup and preventive care',
            'default_duration_minutes': 30,
            'color': '#10b981',  # Green
            'is_active': True
        },
        {
            'name': 'Sick Visit',
            'description': 'Examination for illness or injury',
            'default_duration_minutes': 30,
            'color': '#f59e0b',  # Amber/Orange
            'is_active': True
        },
        {
            'name': 'Vaccination',
            'description': 'Routine vaccination appointment',
            'default_duration_minutes': 15,
            'color': '#3b82f6',  # Blue
            'is_active': True
        },
        {
            'name': 'Surgery',
            'description': 'Surgical procedure',
            'default_duration_minutes': 120,
            'color': '#ef4444',  # Red
            'is_active': True
        },
        {
            'name': 'Dental Cleaning',
            'description': 'Professional dental cleaning and exam',
            'default_duration_minutes': 90,
            'color': '#8b5cf6',  # Purple
            'is_active': True
        },
        {
            'name': 'Grooming',
            'description': 'Grooming services',
            'default_duration_minutes': 60,
            'color': '#ec4899',  # Pink
            'is_active': True
        },
        {
            'name': 'Follow-up',
            'description': 'Follow-up appointment after treatment',
            'default_duration_minutes': 20,
            'color': '#14b8a6',  # Teal
            'is_active': True
        },
        {
            'name': 'Emergency',
            'description': 'Emergency visit',
            'default_duration_minutes': 60,
            'color': '#dc2626',  # Dark Red
            'is_active': True
        },
        {
            'name': 'Consultation',
            'description': 'General consultation',
            'default_duration_minutes': 30,
            'color': '#6366f1',  # Indigo
            'is_active': True
        },
        {
            'name': 'Lab Work',
            'description': 'Laboratory testing and sample collection',
            'default_duration_minutes': 20,
            'color': '#06b6d4',  # Cyan
            'is_active': True
        },
    ]

    added_count = 0
    skipped_count = 0

    for apt_type_data in appointment_types:
        # Check if appointment type already exists
        existing = AppointmentType.query.filter_by(name=apt_type_data['name']).first()

        if existing:
            print(f"⏭️  Skipping '{apt_type_data['name']}' - already exists")
            skipped_count += 1
            continue

        # Create new appointment type
        apt_type = AppointmentType(**apt_type_data)
        db.session.add(apt_type)
        print(f"✅ Added appointment type: {apt_type_data['name']} ({apt_type_data['color']})")
        added_count += 1

    try:
        db.session.commit()
        print(f"\n🎉 Seed complete! Added {added_count} appointment types, skipped {skipped_count} existing.")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error committing to database: {e}", file=sys.stderr)
        return False


def main():
    """Main function to run the seed script."""
    print("🌱 Starting seed script for Lenox Cat Hospital...")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        print("\n📋 Seeding Appointment Types...")
        print("-" * 60)

        success = seed_appointment_types()

        if success:
            print("\n✨ All done! Your database has been seeded with default data.")
            return 0
        else:
            print("\n⚠️  Seeding completed with errors. Please check the logs above.")
            return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
