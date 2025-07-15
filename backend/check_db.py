#!/usr/bin/env python3
"""
Check database tables
"""
import sys
import os
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from models import engine
from sqlalchemy import inspect

def check_database():
    """Check database tables"""
    print("📊 Checking database tables...")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table}")
    
    return tables

if __name__ == "__main__":
    tables = check_database()
    if not tables:
        print("❌ No tables found")
        sys.exit(1)
    else:
        print("✅ Database tables found")
        sys.exit(0)