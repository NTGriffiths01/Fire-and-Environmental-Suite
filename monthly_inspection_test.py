#!/usr/bin/env python3
"""
Monthly Inspection System Backend Testing Suite
Tests all Monthly Inspection System APIs comprehensively
"""

import requests
import json
import sys
from datetime import datetime, date
import uuid
import base64

# Configuration
BASE_URL = "https://c94b3df9-82b5-41bd-a80d-f821e8a6f0cc.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@madoc.gov"
ADMIN_PASSWORD = "admin123"

class MonthlyInspectionTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        self.facility_id = None
        self.inspection_id = None
        self.deficiency_id = None
        self.violation_code_id = None
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                self.log_result("Basic Connectivity", True, "API is accessible")
                return True
            else:
                self.log_result("Basic Connectivity", False, f"API returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Basic Connectivity", False, f"Connection error: {str(e)}")
            return False
    
    def test_admin_login(self):
        """Test admin authentication"""
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                self.log_result("Admin Login", True, "Admin authentication successful")
                return True
            else:
                self.log_result("Admin Login", False, f"Login failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Admin Login", False, f"Login error: {str(e)}")
            return False
    
    def get_facility_id(self):
        """Get a facility ID for testing"""
        try:
            response = self.session.get(f"{BASE_URL}/facilities")
            if response.status_code == 200:
                facilities = response.json()
                if facilities:
                    self.facility_id = facilities[0]["id"]
                    self.log_result("Get Facility ID", True, f"Using facility: {facilities[0]['name']}")
                    return True
                else:
                    self.log_result("Get Facility ID", False, "No facilities found")
                    return False
            else:
                self.log_result("Get Facility ID", False, f"Failed to get facilities: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Get Facility ID", False, f"Error getting facility: {str(e)}")
            return False
    
    def test_violation_codes_seed(self):
        """Test seeding violation codes"""
        try:
            response = self.session.post(f"{BASE_URL}/monthly-inspections/violation-codes/seed")
            if response.status_code == 200:
                result = response.json()
                self.log_result("Violation Codes Seed", True, 
                              f"Seeded {result['result']['created_count']} violation codes")
                return True
            else:
                self.log_result("Violation Codes Seed", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Violation Codes Seed", False, f"Error: {str(e)}")
            return False
    
    def test_violation_codes_get(self):
        """Test getting violation codes"""
        try:
            # Test basic get all violation codes
            response = self.session.get(f"{BASE_URL}/monthly-inspections/violation-codes")
            if response.status_code == 200:
                codes = response.json()
                self.log_result("Get Violation Codes", True, f"Retrieved {len(codes)} violation codes")
                
                if codes:
                    self.violation_code_id = codes[0]["id"]
                    
                    # Test filtering by code_type
                    response = self.session.get(f"{BASE_URL}/monthly-inspections/violation-codes?code_type=ICC")
                    if response.status_code == 200:
                        icc_codes = response.json()
                        self.log_result("Filter Violation Codes by Type", True, 
                                      f"Retrieved {len(icc_codes)} ICC codes")
                    else:
                        self.log_result("Filter Violation Codes by Type", False, 
                                      f"Failed with status {response.status_code}")
                    
                    # Test filtering by area_category
                    response = self.session.get(f"{BASE_URL}/monthly-inspections/violation-codes?area_category=fire_safety")
                    if response.status_code == 200:
                        fire_codes = response.json()
                        self.log_result("Filter Violation Codes by Area", True, 
                                      f"Retrieved {len(fire_codes)} fire safety codes")
                    else:
                        self.log_result("Filter Violation Codes by Area", False, 
                                      f"Failed with status {response.status_code}")
                    
                    # Test search functionality
                    response = self.session.get(f"{BASE_URL}/monthly-inspections/violation-codes?search=fire")
                    if response.status_code == 200:
                        search_codes = response.json()
                        self.log_result("Search Violation Codes", True, 
                                      f"Found {len(search_codes)} codes matching 'fire'")
                    else:
                        self.log_result("Search Violation Codes", False, 
                                      f"Failed with status {response.status_code}")
                    
                    return True
                else:
                    self.log_result("Get Violation Codes", False, "No violation codes found")
                    return False
            else:
                self.log_result("Get Violation Codes", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Get Violation Codes", False, f"Error: {str(e)}")
            return False
    
    def test_violation_codes_by_area(self):
        """Test getting violation codes grouped by area"""
        try:
            response = self.session.get(f"{BASE_URL}/monthly-inspections/violation-codes/by-area")
            if response.status_code == 200:
                grouped_codes = response.json()
                total_codes = sum(len(codes) for codes in grouped_codes.values())
                self.log_result("Get Violation Codes by Area", True, 
                              f"Retrieved codes grouped into {len(grouped_codes)} areas, total {total_codes} codes")
                return True
            else:
                self.log_result("Get Violation Codes by Area", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Get Violation Codes by Area", False, f"Error: {str(e)}")
            return False
    
    def test_create_violation_code(self):
        """Test creating a new violation code"""
        try:
            code_data = {
                "code_type": "TEST",
                "code_number": "TEST-001",
                "title": "Test Violation Code",
                "section": "1.1",
                "description": "Test violation code for testing purposes",
                "severity_level": "medium",
                "area_category": "testing"
            }
            
            response = self.session.post(f"{BASE_URL}/monthly-inspections/violation-codes", data=code_data)
            if response.status_code == 200:
                result = response.json()
                self.log_result("Create Violation Code", True, 
                              f"Created violation code: {result['violation_code']['code_number']}")
                return True
            else:
                self.log_result("Create Violation Code", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Create Violation Code", False, f"Error: {str(e)}")
            return False
    
    def test_upload_violation_pdf(self):
        """Test uploading violation code PDF"""
        try:
            # Create a simple test PDF content (base64 encoded)
            test_pdf_content = b"Test PDF content for violation codes"
            
            files = {"file": ("test_violation.pdf", test_pdf_content, "application/pdf")}
            data = {
                "code_type": "TEST",
                "uploaded_by": "admin@madoc.gov",
                "description": "Test PDF upload for violation codes"
            }
            
            response = self.session.post(f"{BASE_URL}/monthly-inspections/violation-codes/upload-pdf", 
                                       files=files, data=data)
            if response.status_code == 200:
                result = response.json()
                self.log_result("Upload Violation PDF", True, 
                              f"PDF uploaded successfully with ID: {result['pdf_id']}")
                return True
            else:
                self.log_result("Upload Violation PDF", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Upload Violation PDF", False, f"Error: {str(e)}")
            return False
    
    def test_auto_generate_inspections(self):
        """Test auto-generating monthly inspections"""
        try:
            current_date = datetime.now()
            data = {
                "target_year": current_date.year,
                "target_month": current_date.month
            }
            
            response = self.session.post(f"{BASE_URL}/monthly-inspections/auto-generate", data=data)
            if response.status_code == 200:
                result = response.json()
                self.log_result("Auto Generate Inspections", True, 
                              f"Generated {result['result']['created_count']} monthly inspections")
                return True
            else:
                self.log_result("Auto Generate Inspections", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Auto Generate Inspections", False, f"Error: {str(e)}")
            return False
    
    def test_create_monthly_inspection(self):
        """Test creating a monthly inspection"""
        try:
            if not self.facility_id:
                self.log_result("Create Monthly Inspection", False, "No facility ID available")
                return False
            
            current_date = datetime.now()
            data = {
                "facility_id": self.facility_id,
                "year": current_date.year,
                "month": current_date.month,
                "created_by": "admin@madoc.gov"
            }
            
            response = self.session.post(f"{BASE_URL}/monthly-inspections/create", data=data)
            if response.status_code == 200:
                result = response.json()
                self.inspection_id = result["inspection"]["id"]
                self.log_result("Create Monthly Inspection", True, 
                              f"Created inspection with ID: {self.inspection_id}")
                return True
            else:
                self.log_result("Create Monthly Inspection", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Create Monthly Inspection", False, f"Error: {str(e)}")
            return False
    
    def test_get_monthly_inspection(self):
        """Test getting monthly inspection by ID"""
        try:
            if not self.inspection_id:
                self.log_result("Get Monthly Inspection", False, "No inspection ID available")
                return False
            
            response = self.session.get(f"{BASE_URL}/monthly-inspections/{self.inspection_id}")
            if response.status_code == 200:
                inspection = response.json()
                self.log_result("Get Monthly Inspection", True, 
                              f"Retrieved inspection for facility {inspection['facility_id']}")
                return True
            else:
                self.log_result("Get Monthly Inspection", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Get Monthly Inspection", False, f"Error: {str(e)}")
            return False
    
    def test_get_inspections_by_facility(self):
        """Test getting inspections by facility"""
        try:
            if not self.facility_id:
                self.log_result("Get Inspections by Facility", False, "No facility ID available")
                return False
            
            response = self.session.get(f"{BASE_URL}/monthly-inspections/facility/{self.facility_id}")
            if response.status_code == 200:
                inspections = response.json()
                self.log_result("Get Inspections by Facility", True, 
                              f"Retrieved {len(inspections)} inspections for facility")
                
                # Test with year filter
                current_year = datetime.now().year
                response = self.session.get(f"{BASE_URL}/monthly-inspections/facility/{self.facility_id}?year={current_year}")
                if response.status_code == 200:
                    year_inspections = response.json()
                    self.log_result("Get Inspections by Facility with Year Filter", True, 
                                  f"Retrieved {len(year_inspections)} inspections for {current_year}")
                else:
                    self.log_result("Get Inspections by Facility with Year Filter", False, 
                                  f"Failed with status {response.status_code}")
                
                return True
            else:
                self.log_result("Get Inspections by Facility", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Get Inspections by Facility", False, f"Error: {str(e)}")
            return False
    
    def test_update_inspection_form_data(self):
        """Test updating inspection form data"""
        try:
            if not self.inspection_id:
                self.log_result("Update Inspection Form Data", False, "No inspection ID available")
                return False
            
            form_data = {
                "fire_alarm_tested": True,
                "smoke_detectors_functional": True,
                "sprinkler_system_functional": False,
                "exits_clear": True,
                "notes": "Test form data update"
            }
            
            data = {
                "form_data": json.dumps(form_data)
            }
            
            response = self.session.put(f"{BASE_URL}/monthly-inspections/{self.inspection_id}/form-data", 
                                      data=data)
            if response.status_code == 200:
                result = response.json()
                self.log_result("Update Inspection Form Data", True, 
                              "Form data updated successfully")
                return True
            else:
                self.log_result("Update Inspection Form Data", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Update Inspection Form Data", False, f"Error: {str(e)}")
            return False
    
    def test_add_inspection_deficiency(self):
        """Test adding deficiency to inspection"""
        try:
            if not self.inspection_id:
                self.log_result("Add Inspection Deficiency", False, "No inspection ID available")
                return False
            
            deficiency_data = {
                "area_type": "fire_safety",
                "description": "Fire extinguisher missing from corridor",
                "location": "Building A, Corridor 1",
                "citation_code": "ICC-FC-906",
                "citation_section": "906.1",
                "severity": "high",
                "corrective_action": "Install fire extinguisher",
                "target_completion_date": "2024-02-15"
            }
            
            if self.violation_code_id:
                deficiency_data["violation_code_id"] = self.violation_code_id
            
            response = self.session.post(f"{BASE_URL}/monthly-inspections/{self.inspection_id}/deficiencies", 
                                       data=deficiency_data)
            if response.status_code == 200:
                result = response.json()
                self.deficiency_id = result["deficiency"]["id"]
                self.log_result("Add Inspection Deficiency", True, 
                              f"Added deficiency with ID: {self.deficiency_id}")
                return True
            else:
                self.log_result("Add Inspection Deficiency", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Add Inspection Deficiency", False, f"Error: {str(e)}")
            return False
    
    def test_get_inspection_deficiencies(self):
        """Test getting inspection deficiencies"""
        try:
            if not self.inspection_id:
                self.log_result("Get Inspection Deficiencies", False, "No inspection ID available")
                return False
            
            response = self.session.get(f"{BASE_URL}/monthly-inspections/{self.inspection_id}/deficiencies")
            if response.status_code == 200:
                deficiencies = response.json()
                self.log_result("Get Inspection Deficiencies", True, 
                              f"Retrieved {len(deficiencies)} deficiencies")
                return True
            else:
                self.log_result("Get Inspection Deficiencies", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Get Inspection Deficiencies", False, f"Error: {str(e)}")
            return False
    
    def test_update_deficiency_status(self):
        """Test updating deficiency status"""
        try:
            if not self.deficiency_id:
                self.log_result("Update Deficiency Status", False, "No deficiency ID available")
                return False
            
            data = {
                "status": "resolved",
                "completed_by": "admin@madoc.gov"
            }
            
            response = self.session.put(f"{BASE_URL}/monthly-inspections/deficiencies/{self.deficiency_id}/status", 
                                      data=data)
            if response.status_code == 200:
                result = response.json()
                self.log_result("Update Deficiency Status", True, 
                              "Deficiency status updated to resolved")
                return True
            else:
                self.log_result("Update Deficiency Status", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Update Deficiency Status", False, f"Error: {str(e)}")
            return False
    
    def test_add_inspector_signature(self):
        """Test adding inspector signature"""
        try:
            if not self.inspection_id:
                self.log_result("Add Inspector Signature", False, "No inspection ID available")
                return False
            
            signature_data = {
                "signature_type": "inspector",
                "signed_by": "admin@madoc.gov",
                "signature_data": "inspector_signature_data_base64",
                "ip_address": "127.0.0.1",
                "user_agent": "Test Agent"
            }
            
            response = self.session.post(f"{BASE_URL}/monthly-inspections/{self.inspection_id}/signature", 
                                       data=signature_data)
            if response.status_code == 200:
                result = response.json()
                self.log_result("Add Inspector Signature", True, 
                              f"Inspector signature added successfully")
                return True
            else:
                self.log_result("Add Inspector Signature", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Add Inspector Signature", False, f"Error: {str(e)}")
            return False
    
    def test_add_deputy_signature(self):
        """Test adding deputy signature"""
        try:
            if not self.inspection_id:
                self.log_result("Add Deputy Signature", False, "No inspection ID available")
                return False
            
            signature_data = {
                "signature_type": "deputy",
                "signed_by": "admin@madoc.gov",
                "signature_data": "deputy_signature_data_base64",
                "ip_address": "127.0.0.1",
                "user_agent": "Test Agent"
            }
            
            response = self.session.post(f"{BASE_URL}/monthly-inspections/{self.inspection_id}/signature", 
                                       data=signature_data)
            if response.status_code == 200:
                result = response.json()
                self.log_result("Add Deputy Signature", True, 
                              f"Deputy signature added successfully")
                return True
            else:
                self.log_result("Add Deputy Signature", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Add Deputy Signature", False, f"Error: {str(e)}")
            return False
    
    def test_get_inspection_signatures(self):
        """Test getting inspection signatures"""
        try:
            if not self.inspection_id:
                self.log_result("Get Inspection Signatures", False, "No inspection ID available")
                return False
            
            response = self.session.get(f"{BASE_URL}/monthly-inspections/{self.inspection_id}/signatures")
            if response.status_code == 200:
                signatures = response.json()
                self.log_result("Get Inspection Signatures", True, 
                              f"Retrieved {len(signatures)} signatures")
                return True
            else:
                self.log_result("Get Inspection Signatures", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Get Inspection Signatures", False, f"Error: {str(e)}")
            return False
    
    def test_inspection_statistics(self):
        """Test getting inspection statistics"""
        try:
            # Test general statistics
            response = self.session.get(f"{BASE_URL}/monthly-inspections/statistics")
            if response.status_code == 200:
                stats = response.json()
                self.log_result("Get Inspection Statistics", True, 
                              f"Retrieved statistics: {stats['total_inspections']} total inspections")
                
                # Test facility-specific statistics
                if self.facility_id:
                    response = self.session.get(f"{BASE_URL}/monthly-inspections/statistics?facility_id={self.facility_id}")
                    if response.status_code == 200:
                        facility_stats = response.json()
                        self.log_result("Get Facility Statistics", True, 
                                      f"Retrieved facility statistics: {facility_stats['total_inspections']} inspections")
                    else:
                        self.log_result("Get Facility Statistics", False, 
                                      f"Failed with status {response.status_code}")
                
                # Test year-specific statistics
                current_year = datetime.now().year
                response = self.session.get(f"{BASE_URL}/monthly-inspections/statistics?year={current_year}")
                if response.status_code == 200:
                    year_stats = response.json()
                    self.log_result("Get Year Statistics", True, 
                                  f"Retrieved {current_year} statistics: {year_stats['total_inspections']} inspections")
                else:
                    self.log_result("Get Year Statistics", False, 
                                  f"Failed with status {response.status_code}")
                
                return True
            else:
                self.log_result("Get Inspection Statistics", False, 
                              f"Failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Get Inspection Statistics", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all monthly inspection tests in sequence"""
        print("🚀 Starting Monthly Inspection System Backend Tests")
        print("=" * 70)
        
        # Basic connectivity and authentication
        if not self.test_basic_connectivity():
            print("❌ Basic connectivity failed. Stopping tests.")
            return False
        
        if not self.test_admin_login():
            print("❌ Admin login failed. Stopping tests.")
            return False
        
        if not self.get_facility_id():
            print("❌ Could not get facility ID. Stopping tests.")
            return False
        
        # Violation Codes System Tests
        print("\n" + "=" * 70)
        print("📋 TESTING VIOLATION CODES SYSTEM")
        print("=" * 70)
        
        self.test_violation_codes_seed()
        self.test_violation_codes_get()
        self.test_violation_codes_by_area()
        self.test_create_violation_code()
        self.test_upload_violation_pdf()
        
        # Monthly Inspection Core Tests
        print("\n" + "=" * 70)
        print("🔍 TESTING MONTHLY INSPECTION CORE FUNCTIONALITY")
        print("=" * 70)
        
        self.test_auto_generate_inspections()
        self.test_create_monthly_inspection()
        self.test_get_monthly_inspection()
        self.test_get_inspections_by_facility()
        self.test_update_inspection_form_data()
        
        # Deficiency Management Tests
        print("\n" + "=" * 70)
        print("⚠️  TESTING DEFICIENCY MANAGEMENT")
        print("=" * 70)
        
        self.test_add_inspection_deficiency()
        self.test_get_inspection_deficiencies()
        self.test_update_deficiency_status()
        
        # Signature Workflow Tests
        print("\n" + "=" * 70)
        print("✍️  TESTING SIGNATURE WORKFLOW")
        print("=" * 70)
        
        self.test_add_inspector_signature()
        self.test_add_deputy_signature()
        self.test_get_inspection_signatures()
        
        # Statistics Tests
        print("\n" + "=" * 70)
        print("📊 TESTING STATISTICS")
        print("=" * 70)
        
        self.test_inspection_statistics()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return failed == 0

if __name__ == "__main__":
    tester = MonthlyInspectionTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)