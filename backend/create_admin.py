#!/usr/bin/env python
"""
Script to create an admin user in the database.
Run this from the backend folder: python create_admin.py
"""

from app import create_app, db
from app.models import Users

def create_admin():
    app = create_app('development')
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = Users.query.filter_by(email='admin@ulendo.local').first()
        if existing_admin:
            print(f"Admin user already exists: {existing_admin.name} ({existing_admin.email})")
            return
        
        # Create admin user
        admin = Users(
            name='System Administrator',
            email='admin@ulendo.local',
            phone_number='0999999999',
            role='admin'
        )
        admin.set_password('admin@123')  # Change this password in production!
        
        try:
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created successfully!")
            print(f"   Email/Phone: admin@ulendo.local or 0999999999")
            print(f"   Password: admin@123")
            print(f"   ID: {admin.id}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin: {e}")

if __name__ == '__main__':
    create_admin()
