#!/usr/bin/env python3
"""
Seed script to populate compliance tracking system with facilities and functions
"""
import sys
import os
from pathlib import Path
from datetime import date

# Add backend directory to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Change to backend directory for database path
os.chdir(backend_dir)

from models import SessionLocal
from compliance_service import ComplianceService

# 17 Facilities as specified
FACILITIES = [
    {"name": "Bay State Correctional Center", "facility_type": "Correctional Center", "capacity": 1500},
    {"name": "Boston Pre-Release", "facility_type": "Pre-Release Center", "capacity": 200},
    {"name": "Bridgewater State Hospital", "facility_type": "State Hospital", "capacity": 600},
    {"name": "Bridgewater Warehouse", "facility_type": "Warehouse", "capacity": None},
    {"name": "Lemuel Shattuck Hospital", "facility_type": "Hospital", "capacity": 400},
    {"name": "MASAC@Plymouth", "facility_type": "Treatment Center", "capacity": 300},
    {"name": "Massachusetts Treatment Center", "facility_type": "Treatment Center", "capacity": 800},
    {"name": "MCI-Cedar Junction", "facility_type": "Maximum Security", "capacity": 1200},
    {"name": "MCI-Framingham", "facility_type": "Medium Security", "capacity": 600},
    {"name": "MCI-Norfolk", "facility_type": "Medium Security", "capacity": 1400},
    {"name": "MCI-Shirley", "facility_type": "Medium Security", "capacity": 1200},
    {"name": "Milford DOC Headquarters", "facility_type": "Administrative", "capacity": None},
    {"name": "NCCI Gardner", "facility_type": "Medium Security", "capacity": 900},
    {"name": "NECC", "facility_type": "Medium Security", "capacity": 1000},
    {"name": "Old Colony Correctional Center", "facility_type": "Medium Security", "capacity": 1000},
    {"name": "Pondville", "facility_type": "Medium Security", "capacity": 800},
    {"name": "Souza Baranowski Correctional Center", "facility_type": "Maximum Security", "capacity": 1200},
]

# Compliance functions based on the image and requirements
COMPLIANCE_FUNCTIONS = [
    {
        "name": "EHSO Weekly Inspection Reports",
        "description": "Environmental Health & Safety Office weekly inspection reports",
        "category": "EHSO",
        "default_frequency": "W",
        "citation_references": ["105 CMR 451.126", "DOC Policy 103.05"]
    },
    {
        "name": "Fire Alarm System",
        "description": "Fire alarm system inspection and testing",
        "category": "Fire Safety",
        "default_frequency": "M",
        "citation_references": ["NFPA 72", "ICC Fire Code 907"]
    },
    {
        "name": "Fire Pump Inspection",
        "description": "Fire pump inspection and testing",
        "category": "Fire Safety",
        "default_frequency": "M",
        "citation_references": ["NFPA 20", "ICC Fire Code 913"]
    },
    {
        "name": "Fire Department Inspection",
        "description": "Annual fire department inspection",
        "category": "Fire Safety",
        "default_frequency": "A",
        "citation_references": ["ICC Fire Code 106", "105 CMR 451.126"]
    },
    {
        "name": "Sprinkler Testing",
        "description": "Fire sprinkler system testing and maintenance",
        "category": "Fire Safety",
        "default_frequency": "Q",
        "citation_references": ["NFPA 25", "ICC Fire Code 901"]
    },
    {
        "name": "Ventilation Survey",
        "description": "HVAC and ventilation system survey",
        "category": "Environmental",
        "default_frequency": "SA",
        "citation_references": ["105 CMR 451.140", "ASHRAE 62.1"]
    },
    {
        "name": "State Building Certificate",
        "description": "State building certificate renewal",
        "category": "Building",
        "default_frequency": "A",
        "citation_references": ["780 CMR 1100", "105 CMR 451.120"]
    },
    {
        "name": "DPH Inspection",
        "description": "Department of Public Health inspection",
        "category": "Health",
        "default_frequency": "A",
        "citation_references": ["105 CMR 451", "DPH Regulations"]
    },
    {
        "name": "Medical Waste Bio-Haz Disposal",
        "description": "Medical waste and biohazard disposal compliance",
        "category": "Environmental",
        "default_frequency": "M",
        "citation_references": ["105 CMR 480", "40 CFR 259"]
    },
    {
        "name": "UST System Inspection",
        "description": "Underground storage tank system inspection",
        "category": "Environmental",
        "default_frequency": "A",
        "citation_references": ["527 CMR 9", "40 CFR 280"]
    },
    {
        "name": "Sound Tests (Day/Night)",
        "description": "Environmental noise level testing",
        "category": "Environmental",
        "default_frequency": "SA",
        "citation_references": ["310 CMR 7.10", "105 CMR 451.142"]
    },
    {
        "name": "Kitchen Hood Cleaning",
        "description": "Commercial kitchen hood cleaning and maintenance",
        "category": "Fire Safety",
        "default_frequency": "Q",
        "citation_references": ["NFPA 96", "ICC Fire Code 609"]
    },
    {
        "name": "Hydrant Flow Tests",
        "description": "Fire hydrant flow testing and maintenance",
        "category": "Fire Safety",
        "default_frequency": "A",
        "citation_references": ["NFPA 291", "ICC Fire Code 508"]
    },
    {
        "name": "Air Temperature Systems",
        "description": "HVAC air temperature system inspection",
        "category": "Environmental",
        "default_frequency": "Q",
        "citation_references": ["105 CMR 451.140", "ASHRAE 90.1"]
    },
    {
        "name": "Elevator Inspections",
        "description": "Elevator safety inspection and certification",
        "category": "Building",
        "default_frequency": "A",
        "citation_references": ["524 CMR 5.00", "ASME A17.1"]
    },
    {
        "name": "Pest Control",
        "description": "Integrated pest management and control",
        "category": "Environmental",
        "default_frequency": "M",
        "citation_references": ["105 CMR 451.144", "333 CMR 8.00"]
    },
    {
        "name": "Pressure Vessels",
        "description": "Pressure vessel inspection and certification",
        "category": "Building",
        "default_frequency": "A",
        "citation_references": ["520 CMR 3.00", "ASME BPVC"]
    },
    {
        "name": "Emergency Generator Testing",
        "description": "Emergency generator testing and maintenance",
        "category": "Building",
        "default_frequency": "M",
        "citation_references": ["NFPA 110", "ICC Fire Code 604"]
    },
    {
        "name": "Exit Sign Inspection",
        "description": "Emergency exit sign inspection and maintenance",
        "category": "Fire Safety",
        "default_frequency": "M",
        "citation_references": ["NFPA 101", "ICC Fire Code 1011"]
    },
    {
        "name": "Boiler Inspection",
        "description": "Boiler safety inspection and certification",
        "category": "Building",
        "default_frequency": "A",
        "citation_references": ["520 CMR 3.00", "ASME BPVC"]
    }
]

def seed_compliance_system():
    """Seed the compliance tracking system"""
    print("🌱 Seeding compliance tracking system...")
    
    db = SessionLocal()
    service = ComplianceService(db)
    
    try:
        # Create facilities
        print("\n📍 Creating facilities...")
        facility_ids = {}
        for facility_data in FACILITIES:
            facility = service.create_facility(
                name=facility_data["name"],
                facility_type=facility_data["facility_type"],
                capacity=facility_data["capacity"]
            )
            facility_ids[facility.name] = facility.id
            print(f"   ✅ Created facility: {facility.name}")
        
        # Create compliance functions
        print("\n🔧 Creating compliance functions...")
        function_ids = {}
        for function_data in COMPLIANCE_FUNCTIONS:
            function = service.create_compliance_function(
                name=function_data["name"],
                description=function_data["description"],
                category=function_data["category"],
                default_frequency=function_data["default_frequency"],
                citation_references=function_data["citation_references"]
            )
            function_ids[function.name] = function.id
            print(f"   ✅ Created function: {function.name} ({function.default_frequency})")
        
        # Create compliance schedules for each facility
        print("\n📅 Creating compliance schedules...")
        schedule_count = 0
        for facility_name, facility_id in facility_ids.items():
            for function_name, function_id in function_ids.items():
                # Get the function to use its default frequency
                function = service.get_compliance_function_by_id(function_id)
                
                schedule = service.create_compliance_schedule(
                    facility_id=facility_id,
                    function_id=function_id,
                    frequency=function.default_frequency,
                    start_date=date.today()
                )
                schedule_count += 1
            
            print(f"   ✅ Created {len(function_ids)} schedules for {facility_name}")
        
        print(f"\n🎉 Compliance system seeded successfully!")
        print(f"   📍 {len(facility_ids)} facilities created")
        print(f"   🔧 {len(function_ids)} compliance functions created")
        print(f"   📅 {schedule_count} compliance schedules created")
        
        return True
        
    except Exception as e:
        print(f"❌ Error seeding compliance system: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = seed_compliance_system()
    sys.exit(0 if success else 1)