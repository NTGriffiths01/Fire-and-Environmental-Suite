#!/usr/bin/env python3
"""
Test script to verify SQLite migration functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from models import SessionLocal, User, Template, Inspection, CorrectiveAction, AuditLog
from database_service import DatabaseService
from datetime import datetime, date
import json

def test_migration():
    """Test all migration functionality"""
    print("🧪 Testing SQLite migration functionality...")
    
    db = SessionLocal()
    service = DatabaseService(db)
    
    try:
        # Test 1: Verify user creation
        print("\n1. Testing user operations...")
        users = service.get_all_users()
        print(f"   ✅ Found {len(users)} users")
        
        if users:
            user = users[0]
            print(f"   ✅ Admin user: {user.username} (role: {user.role})")
        
        # Test 2: Verify template creation
        print("\n2. Testing template operations...")
        templates = service.get_all_templates()
        print(f"   ✅ Found {len(templates)} templates")
        
        if templates:
            template = templates[0]
            print(f"   ✅ Template: {template.name}")
            print(f"   ✅ Schema sections: {len(template.schema.get('sections', []))}")
        
        # Test 3: Create a test inspection
        print("\n3. Testing inspection operations...")
        if users and templates:
            test_inspection = service.create_inspection(
                template_id=templates[0].id,
                facility="Test Facility",
                payload={
                    "fire_door_1": True,
                    "fire_door_2": False,
                    "fire_door_notes": "Door 2 requires maintenance"
                },
                inspector_id=users[0].id
            )
            print(f"   ✅ Created inspection: {test_inspection.id}")
            
            # Test status update
            updated_inspection = service.update_inspection_status(
                test_inspection.id, 
                "submitted", 
                users[0].id
            )
            print(f"   ✅ Updated status to: {updated_inspection.status}")
        
        # Test 4: Create corrective action
        print("\n4. Testing corrective action operations...")
        if 'test_inspection' in locals():
            corrective_action = service.create_corrective_action(
                inspection_id=test_inspection.id,
                violation_ref="ICC-FC-907",
                action_plan="Repair fire door mechanism",
                due_date=date(2024, 8, 1)
            )
            print(f"   ✅ Created corrective action: {corrective_action.id}")
        
        # Test 5: Create audit log
        print("\n5. Testing audit log operations...")
        audit_log = service.create_audit_log(
            username="admin@madoc.gov",
            action="TEST_MIGRATION",
            ip_addr="127.0.0.1"
        )
        print(f"   ✅ Created audit log: {audit_log.id}")
        
        # Test 6: Statistics
        print("\n6. Testing statistics...")
        stats = service.get_statistics()
        print(f"   ✅ Total users: {stats['total_users']}")
        print(f"   ✅ Total templates: {stats['total_templates']}")
        print(f"   ✅ Total inspections: {stats['total_inspections']}")
        print(f"   ✅ Pending reviews: {stats['pending_reviews']}")
        
        print("\n🎉 All migration tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    success = test_migration()
    sys.exit(0 if success else 1)