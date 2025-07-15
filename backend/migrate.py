#!/usr/bin/env python3
"""
Database migration utility for Fire Safety Suite
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

load_dotenv()

def run_migration():
    """Run database migrations"""
    try:
        # Check if database exists and is accessible
        print("🔍 Checking database connection...")
        
        # Run Alembic migration
        print("📦 Running database migrations...")
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Database migrations completed successfully!")
            print(result.stdout)
        else:
            print("❌ Migration failed!")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False
    
    return True

def seed_initial_data():
    """Seed initial data after migration"""
    try:
        print("🌱 Seeding initial data...")
        
        from models import SessionLocal
        from database_service import DatabaseService
        import uuid
        
        db = SessionLocal()
        service = DatabaseService(db)
        
        # Create admin user
        admin_user = service.create_user(
            username="admin@madoc.gov",
            role="admin"
        )
        print(f"✅ Created admin user: {admin_user.username}")
        
        # Create default template
        template = service.create_template(
            name="Fire Safety Inspection",
            schema={
                "sections": [
                    {
                        "title": "Fire Doors",
                        "items": [
                            {"id": "fire_door_1", "label": "Fire doors properly maintained", "type": "checkbox"},
                            {"id": "fire_door_2", "label": "Self-closing mechanisms functional", "type": "checkbox"},
                            {"id": "fire_door_notes", "label": "Notes", "type": "textarea"}
                        ]
                    },
                    {
                        "title": "Emergency Exits",
                        "items": [
                            {"id": "exit_1", "label": "Exit signs illuminated", "type": "checkbox"},
                            {"id": "exit_2", "label": "Exit paths clear", "type": "checkbox"},
                            {"id": "exit_notes", "label": "Notes", "type": "textarea"}
                        ]
                    },
                    {
                        "title": "Fire Suppression",
                        "items": [
                            {"id": "sprinkler_1", "label": "Sprinkler system operational", "type": "checkbox"},
                            {"id": "extinguisher_1", "label": "Fire extinguishers accessible", "type": "checkbox"},
                            {"id": "suppression_notes", "label": "Notes", "type": "textarea"}
                        ]
                    }
                ]
            },
            created_by=str(admin_user.id)
        )
        print(f"✅ Created default template: {template.name}")
        
        db.close()
        print("✅ Initial data seeded successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        return False
    
    return True

def main():
    """Main migration command"""
    print("🚀 Starting Fire Safety Suite database setup...")
    
    if run_migration():
        if seed_initial_data():
            print("\n🎉 Database setup completed successfully!")
            print("\nDefault credentials:")
            print("  Username: admin@madoc.gov")
            print("  Password: admin123")
        else:
            print("\n⚠️  Migration completed but seeding failed.")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")

if __name__ == "__main__":
    main()