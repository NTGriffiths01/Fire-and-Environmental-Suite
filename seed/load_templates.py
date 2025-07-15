#!/usr/bin/env python3
"""
Seed script to load JSON schema templates into the database
"""
import sys
import os
import json
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Change to backend directory for database path
os.chdir(backend_dir)

from models import SessionLocal
from database_service import DatabaseService

def load_template_schemas():
    """Load JSON schema templates from seed directory"""
    print("🌱 Loading JSON schema templates...")
    
    seed_dir = Path(__file__).parent / "templates"
    db = SessionLocal()
    service = DatabaseService(db)
    
    try:
        # Get admin user for template creation
        admin_user = service.get_user_by_username("admin@madoc.gov")
        if not admin_user:
            print("❌ Admin user not found. Please run migration first.")
            return False
        
        # Load each template file
        for template_file in seed_dir.glob("*.json"):
            print(f"📄 Loading template: {template_file.name}")
            
            with open(template_file, 'r') as f:
                schema_data = json.load(f)
            
            # Create template in database
            template_name = schema_data.get("title", template_file.stem)
            template = service.create_template(
                name=template_name,
                schema=schema_data,
                created_by=admin_user.id
            )
            print(f"✅ Created template: {template.name} (ID: {template.id})")
        
        print("🎉 All templates loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error loading templates: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = load_template_schemas()
    sys.exit(0 if success else 1)