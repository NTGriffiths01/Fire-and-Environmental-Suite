#!/usr/bin/env python3
"""
Comprehensive Backend Testing Suite for Fire and Environmental Safety Suite
Tests all backend APIs systematically with proper authentication and role-based access control
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://d3c89639-d3ec-46ee-978a-58e8387c6aad.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@madoc.gov"
ADMIN_PASSWORD = "admin123"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.inspector_token = None
        self.deputy_token = None
        self.test_results = []
        self.facility_id = None
        self.template_id = None
        self.inspection_id = None
        
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
                data = response.json()
                self.log_result("Basic Connectivity", True, "API is accessible", {"response": data})
                return True
            else:
                self.log_result("Basic Connectivity", False, f"API returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Basic Connectivity", False, f"Connection failed: {str(e)}")
            return False
    
    def test_admin_login(self):
        """Test admin login and token generation"""
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                user_info = data["user"]
                
                if user_info["role"] == "admin" and user_info["email"] == ADMIN_EMAIL:
                    self.log_result("Admin Login", True, "Admin login successful", {
                        "user_id": user_info["id"],
                        "role": user_info["role"],
                        "token_type": data["token_type"]
                    })
                    return True
                else:
                    self.log_result("Admin Login", False, "Invalid user data returned", {"user": user_info})
                    return False
            else:
                self.log_result("Admin Login", False, f"Login failed with status {response.status_code}", 
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Admin Login", False, f"Login error: {str(e)}")
            return False
    
    def test_user_registration(self):
        """Test user registration functionality"""
        try:
            # Create inspector user
            inspector_data = {
                "email": "inspector.smith@madoc.gov",
                "full_name": "Inspector John Smith",
                "role": "inspector",
                "password": "inspector123"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/register", json=inspector_data)
            
            if response.status_code == 200:
                user = response.json()
                self.log_result("User Registration - Inspector", True, "Inspector user created successfully", {
                    "user_id": user["id"],
                    "email": user["email"],
                    "role": user["role"]
                })
                
                # Test login with new inspector
                login_response = self.session.post(f"{BASE_URL}/auth/login", json={
                    "email": inspector_data["email"],
                    "password": inspector_data["password"]
                })
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    self.inspector_token = login_data["access_token"]
                    self.log_result("Inspector Login", True, "Inspector login successful")
                else:
                    self.log_result("Inspector Login", False, "Inspector login failed after registration")
                
                return True
            else:
                self.log_result("User Registration - Inspector", False, 
                              f"Registration failed with status {response.status_code}", 
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("User Registration - Inspector", False, f"Registration error: {str(e)}")
            return False
    
    def test_deputy_user_creation(self):
        """Test deputy user creation (admin only)"""
        try:
            if not self.admin_token:
                self.log_result("Deputy User Creation", False, "No admin token available")
                return False
            
            deputy_data = {
                "email": "deputy.johnson@madoc.gov",
                "full_name": "Deputy Operations Manager Johnson",
                "role": "deputy_of_operations",
                "password": "deputy123"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/register", json=deputy_data)
            
            if response.status_code == 200:
                user = response.json()
                self.log_result("Deputy User Creation", True, "Deputy user created successfully", {
                    "user_id": user["id"],
                    "role": user["role"]
                })
                
                # Test deputy login
                login_response = self.session.post(f"{BASE_URL}/auth/login", json={
                    "email": deputy_data["email"],
                    "password": deputy_data["password"]
                })
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    self.deputy_token = login_data["access_token"]
                    self.log_result("Deputy Login", True, "Deputy login successful")
                else:
                    self.log_result("Deputy Login", False, "Deputy login failed after creation")
                
                return True
            else:
                self.log_result("Deputy User Creation", False, 
                              f"Creation failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Deputy User Creation", False, f"Creation error: {str(e)}")
            return False
    
    def test_auth_me_endpoint(self):
        """Test /auth/me endpoint with different tokens"""
        try:
            # Test with admin token
            if self.admin_token:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                response = self.session.get(f"{BASE_URL}/auth/me", headers=headers)
                
                if response.status_code == 200:
                    user = response.json()
                    if user["role"] == "admin":
                        self.log_result("Auth Me - Admin", True, "Admin user info retrieved correctly")
                    else:
                        self.log_result("Auth Me - Admin", False, "Wrong role returned for admin")
                else:
                    self.log_result("Auth Me - Admin", False, f"Failed with status {response.status_code}")
            
            # Test with inspector token
            if self.inspector_token:
                headers = {"Authorization": f"Bearer {self.inspector_token}"}
                response = self.session.get(f"{BASE_URL}/auth/me", headers=headers)
                
                if response.status_code == 200:
                    user = response.json()
                    if user["role"] == "inspector":
                        self.log_result("Auth Me - Inspector", True, "Inspector user info retrieved correctly")
                    else:
                        self.log_result("Auth Me - Inspector", False, "Wrong role returned for inspector")
                else:
                    self.log_result("Auth Me - Inspector", False, f"Failed with status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Auth Me Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_facility_management(self):
        """Test facility CRUD operations"""
        try:
            if not self.admin_token:
                self.log_result("Facility Management", False, "No admin token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test GET facilities
            response = self.session.get(f"{BASE_URL}/facilities", headers=headers)
            if response.status_code == 200:
                facilities = response.json()
                self.log_result("Get Facilities", True, f"Retrieved {len(facilities)} facilities")
                
                # Store first facility ID for later use
                if facilities:
                    self.facility_id = facilities[0]["id"]
            else:
                self.log_result("Get Facilities", False, f"Failed with status {response.status_code}")
                return False
            
            # Test CREATE facility (admin only)
            facility_data = {
                "name": "MCI-Framingham",
                "address": "1 Administration Way, Framingham, MA 01702",
                "facility_type": "Medium Security",
                "capacity": 800
            }
            
            response = self.session.post(f"{BASE_URL}/facilities", json=facility_data, headers=headers)
            if response.status_code == 200:
                facility = response.json()
                self.log_result("Create Facility", True, "Facility created successfully", {
                    "facility_id": facility["id"],
                    "name": facility["name"]
                })
                if not self.facility_id:  # Use this if no default facility
                    self.facility_id = facility["id"]
            else:
                self.log_result("Create Facility", False, f"Failed with status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Facility Management", False, f"Error: {str(e)}")
            return False
    
    def test_inspection_templates(self):
        """Test inspection template system"""
        try:
            if not self.admin_token:
                self.log_result("Inspection Templates", False, "No admin token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test GET templates
            response = self.session.get(f"{BASE_URL}/templates", headers=headers)
            if response.status_code == 200:
                templates = response.json()
                self.log_result("Get Templates", True, f"Retrieved {len(templates)} templates")
                
                # Store first template ID for later use
                if templates:
                    self.template_id = templates[0]["id"]
                    
                    # Test GET specific template
                    template_response = self.session.get(f"{BASE_URL}/templates/{self.template_id}", headers=headers)
                    if template_response.status_code == 200:
                        template = template_response.json()
                        self.log_result("Get Specific Template", True, "Template retrieved successfully", {
                            "template_id": template["id"],
                            "name": template["name"],
                            "has_template_data": "template_data" in template
                        })
                    else:
                        self.log_result("Get Specific Template", False, f"Failed with status {template_response.status_code}")
            else:
                self.log_result("Get Templates", False, f"Failed with status {response.status_code}")
                return False
            
            # Test CREATE template (admin only)
            template_data = {
                "name": "Weekly Environmental Safety Check",
                "description": "Weekly environmental safety inspection checklist",
                "template_data": {
                    "sections": [
                        {
                            "title": "Air Quality",
                            "fields": [
                                {"name": "ventilation_adequate", "type": "checkbox", "label": "Ventilation adequate"},
                                {"name": "air_quality_notes", "type": "textarea", "label": "Air quality notes"}
                            ]
                        },
                        {
                            "title": "Water Systems",
                            "fields": [
                                {"name": "water_pressure_ok", "type": "checkbox", "label": "Water pressure adequate"},
                                {"name": "water_notes", "type": "textarea", "label": "Water system notes"}
                            ]
                        }
                    ]
                },
                "created_by": "admin",  # This field is required
                "is_active": True
            }
            
            response = self.session.post(f"{BASE_URL}/templates", json=template_data, headers=headers)
            if response.status_code == 200:
                template = response.json()
                self.log_result("Create Template", True, "Template created successfully", {
                    "template_id": template["id"],
                    "name": template["name"]
                })
                if not self.template_id:  # Use this if no default template
                    self.template_id = template["id"]
            else:
                self.log_result("Create Template", False, f"Failed with status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Inspection Templates", False, f"Error: {str(e)}")
            return False
    
    def test_inspection_forms(self):
        """Test inspection form management with status transitions"""
        try:
            if not self.inspector_token or not self.template_id or not self.facility_id:
                self.log_result("Inspection Forms", False, "Missing required tokens or IDs")
                return False
            
            inspector_headers = {"Authorization": f"Bearer {self.inspector_token}"}
            
            # Test CREATE inspection (inspector)
            inspection_data = {
                "template_id": self.template_id,
                "facility_id": self.facility_id,
                "inspection_date": datetime.now().isoformat(),
                "form_data": {
                    "alarm_functional": True,
                    "alarm_notes": "All fire alarms tested and functional",
                    "sprinkler_functional": True,
                    "sprinkler_notes": "Sprinkler system pressure normal",
                    "exits_clear": True,
                    "exit_notes": "All emergency exits clear and properly marked"
                },
                "status": "draft"
            }
            
            response = self.session.post(f"{BASE_URL}/inspections", json=inspection_data, headers=inspector_headers)
            if response.status_code == 200:
                inspection = response.json()
                self.inspection_id = inspection["id"]
                self.log_result("Create Inspection", True, "Inspection created successfully", {
                    "inspection_id": inspection["id"],
                    "status": inspection["status"]
                })
            else:
                self.log_result("Create Inspection", False, f"Failed with status {response.status_code}")
                return False
            
            # Test GET inspections (inspector should see their own)
            response = self.session.get(f"{BASE_URL}/inspections", headers=inspector_headers)
            if response.status_code == 200:
                inspections = response.json()
                self.log_result("Get Inspections - Inspector", True, f"Inspector retrieved {len(inspections)} inspections")
            else:
                self.log_result("Get Inspections - Inspector", False, f"Failed with status {response.status_code}")
            
            # Test UPDATE inspection
            update_data = inspection_data.copy()
            update_data["form_data"]["alarm_notes"] = "Updated: All fire alarms tested and functional - monthly check completed"
            update_data["id"] = self.inspection_id
            
            response = self.session.put(f"{BASE_URL}/inspections/{self.inspection_id}", json=update_data, headers=inspector_headers)
            if response.status_code == 200:
                updated_inspection = response.json()
                self.log_result("Update Inspection", True, "Inspection updated successfully")
            else:
                self.log_result("Update Inspection", False, f"Failed with status {response.status_code}")
            
            # Test SUBMIT inspection (status transition: draft -> submitted)
            response = self.session.post(f"{BASE_URL}/inspections/{self.inspection_id}/submit", headers=inspector_headers)
            if response.status_code == 200:
                self.log_result("Submit Inspection", True, "Inspection submitted successfully")
            else:
                self.log_result("Submit Inspection", False, f"Failed with status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Inspection Forms", False, f"Error: {str(e)}")
            return False
    
    def test_inspection_review_process(self):
        """Test inspection review process (deputy operations)"""
        try:
            if not self.deputy_token or not self.inspection_id:
                self.log_result("Inspection Review", False, "Missing deputy token or inspection ID")
                return False
            
            deputy_headers = {"Authorization": f"Bearer {self.deputy_token}"}
            
            # Test GET inspections (deputy should see submitted ones)
            response = self.session.get(f"{BASE_URL}/inspections", headers=deputy_headers)
            if response.status_code == 200:
                inspections = response.json()
                self.log_result("Get Inspections - Deputy", True, f"Deputy retrieved {len(inspections)} inspections for review")
            else:
                self.log_result("Get Inspections - Deputy", False, f"Failed with status {response.status_code}")
            
            # Test APPROVE inspection (status transition: submitted -> approved)
            review_data = {
                "action": "approve",
                "comments": "Inspection completed thoroughly. All safety systems are functioning properly."
            }
            
            response = self.session.post(f"{BASE_URL}/inspections/{self.inspection_id}/review", 
                                       json=review_data, headers=deputy_headers)
            if response.status_code == 200:
                self.log_result("Approve Inspection", True, "Inspection approved successfully")
            else:
                self.log_result("Approve Inspection", False, f"Failed with status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Inspection Review", False, f"Error: {str(e)}")
            return False
    
    def test_citation_system(self):
        """Test citation suggestion engine"""
        try:
            if not self.inspector_token:
                self.log_result("Citation System", False, "No inspector token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.inspector_token}"}
            
            # Test GET citations
            response = self.session.get(f"{BASE_URL}/citations", headers=headers)
            if response.status_code == 200:
                citations = response.json()
                self.log_result("Get Citations", True, f"Retrieved {len(citations)} citations")
            else:
                self.log_result("Get Citations", False, f"Failed with status {response.status_code}")
                return False
            
            # Test citation suggestions
            test_findings = [
                "Fire alarm system not responding properly",
                "Emergency exit door blocked by equipment",
                "Sprinkler system pressure below normal range"
            ]
            
            for finding in test_findings:
                # Use query parameter instead of JSON body
                response = self.session.post(f"{BASE_URL}/citations/suggest?finding={finding}", 
                                           headers=headers)
                if response.status_code == 200:
                    suggestions = response.json()
                    self.log_result(f"Citation Suggestion - {finding[:30]}...", True, 
                                  f"Got {len(suggestions.get('suggestions', []))} suggestions")
                else:
                    self.log_result(f"Citation Suggestion - {finding[:30]}...", False, 
                                  f"Failed with status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Citation System", False, f"Error: {str(e)}")
            return False
    
    def test_file_upload(self):
        """Test file upload system"""
        try:
            if not self.inspector_token:
                self.log_result("File Upload", False, "No inspector token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.inspector_token}"}
            
            # Create a test file content
            test_content = "This is a test inspection report document.\nInspection completed on " + datetime.now().strftime("%Y-%m-%d")
            
            # Prepare file upload
            files = {
                'file': ('test_inspection_report.txt', test_content, 'text/plain')
            }
            
            response = self.session.post(f"{BASE_URL}/upload", files=files, headers=headers)
            if response.status_code == 200:
                result = response.json()
                self.log_result("File Upload", True, "File uploaded successfully", {
                    "file_id": result.get("file_id"),
                    "filename": result.get("filename")
                })
            else:
                self.log_result("File Upload", False, f"Failed with status {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_result("File Upload", False, f"Error: {str(e)}")
            return False
    
    def test_dashboard_statistics(self):
        """Test role-based dashboard statistics"""
        try:
            # Test admin dashboard stats
            if self.admin_token:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                response = self.session.get(f"{BASE_URL}/dashboard/stats", headers=headers)
                if response.status_code == 200:
                    stats = response.json()
                    expected_keys = ["total_users", "total_facilities", "total_inspections", "pending_reviews"]
                    if all(key in stats for key in expected_keys):
                        self.log_result("Dashboard Stats - Admin", True, "Admin dashboard stats retrieved", stats)
                    else:
                        self.log_result("Dashboard Stats - Admin", False, "Missing expected stats keys")
                else:
                    self.log_result("Dashboard Stats - Admin", False, f"Failed with status {response.status_code}")
            
            # Test inspector dashboard stats
            if self.inspector_token:
                headers = {"Authorization": f"Bearer {self.inspector_token}"}
                response = self.session.get(f"{BASE_URL}/dashboard/stats", headers=headers)
                if response.status_code == 200:
                    stats = response.json()
                    expected_keys = ["my_inspections", "draft_inspections", "submitted_inspections"]
                    if all(key in stats for key in expected_keys):
                        self.log_result("Dashboard Stats - Inspector", True, "Inspector dashboard stats retrieved", stats)
                    else:
                        self.log_result("Dashboard Stats - Inspector", False, "Missing expected stats keys")
                else:
                    self.log_result("Dashboard Stats - Inspector", False, f"Failed with status {response.status_code}")
            
            # Test deputy dashboard stats
            if self.deputy_token:
                headers = {"Authorization": f"Bearer {self.deputy_token}"}
                response = self.session.get(f"{BASE_URL}/dashboard/stats", headers=headers)
                if response.status_code == 200:
                    stats = response.json()
                    expected_keys = ["pending_reviews", "approved_inspections", "rejected_inspections"]
                    if all(key in stats for key in expected_keys):
                        self.log_result("Dashboard Stats - Deputy", True, "Deputy dashboard stats retrieved", stats)
                    else:
                        self.log_result("Dashboard Stats - Deputy", False, "Missing expected stats keys")
                else:
                    self.log_result("Dashboard Stats - Deputy", False, f"Failed with status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Dashboard Statistics", False, f"Error: {str(e)}")
            return False
    
    def test_audit_logging(self):
        """Test audit logging system (admin only)"""
        try:
            if not self.admin_token:
                self.log_result("Audit Logging", False, "No admin token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test GET audit logs (admin only)
            response = self.session.get(f"{BASE_URL}/audit-logs", headers=headers)
            if response.status_code == 200:
                logs = response.json()
                self.log_result("Get Audit Logs", True, f"Retrieved {len(logs)} audit log entries")
                
                # Check if logs have expected structure
                if logs and len(logs) > 0:
                    log_entry = logs[0]
                    expected_fields = ["id", "user_id", "action", "resource_type", "timestamp"]
                    if all(field in log_entry for field in expected_fields):
                        self.log_result("Audit Log Structure", True, "Audit logs have correct structure")
                    else:
                        self.log_result("Audit Log Structure", False, "Audit logs missing expected fields")
                
            else:
                self.log_result("Get Audit Logs", False, f"Failed with status {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_result("Audit Logging", False, f"Error: {str(e)}")
            return False
    
    def test_role_based_access_control(self):
        """Test role-based access control enforcement"""
        try:
            # Test inspector trying to access admin-only endpoints
            if self.inspector_token:
                headers = {"Authorization": f"Bearer {self.inspector_token}"}
                
                # Inspector should NOT be able to create facilities
                facility_data = {
                    "name": "Test Facility",
                    "address": "Test Address",
                    "facility_type": "Test",
                    "capacity": 100
                }
                response = self.session.post(f"{BASE_URL}/facilities", json=facility_data, headers=headers)
                if response.status_code == 403:
                    self.log_result("RBAC - Inspector Facility Creation", True, "Inspector correctly denied facility creation")
                else:
                    self.log_result("RBAC - Inspector Facility Creation", False, f"Inspector should be denied, got status {response.status_code}")
                
                # Inspector should NOT be able to access audit logs
                response = self.session.get(f"{BASE_URL}/audit-logs", headers=headers)
                if response.status_code == 403:
                    self.log_result("RBAC - Inspector Audit Logs", True, "Inspector correctly denied audit log access")
                else:
                    self.log_result("RBAC - Inspector Audit Logs", False, f"Inspector should be denied, got status {response.status_code}")
            
            # Test deputy trying to create inspections (should be denied)
            if self.deputy_token and self.template_id and self.facility_id:
                headers = {"Authorization": f"Bearer {self.deputy_token}"}
                
                inspection_data = {
                    "template_id": self.template_id,
                    "facility_id": self.facility_id,
                    "inspection_date": datetime.now().isoformat(),
                    "form_data": {"test": "data"},
                    "status": "draft"
                }
                response = self.session.post(f"{BASE_URL}/inspections", json=inspection_data, headers=headers)
                if response.status_code == 403:
                    self.log_result("RBAC - Deputy Inspection Creation", True, "Deputy correctly denied inspection creation")
                else:
                    self.log_result("RBAC - Deputy Inspection Creation", False, f"Deputy should be denied, got status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Role-Based Access Control", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests in sequence"""
        print("🚀 Starting Fire and Environmental Safety Suite Backend Tests")
        print("=" * 70)
        
        # Basic connectivity
        if not self.test_basic_connectivity():
            print("❌ Basic connectivity failed. Stopping tests.")
            return False
        
        # Authentication tests
        if not self.test_admin_login():
            print("❌ Admin login failed. Stopping tests.")
            return False
        
        self.test_user_registration()
        self.test_deputy_user_creation()
        self.test_auth_me_endpoint()
        
        # Core functionality tests
        self.test_facility_management()
        self.test_inspection_templates()
        self.test_inspection_forms()
        self.test_inspection_review_process()
        self.test_citation_system()
        self.test_file_upload()
        self.test_dashboard_statistics()
        self.test_audit_logging()
        self.test_role_based_access_control()
        
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
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)