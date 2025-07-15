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
BASE_URL = "https://e2b3ed4c-c62a-4948-9d9a-77995a1cc3c6.preview.emergentagent.com/api"
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
        self.compliance_facility_id = None
        self.compliance_function_id = None
        self.compliance_schedule_id = None
        
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
            elif response.status_code == 400 and "already registered" in response.text:
                self.log_result("User Registration - Inspector", True, "Inspector user already exists (expected)")
            else:
                self.log_result("User Registration - Inspector", False, 
                              f"Registration failed with status {response.status_code}", 
                              {"response": response.text})
                return False
            
            # Test login with inspector (whether new or existing)
            login_response = self.session.post(f"{BASE_URL}/auth/login", json={
                "email": inspector_data["email"],
                "password": inspector_data["password"]
            })
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                self.inspector_token = login_data["access_token"]
                self.log_result("Inspector Login", True, "Inspector login successful")
            else:
                self.log_result("Inspector Login", False, "Inspector login failed")
            
            return True
                
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
            elif response.status_code == 400 and "already registered" in response.text:
                self.log_result("Deputy User Creation", True, "Deputy user already exists (expected)")
            else:
                self.log_result("Deputy User Creation", False, 
                              f"Creation failed with status {response.status_code}")
                return False
            
            # Test deputy login (whether new or existing)
            login_response = self.session.post(f"{BASE_URL}/auth/login", json={
                "email": deputy_data["email"],
                "password": deputy_data["password"]
            })
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                self.deputy_token = login_data["access_token"]
                self.log_result("Deputy Login", True, "Deputy login successful")
            else:
                self.log_result("Deputy Login", False, "Deputy login failed")
            
            return True
                
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
            
            # Get current inspector info to get the correct ID
            user_response = self.session.get(f"{BASE_URL}/auth/me", headers=inspector_headers)
            if user_response.status_code != 200:
                self.log_result("Inspection Forms", False, "Could not get inspector info")
                return False
            
            inspector_info = user_response.json()
            inspector_id = inspector_info["id"]
            
            # Test CREATE inspection (inspector)
            inspection_data = {
                "template_id": self.template_id,
                "facility_id": self.facility_id,
                "inspector_id": inspector_id,  # Use actual inspector ID
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
            review_form_data = {
                "action": "approve",
                "comments": "Inspection completed thoroughly. All safety systems are functioning properly."
            }
            
            response = self.session.post(f"{BASE_URL}/inspections/{self.inspection_id}/review?action=approve&comments=Inspection completed thoroughly. All safety systems are functioning properly.", 
                                       headers=deputy_headers)
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
                # Use query parameter
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
    
    def test_sqlite_database_migration(self):
        """Test SQLite database migration system"""
        try:
            # Test if SQLite database file exists
            import os
            db_path = "/app/backend/fire_safety_suite.db"
            if os.path.exists(db_path):
                self.log_result("SQLite Database File", True, "SQLite database file exists")
            else:
                self.log_result("SQLite Database File", False, "SQLite database file not found")
                return False
            
            # Test database connection by checking if we can access v2 endpoints
            response = self.session.get(f"{BASE_URL}/v2/users")
            if response.status_code in [200, 401]:  # 401 is expected without auth
                self.log_result("SQLite API Connectivity", True, "SQLite API endpoints accessible")
            else:
                self.log_result("SQLite API Connectivity", False, f"SQLite API not accessible, status: {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_result("SQLite Database Migration", False, f"Error: {str(e)}")
            return False
    
    def test_sqlite_user_management(self):
        """Test SQLite user management endpoints"""
        try:
            # Test GET users
            response = self.session.get(f"{BASE_URL}/v2/users")
            if response.status_code == 200:
                users = response.json()
                self.log_result("SQLite Get Users", True, f"Retrieved {len(users)} users from SQLite")
            else:
                self.log_result("SQLite Get Users", False, f"Failed with status {response.status_code}")
                return False
            
            # Test CREATE user
            user_data = {
                "username": "sqlite_test_user@madoc.gov",
                "role": "inspector"
            }
            response = self.session.post(f"{BASE_URL}/v2/users", json=user_data)
            if response.status_code == 200:
                user = response.json()
                self.log_result("SQLite Create User", True, f"Created user: {user['username']}")
                
                # Test GET specific user
                user_id = user["id"]
                response = self.session.get(f"{BASE_URL}/v2/users/{user_id}")
                if response.status_code == 200:
                    retrieved_user = response.json()
                    self.log_result("SQLite Get User by ID", True, f"Retrieved user: {retrieved_user['username']}")
                else:
                    self.log_result("SQLite Get User by ID", False, f"Failed with status {response.status_code}")
            else:
                self.log_result("SQLite Create User", False, f"Failed with status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("SQLite User Management", False, f"Error: {str(e)}")
            return False
    
    def test_sqlite_template_system(self):
        """Test SQLite template management endpoints"""
        try:
            # Test GET templates
            response = self.session.get(f"{BASE_URL}/v2/templates")
            if response.status_code == 200:
                templates = response.json()
                self.log_result("SQLite Get Templates", True, f"Retrieved {len(templates)} templates from SQLite")
                
                # Check if seed templates are loaded
                template_names = [t["name"] for t in templates]
                expected_templates = [
                    "Weekly Fire/Environmental Health & Safety Inspection",
                    "Comprehensive Monthly Fire Safety, Sanitation & Equipment Inspection"
                ]
                
                found_templates = [name for name in expected_templates if name in template_names]
                if len(found_templates) >= 1:
                    self.log_result("SQLite Seed Templates", True, f"Found {len(found_templates)} seed templates")
                else:
                    self.log_result("SQLite Seed Templates", False, "Seed templates not found")
                
                # Test GET specific template if available
                if templates:
                    template_id = templates[0]["id"]
                    response = self.session.get(f"{BASE_URL}/v2/templates/{template_id}")
                    if response.status_code == 200:
                        template = response.json()
                        self.log_result("SQLite Get Template by ID", True, f"Retrieved template: {template['name']}")
                        
                        # Verify JSON schema structure
                        if "schema" in template and isinstance(template["schema"], dict):
                            schema = template["schema"]
                            if "$schema" in schema and "properties" in schema:
                                self.log_result("SQLite Template Schema", True, "Template has valid JSON schema structure")
                            else:
                                self.log_result("SQLite Template Schema", False, "Template schema missing required fields")
                        else:
                            self.log_result("SQLite Template Schema", False, "Template schema not found or invalid")
                    else:
                        self.log_result("SQLite Get Template by ID", False, f"Failed with status {response.status_code}")
            else:
                self.log_result("SQLite Get Templates", False, f"Failed with status {response.status_code}")
                return False
            
            # Test CREATE template
            template_data = {
                "name": "SQLite Test Template",
                "schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "title": "Test Inspection",
                    "type": "object",
                    "properties": {
                        "test_field": {"type": "boolean", "title": "Test Field"},
                        "notes": {"type": "string", "title": "Notes"}
                    },
                    "required": ["test_field"]
                }
            }
            response = self.session.post(f"{BASE_URL}/v2/templates", json=template_data)
            if response.status_code == 200:
                template = response.json()
                self.log_result("SQLite Create Template", True, f"Created template: {template['name']}")
            else:
                self.log_result("SQLite Create Template", False, f"Failed with status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("SQLite Template System", False, f"Error: {str(e)}")
            return False
    
    def test_sqlite_inspection_workflow(self):
        """Test SQLite inspection workflow"""
        try:
            # First get available templates
            templates_response = self.session.get(f"{BASE_URL}/v2/templates")
            if templates_response.status_code != 200:
                self.log_result("SQLite Inspection Workflow", False, "Could not retrieve templates")
                return False
            
            templates = templates_response.json()
            if not templates:
                self.log_result("SQLite Inspection Workflow", False, "No templates available")
                return False
            
            template_id = templates[0]["id"]
            
            # Test CREATE inspection
            inspection_data = {
                "template_id": template_id,
                "facility": "MCI-Cedar Junction",
                "payload": {
                    "location": "Cell Block A",
                    "wallsCeilingClean": True,
                    "lavatoriesStocked": True,
                    "fireExtinguishersTagged": True,
                    "emergencyExitsClear": True,
                    "comments": "All systems operational"
                }
            }
            response = self.session.post(f"{BASE_URL}/v2/inspections", json=inspection_data)
            if response.status_code == 200:
                inspection = response.json()
                inspection_id = inspection["id"]
                self.log_result("SQLite Create Inspection", True, f"Created inspection: {inspection_id}")
                
                # Test GET inspections
                response = self.session.get(f"{BASE_URL}/v2/inspections")
                if response.status_code == 200:
                    inspections = response.json()
                    self.log_result("SQLite Get Inspections", True, f"Retrieved {len(inspections)} inspections")
                else:
                    self.log_result("SQLite Get Inspections", False, f"Failed with status {response.status_code}")
                
                # Test GET specific inspection
                response = self.session.get(f"{BASE_URL}/v2/inspections/{inspection_id}")
                if response.status_code == 200:
                    retrieved_inspection = response.json()
                    self.log_result("SQLite Get Inspection by ID", True, f"Retrieved inspection: {retrieved_inspection['id']}")
                else:
                    self.log_result("SQLite Get Inspection by ID", False, f"Failed with status {response.status_code}")
                
                # Test UPDATE inspection status
                response = self.session.put(f"{BASE_URL}/v2/inspections/{inspection_id}/status?status=submitted")
                if response.status_code == 200:
                    updated_inspection = response.json()
                    if updated_inspection["status"] == "submitted":
                        self.log_result("SQLite Update Inspection Status", True, "Status updated to submitted")
                    else:
                        self.log_result("SQLite Update Inspection Status", False, "Status not updated correctly")
                else:
                    self.log_result("SQLite Update Inspection Status", False, f"Failed with status {response.status_code}")
            else:
                self.log_result("SQLite Create Inspection", False, f"Failed with status {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_result("SQLite Inspection Workflow", False, f"Error: {str(e)}")
            return False
    
    def test_sqlite_corrective_actions(self):
        """Test SQLite corrective actions system"""
        try:
            # First get an inspection to work with
            inspections_response = self.session.get(f"{BASE_URL}/v2/inspections")
            if inspections_response.status_code != 200:
                self.log_result("SQLite Corrective Actions", False, "Could not retrieve inspections")
                return False
            
            inspections = inspections_response.json()
            if not inspections:
                self.log_result("SQLite Corrective Actions", False, "No inspections available")
                return False
            
            inspection_id = inspections[0]["id"]
            
            # Test CREATE corrective action
            from datetime import date, timedelta
            due_date = (date.today() + timedelta(days=30)).isoformat()
            
            action_data = {
                "inspection_id": inspection_id,
                "violation_ref": "ICC-FC-907",
                "action_plan": "Replace faulty fire alarm system in Cell Block A",
                "due_date": due_date
            }
            response = self.session.post(f"{BASE_URL}/v2/corrective-actions", json=action_data)
            if response.status_code == 200:
                action = response.json()
                action_id = action["id"]
                self.log_result("SQLite Create Corrective Action", True, f"Created corrective action: {action_id}")
                
                # Test GET corrective actions by inspection
                response = self.session.get(f"{BASE_URL}/v2/corrective-actions/inspection/{inspection_id}")
                if response.status_code == 200:
                    actions = response.json()
                    self.log_result("SQLite Get Corrective Actions", True, f"Retrieved {len(actions)} corrective actions")
                else:
                    self.log_result("SQLite Get Corrective Actions", False, f"Failed with status {response.status_code}")
                
                # Test COMPLETE corrective action
                response = self.session.put(f"{BASE_URL}/v2/corrective-actions/{action_id}/complete")
                if response.status_code == 200:
                    completed_action = response.json()
                    if completed_action["completed"]:
                        self.log_result("SQLite Complete Corrective Action", True, "Corrective action marked as completed")
                    else:
                        self.log_result("SQLite Complete Corrective Action", False, "Corrective action not marked as completed")
                else:
                    self.log_result("SQLite Complete Corrective Action", False, f"Failed with status {response.status_code}")
            else:
                self.log_result("SQLite Create Corrective Action", False, f"Failed with status {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_result("SQLite Corrective Actions", False, f"Error: {str(e)}")
            return False
    
    def test_sqlite_statistics(self):
        """Test SQLite statistics endpoints"""
        try:
            # Test dashboard statistics
            response = self.session.get(f"{BASE_URL}/v2/statistics/dashboard")
            if response.status_code == 200:
                stats = response.json()
                expected_keys = ["total_users", "total_templates", "total_inspections", "pending_reviews"]
                if all(key in stats for key in expected_keys):
                    self.log_result("SQLite Dashboard Statistics", True, f"Dashboard stats: {stats}")
                else:
                    self.log_result("SQLite Dashboard Statistics", False, "Missing expected statistics keys")
            else:
                self.log_result("SQLite Dashboard Statistics", False, f"Failed with status {response.status_code}")
                return False
            
            # Test deputy statistics
            response = self.session.get(f"{BASE_URL}/v2/statistics/deputy")
            if response.status_code == 200:
                deputy_stats = response.json()
                expected_keys = ["pending_reviews", "completed_inspections", "total_inspections"]
                if all(key in deputy_stats for key in expected_keys):
                    self.log_result("SQLite Deputy Statistics", True, f"Deputy stats: {deputy_stats}")
                else:
                    self.log_result("SQLite Deputy Statistics", False, "Missing expected deputy statistics keys")
            else:
                self.log_result("SQLite Deputy Statistics", False, f"Failed with status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("SQLite Statistics", False, f"Error: {str(e)}")
            return False
    
    def test_compliance_facilities(self):
        """Test compliance facilities endpoints"""
        try:
            # Test GET facilities
            response = self.session.get(f"{BASE_URL}/compliance/facilities")
            if response.status_code == 200:
                facilities = response.json()
                self.log_result("Compliance Get Facilities", True, f"Retrieved {len(facilities)} compliance facilities")
                
                # Store first facility ID for later use
                if facilities:
                    self.compliance_facility_id = facilities[0]["id"]
                    
                    # Test GET specific facility
                    facility_response = self.session.get(f"{BASE_URL}/compliance/facilities/{self.compliance_facility_id}")
                    if facility_response.status_code == 200:
                        facility = facility_response.json()
                        self.log_result("Compliance Get Facility by ID", True, f"Retrieved facility: {facility['name']}")
                    else:
                        self.log_result("Compliance Get Facility by ID", False, f"Failed with status {facility_response.status_code}")
                else:
                    self.log_result("Compliance Facilities", False, "No facilities found")
                    return False
            else:
                self.log_result("Compliance Get Facilities", False, f"Failed with status {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_result("Compliance Facilities", False, f"Error: {str(e)}")
            return False
    
    def test_compliance_functions(self):
        """Test compliance functions endpoints"""
        try:
            # Test GET compliance functions
            response = self.session.get(f"{BASE_URL}/compliance/functions")
            if response.status_code == 200:
                functions = response.json()
                self.log_result("Compliance Get Functions", True, f"Retrieved {len(functions)} compliance functions")
                
                # Store first function ID for later use
                if functions:
                    self.compliance_function_id = functions[0]["id"]
                    
                    # Test GET specific function
                    function_response = self.session.get(f"{BASE_URL}/compliance/functions/{self.compliance_function_id}")
                    if function_response.status_code == 200:
                        function = function_response.json()
                        self.log_result("Compliance Get Function by ID", True, f"Retrieved function: {function['name']}")
                        
                        # Verify function structure
                        expected_fields = ["id", "name", "category", "default_frequency", "citation_references"]
                        if all(field in function for field in expected_fields):
                            self.log_result("Compliance Function Structure", True, "Function has correct structure")
                        else:
                            self.log_result("Compliance Function Structure", False, "Function missing expected fields")
                    else:
                        self.log_result("Compliance Get Function by ID", False, f"Failed with status {function_response.status_code}")
                else:
                    self.log_result("Compliance Functions", False, "No functions found")
                    return False
            else:
                self.log_result("Compliance Get Functions", False, f"Failed with status {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_result("Compliance Functions", False, f"Error: {str(e)}")
            return False
    
    def test_compliance_schedules(self):
        """Test compliance schedules endpoints"""
        try:
            if not hasattr(self, 'compliance_facility_id'):
                self.log_result("Compliance Schedules", False, "No facility ID available")
                return False
            
            # Test GET facility schedules
            response = self.session.get(f"{BASE_URL}/compliance/facilities/{self.compliance_facility_id}/schedules")
            if response.status_code == 200:
                schedules = response.json()
                self.log_result("Compliance Get Facility Schedules", True, f"Retrieved {len(schedules)} schedules for facility")
                
                # Store first schedule ID for later use
                if schedules:
                    self.compliance_schedule_id = schedules[0]["id"]
                    
                    # Verify schedule structure
                    schedule = schedules[0]
                    expected_fields = ["id", "facility_id", "function_id", "frequency", "next_due_date"]
                    if all(field in schedule for field in expected_fields):
                        self.log_result("Compliance Schedule Structure", True, "Schedule has correct structure")
                    else:
                        self.log_result("Compliance Schedule Structure", False, "Schedule missing expected fields")
                else:
                    self.log_result("Compliance Schedules", False, "No schedules found")
                    return False
            else:
                self.log_result("Compliance Get Facility Schedules", False, f"Failed with status {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_result("Compliance Schedules", False, f"Error: {str(e)}")
            return False
    
    def test_compliance_records(self):
        """Test compliance records endpoints"""
        try:
            # Test GET overdue records
            response = self.session.get(f"{BASE_URL}/compliance/records/overdue")
            if response.status_code == 200:
                overdue_records = response.json()
                self.log_result("Compliance Get Overdue Records", True, f"Retrieved {len(overdue_records)} overdue records")
            else:
                self.log_result("Compliance Get Overdue Records", False, f"Failed with status {response.status_code}")
            
            # Test GET upcoming records
            response = self.session.get(f"{BASE_URL}/compliance/records/upcoming?days_ahead=30")
            if response.status_code == 200:
                upcoming_records = response.json()
                self.log_result("Compliance Get Upcoming Records", True, f"Retrieved {len(upcoming_records)} upcoming records")
            else:
                self.log_result("Compliance Get Upcoming Records", False, f"Failed with status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Compliance Records", False, f"Error: {str(e)}")
            return False
    
    def test_compliance_dashboard(self):
        """Test compliance dashboard endpoints"""
        try:
            if not hasattr(self, 'compliance_facility_id'):
                self.log_result("Compliance Dashboard", False, "No facility ID available")
                return False
            
            # Test GET facility dashboard
            current_year = datetime.now().year
            response = self.session.get(f"{BASE_URL}/compliance/facilities/{self.compliance_facility_id}/dashboard?year={current_year}")
            if response.status_code == 200:
                dashboard = response.json()
                self.log_result("Compliance Facility Dashboard", True, f"Retrieved dashboard for facility with {len(dashboard.get('schedules', []))} schedules")
                
                # Verify dashboard structure
                expected_fields = ["facility_id", "facility_name", "year", "schedules"]
                if all(field in dashboard for field in expected_fields):
                    self.log_result("Compliance Dashboard Structure", True, "Dashboard has correct structure")
                    
                    # Check schedule structure if available
                    if dashboard.get("schedules"):
                        schedule = dashboard["schedules"][0]
                        schedule_fields = ["schedule_id", "function_name", "frequency", "monthly_status"]
                        if all(field in schedule for field in schedule_fields):
                            self.log_result("Compliance Dashboard Schedule Structure", True, "Schedule structure correct")
                        else:
                            self.log_result("Compliance Dashboard Schedule Structure", False, "Schedule structure incorrect")
                else:
                    self.log_result("Compliance Dashboard Structure", False, "Dashboard missing expected fields")
            else:
                self.log_result("Compliance Facility Dashboard", False, f"Failed with status {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_result("Compliance Dashboard", False, f"Error: {str(e)}")
            return False
    
    def test_compliance_statistics(self):
        """Test compliance statistics endpoints"""
        try:
            # Test GET compliance statistics
            response = self.session.get(f"{BASE_URL}/compliance/statistics")
            if response.status_code == 200:
                stats = response.json()
                self.log_result("Compliance Statistics", True, f"Retrieved compliance statistics")
                
                # Verify statistics structure
                expected_fields = ["total_records", "completed_records", "completion_rate", "overdue_records"]
                if all(field in stats for field in expected_fields):
                    self.log_result("Compliance Statistics Structure", True, f"Statistics: {stats}")
                else:
                    self.log_result("Compliance Statistics Structure", False, "Statistics missing expected fields")
            else:
                self.log_result("Compliance Statistics", False, f"Failed with status {response.status_code}")
                return False
            
            # Test facility-specific statistics if we have a facility ID
            if hasattr(self, 'compliance_facility_id'):
                response = self.session.get(f"{BASE_URL}/compliance/statistics?facility_id={self.compliance_facility_id}")
                if response.status_code == 200:
                    facility_stats = response.json()
                    self.log_result("Compliance Facility Statistics", True, f"Retrieved facility-specific statistics")
                else:
                    self.log_result("Compliance Facility Statistics", False, f"Failed with status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Compliance Statistics", False, f"Error: {str(e)}")
            return False

    # Phase 3: Scheduling System Tests
    def test_scheduling_record_generation(self):
        """Test automatic record generation for upcoming due dates"""
        try:
            # Test record generation with default 90 days ahead
            response = self.session.post(f"{BASE_URL}/compliance/scheduling/generate-records")
            if response.status_code == 200:
                result = response.json()
                self.log_result("Scheduling Record Generation (Default)", True, 
                              f"Generated {result.get('records_generated', 0)} records, updated {result.get('records_updated', 0)} records")
                
                # Verify response structure
                expected_fields = ["records_generated", "records_updated", "total_schedules_processed"]
                if all(field in result for field in expected_fields):
                    self.log_result("Record Generation Response Structure", True, "Response has correct structure")
                else:
                    self.log_result("Record Generation Response Structure", False, "Response missing expected fields")
            else:
                self.log_result("Scheduling Record Generation (Default)", False, f"Failed with status {response.status_code}")
                return False
            
            # Test record generation with custom days ahead
            response = self.session.post(f"{BASE_URL}/compliance/scheduling/generate-records?days_ahead=30")
            if response.status_code == 200:
                result = response.json()
                self.log_result("Scheduling Record Generation (30 days)", True, 
                              f"Generated {result.get('records_generated', 0)} records for 30 days ahead")
            else:
                self.log_result("Scheduling Record Generation (30 days)", False, f"Failed with status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Scheduling Record Generation", False, f"Error: {str(e)}")
            return False
    
    def test_scheduling_overdue_updates(self):
        """Test overdue status updates for past due records"""
        try:
            # Test overdue records update
            response = self.session.post(f"{BASE_URL}/compliance/scheduling/update-overdue")
            if response.status_code == 200:
                result = response.json()
                self.log_result("Scheduling Overdue Updates", True, 
                              f"Updated {result.get('overdue_records_updated', 0)} overdue records")
                
                # Verify response structure
                if "overdue_records_updated" in result:
                    self.log_result("Overdue Update Response Structure", True, "Response has correct structure")
                else:
                    self.log_result("Overdue Update Response Structure", False, "Response missing expected fields")
            else:
                self.log_result("Scheduling Overdue Updates", False, f"Failed with status {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_result("Scheduling Overdue Updates", False, f"Error: {str(e)}")
            return False
    
    def test_scheduling_analytics(self):
        """Test schedule analytics and insights"""
        try:
            # Test analytics without facility filter
            response = self.session.get(f"{BASE_URL}/compliance/scheduling/analytics")
            if response.status_code == 200:
                analytics = response.json()
                self.log_result("Scheduling Analytics (All Facilities)", True, 
                              f"Retrieved analytics for {analytics.get('total_schedules', 0)} schedules")
                
                # Verify analytics structure
                expected_fields = ["total_schedules", "frequency_breakdown", "upcoming_due_dates", "generated_at"]
                if all(field in analytics for field in expected_fields):
                    self.log_result("Analytics Response Structure", True, "Analytics have correct structure")
                    
                    # Test frequency breakdown
                    freq_breakdown = analytics.get("frequency_breakdown", {})
                    if isinstance(freq_breakdown, dict):
                        self.log_result("Frequency Breakdown", True, f"Found frequencies: {list(freq_breakdown.keys())}")
                    else:
                        self.log_result("Frequency Breakdown", False, "Frequency breakdown is not a dictionary")
                    
                    # Test upcoming due dates
                    upcoming = analytics.get("upcoming_due_dates", [])
                    if isinstance(upcoming, list):
                        self.log_result("Upcoming Due Dates", True, f"Found {len(upcoming)} upcoming due dates")
                    else:
                        self.log_result("Upcoming Due Dates", False, "Upcoming due dates is not a list")
                else:
                    self.log_result("Analytics Response Structure", False, "Analytics missing expected fields")
            else:
                self.log_result("Scheduling Analytics (All Facilities)", False, f"Failed with status {response.status_code}")
                return False
            
            # Test analytics with facility filter
            if hasattr(self, 'compliance_facility_id'):
                response = self.session.get(f"{BASE_URL}/compliance/scheduling/analytics?facility_id={self.compliance_facility_id}")
                if response.status_code == 200:
                    facility_analytics = response.json()
                    self.log_result("Scheduling Analytics (Facility Specific)", True, 
                                  f"Retrieved facility-specific analytics for {facility_analytics.get('total_schedules', 0)} schedules")
                else:
                    self.log_result("Scheduling Analytics (Facility Specific)", False, f"Failed with status {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Scheduling Analytics", False, f"Error: {str(e)}")
            return False
    
    def test_scheduling_bulk_updates(self):
        """Test bulk updating multiple schedules"""
        try:
            if not hasattr(self, 'compliance_schedule_id'):
                self.log_result("Scheduling Bulk Updates", False, "No schedule ID available")
                return False
            
            # Test bulk update with frequency change
            bulk_update_data = {
                "updates": [
                    {
                        "schedule_id": self.compliance_schedule_id,
                        "frequency": "M",  # Change to monthly
                        "assigned_to": "test_user@madoc.gov"
                    }
                ]
            }
            
            response = self.session.post(f"{BASE_URL}/compliance/scheduling/bulk-update", json=bulk_update_data)
            if response.status_code == 200:
                result = response.json()
                self.log_result("Scheduling Bulk Updates", True, 
                              f"Updated {result.get('updated_count', 0)} schedules, {result.get('error_count', 0)} errors")
                
                # Verify response structure
                expected_fields = ["updated_count", "error_count", "errors"]
                if all(field in result for field in expected_fields):
                    self.log_result("Bulk Update Response Structure", True, "Response has correct structure")
                else:
                    self.log_result("Bulk Update Response Structure", False, "Response missing expected fields")
                
                # Check for errors
                if result.get("error_count", 0) == 0:
                    self.log_result("Bulk Update Success", True, "No errors in bulk update")
                else:
                    self.log_result("Bulk Update Errors", False, f"Errors: {result.get('errors', [])}")
            else:
                self.log_result("Scheduling Bulk Updates", False, f"Failed with status {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_result("Scheduling Bulk Updates", False, f"Error: {str(e)}")
            return False
    
    def test_scheduling_next_due_date(self):
        """Test updating next due date for a schedule"""
        try:
            if not hasattr(self, 'compliance_schedule_id'):
                self.log_result("Scheduling Next Due Date", False, "No schedule ID available")
                return False
            
            # Test updating next due date
            response = self.session.put(f"{BASE_URL}/compliance/schedules/{self.compliance_schedule_id}/next-due-date")
            if response.status_code == 200:
                result = response.json()
                self.log_result("Scheduling Next Due Date Update", True, "Next due date updated successfully")
                
                # Verify response structure
                if "message" in result:
                    self.log_result("Next Due Date Response Structure", True, "Response has correct structure")
                else:
                    self.log_result("Next Due Date Response Structure", False, "Response missing expected fields")
            else:
                self.log_result("Scheduling Next Due Date Update", False, f"Failed with status {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_result("Scheduling Next Due Date", False, f"Error: {str(e)}")
            return False
    
    def test_scheduling_enhanced_record_completion(self):
        """Test enhanced record completion that auto-updates schedule's next due date"""
        try:
            # First, generate some records to have something to complete
            gen_response = self.session.post(f"{BASE_URL}/compliance/scheduling/generate-records?days_ahead=30")
            if gen_response.status_code != 200:
                self.log_result("Enhanced Record Completion Setup", False, "Failed to generate test records")
                return False
            
            # Get upcoming records to find one to complete
            records_response = self.session.get(f"{BASE_URL}/compliance/records/upcoming?days_ahead=30")
            if records_response.status_code == 200:
                records = records_response.json()
                if records:
                    record_id = records[0]["id"]
                    
                    # Test completing a record
                    completion_data = {
                        "completed_by": "test_user@madoc.gov",
                        "notes": "Test completion for scheduling system"
                    }
                    
                    response = self.session.post(f"{BASE_URL}/compliance/records/{record_id}/complete", 
                                               data=completion_data)
                    if response.status_code == 200:
                        result = response.json()
                        self.log_result("Enhanced Record Completion", True, 
                                      f"Record completed successfully, status: {result.get('status', 'unknown')}")
                        
                        # Verify the record was marked as completed
                        if result.get("status") == "completed":
                            self.log_result("Record Status Update", True, "Record status updated to completed")
                        else:
                            self.log_result("Record Status Update", False, f"Unexpected status: {result.get('status')}")
                    else:
                        self.log_result("Enhanced Record Completion", False, f"Failed with status {response.status_code}")
                        return False
                else:
                    self.log_result("Enhanced Record Completion", True, "No upcoming records to complete (expected for new system)")
            else:
                self.log_result("Enhanced Record Completion", False, "Failed to get upcoming records")
                return False
            
            return True
        except Exception as e:
            self.log_result("Enhanced Record Completion", False, f"Error: {str(e)}")
            return False
    
    def test_scheduling_integration(self):
        """Test integration between scheduling system and existing compliance tracking"""
        try:
            # Test that scheduling analytics integrate with dashboard data
            if hasattr(self, 'compliance_facility_id'):
                # Get dashboard data
                dashboard_response = self.session.get(f"{BASE_URL}/compliance/facilities/{self.compliance_facility_id}/dashboard")
                if dashboard_response.status_code == 200:
                    dashboard_data = dashboard_response.json()
                    
                    # Get scheduling analytics
                    analytics_response = self.session.get(f"{BASE_URL}/compliance/scheduling/analytics?facility_id={self.compliance_facility_id}")
                    if analytics_response.status_code == 200:
                        analytics_data = analytics_response.json()
                        
                        # Compare schedule counts
                        dashboard_schedules = len(dashboard_data.get("schedules", []))
                        analytics_schedules = analytics_data.get("total_schedules", 0)
                        
                        if dashboard_schedules == analytics_schedules:
                            self.log_result("Scheduling Integration - Schedule Count", True, 
                                          f"Dashboard and analytics show same schedule count: {dashboard_schedules}")
                        else:
                            self.log_result("Scheduling Integration - Schedule Count", False, 
                                          f"Mismatch: Dashboard={dashboard_schedules}, Analytics={analytics_schedules}")
                    else:
                        self.log_result("Scheduling Integration", False, "Failed to get analytics data")
                        return False
                else:
                    self.log_result("Scheduling Integration", False, "Failed to get dashboard data")
                    return False
            
            # Test that record generation affects upcoming records count
            initial_upcoming = self.session.get(f"{BASE_URL}/compliance/records/upcoming?days_ahead=90")
            if initial_upcoming.status_code == 200:
                initial_count = len(initial_upcoming.json())
                
                # Generate records
                gen_response = self.session.post(f"{BASE_URL}/compliance/scheduling/generate-records?days_ahead=90")
                if gen_response.status_code == 200:
                    # Check upcoming records again
                    final_upcoming = self.session.get(f"{BASE_URL}/compliance/records/upcoming?days_ahead=90")
                    if final_upcoming.status_code == 200:
                        final_count = len(final_upcoming.json())
                        
                        if final_count >= initial_count:
                            self.log_result("Scheduling Integration - Record Generation", True, 
                                          f"Record generation working: {initial_count} -> {final_count} upcoming records")
                        else:
                            self.log_result("Scheduling Integration - Record Generation", False, 
                                          f"Record count decreased: {initial_count} -> {final_count}")
                    else:
                        self.log_result("Scheduling Integration - Record Generation", False, "Failed to get final upcoming records")
                else:
                    self.log_result("Scheduling Integration - Record Generation", False, "Failed to generate records")
            else:
                self.log_result("Scheduling Integration", False, "Failed to get initial upcoming records")
                return False
            
            return True
        except Exception as e:
            self.log_result("Scheduling Integration", False, f"Error: {str(e)}")
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
        
        # Core functionality tests (MongoDB-based)
        self.test_facility_management()
        self.test_inspection_templates()
        self.test_inspection_forms()
        self.test_inspection_review_process()
        self.test_citation_system()
        self.test_file_upload()
        self.test_dashboard_statistics()
        self.test_audit_logging()
        self.test_role_based_access_control()
        
        # SQLite Database Integration Tests
        print("\n" + "=" * 70)
        print("🗄️  TESTING SQLITE DATABASE INTEGRATION")
        print("=" * 70)
        
        self.test_sqlite_database_migration()
        self.test_sqlite_user_management()
        self.test_sqlite_template_system()
        self.test_sqlite_inspection_workflow()
        self.test_sqlite_corrective_actions()
        self.test_sqlite_statistics()
        
        # Compliance Tracking System Tests
        print("\n" + "=" * 70)
        print("📋 TESTING COMPLIANCE TRACKING SYSTEM")
        print("=" * 70)
        
        self.test_compliance_facilities()
        self.test_compliance_functions()
        self.test_compliance_schedules()
        self.test_compliance_records()
        self.test_compliance_dashboard()
        self.test_compliance_statistics()
        
        # Phase 3: Scheduling System Tests
        print("\n" + "=" * 70)
        print("⏰ TESTING PHASE 3: SCHEDULING SYSTEM")
        print("=" * 70)
        
        self.test_scheduling_record_generation()
        self.test_scheduling_overdue_updates()
        self.test_scheduling_analytics()
        self.test_scheduling_bulk_updates()
        self.test_scheduling_next_due_date()
        self.test_scheduling_enhanced_record_completion()
        self.test_scheduling_integration()
        
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