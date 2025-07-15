#!/usr/bin/env python3
"""
Focused Backend Testing for Fixed Endpoints
Tests the 4 specific endpoints that were previously failing
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://c94b3df9-82b5-41bd-a80d-f821e8a6f0cc.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@madoc.gov"
ADMIN_PASSWORD = "admin123"

class FixedEndpointTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
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
    
    def setup_authentication(self):
        """Setup admin authentication"""
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                print("✅ Admin authentication successful")
                return True
            else:
                print(f"❌ Admin login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def test_bulk_schedule_update_fix(self):
        """Test POST /api/compliance/scheduling/bulk-update - should handle schedules with missing start_dates properly"""
        print("\n" + "="*60)
        print("🔧 TESTING BULK SCHEDULE UPDATE FIX")
        print("="*60)
        
        try:
            # First get some schedules to update
            response = self.session.get(f"{BASE_URL}/compliance/facilities")
            if response.status_code != 200:
                self.log_result("Bulk Schedule Update Fix - Get Facilities", False, "Could not get facilities")
                return
            
            facilities = response.json()
            if not facilities:
                self.log_result("Bulk Schedule Update Fix - Get Facilities", False, "No facilities found")
                return
            
            facility_id = facilities[0]["id"]
            print(f"📍 Using facility: {facilities[0]['name']}")
            
            # Get schedules for the facility
            response = self.session.get(f"{BASE_URL}/compliance/facilities/{facility_id}/schedules")
            if response.status_code != 200:
                self.log_result("Bulk Schedule Update Fix - Get Schedules", False, "Could not get schedules")
                return
            
            schedules = response.json()
            if not schedules:
                self.log_result("Bulk Schedule Update Fix - Get Schedules", False, "No schedules found")
                return
            
            print(f"📋 Found {len(schedules)} schedules to test with")
            
            # Test bulk update with schedules that might have missing start_dates
            # The endpoint expects Form data, not JSON
            schedule_ids = [schedule["id"] for schedule in schedules[:3]]
            frequencies = ["M", "M", "M"]  # Monthly for all
            assigned_tos = ["test_user_0@madoc.gov", "test_user_1@madoc.gov", "test_user_2@madoc.gov"]
            
            form_data = {
                'schedule_ids': schedule_ids,
                'frequencies': frequencies,
                'assigned_tos': assigned_tos
            }
            
            print(f"🔄 Testing bulk update with {len(schedule_ids)} schedule updates")
            
            # Test the bulk update endpoint with form data
            response = self.session.post(f"{BASE_URL}/compliance/scheduling/bulk-update", data=form_data)
            
            if response.status_code == 200:
                result = response.json()
                updated_count = result.get("updated_count", 0)
                error_count = result.get("error_count", 0)
                errors = result.get("errors", [])
                
                print(f"📊 Results: {updated_count} updated, {error_count} errors")
                
                # Check if the fix worked - should handle None start_dates without 'NoneType + timedelta' error
                if error_count == 0 or not any("NoneType" in str(error) for error in errors):
                    self.log_result("Bulk Schedule Update Fix", True, 
                                  f"✅ FIXED: Bulk update handled missing start_dates properly. Updated: {updated_count}, Errors: {error_count}")
                else:
                    self.log_result("Bulk Schedule Update Fix", False, 
                                  f"❌ STILL FAILING: NoneType error still present. Errors: {errors}")
                    print(f"🔍 Error details: {errors}")
            else:
                self.log_result("Bulk Schedule Update Fix", False, 
                              f"❌ ENDPOINT ERROR: Status {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Bulk Schedule Update Fix", False, f"❌ EXCEPTION: {str(e)}")
    
    def test_document_statistics_fix(self):
        """Test GET /api/compliance/documents/statistics - should return proper statistics without 404 errors"""
        print("\n" + "="*60)
        print("📊 TESTING DOCUMENT STATISTICS FIX")
        print("="*60)
        
        try:
            # Test document statistics endpoint
            response = self.session.get(f"{BASE_URL}/compliance/documents/statistics")
            
            if response.status_code == 200:
                stats = response.json()
                expected_fields = ["total_documents", "total_size", "average_size", "type_breakdown", "category_breakdown"]
                
                print(f"📈 Statistics response: {stats}")
                
                if all(field in stats for field in expected_fields):
                    self.log_result("Document Statistics Fix", True, 
                                  f"✅ FIXED: Document statistics endpoint working correctly. Total docs: {stats.get('total_documents', 0)}")
                else:
                    self.log_result("Document Statistics Fix", False, 
                                  f"❌ STRUCTURE ISSUE: Missing expected fields. Got: {list(stats.keys())}")
            elif response.status_code == 404:
                self.log_result("Document Statistics Fix", False, 
                              f"❌ STILL FAILING: 404 error still present. Response: {response.text}")
            else:
                self.log_result("Document Statistics Fix", False, 
                              f"❌ ENDPOINT ERROR: Status {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Document Statistics Fix", False, f"❌ EXCEPTION: {str(e)}")
    
    def test_task_assignment_fix(self):
        """Test POST /api/compliance/tasks/assign - should work without foreign key constraint errors"""
        print("\n" + "="*60)
        print("👤 TESTING TASK ASSIGNMENT FIX")
        print("="*60)
        
        try:
            # First get a record to assign
            response = self.session.get(f"{BASE_URL}/compliance/records/upcoming?days_ahead=90")
            if response.status_code != 200:
                self.log_result("Task Assignment Fix - Get Records", False, "Could not get records")
                return
            
            records = response.json()
            if not records:
                print("🔄 No records found, generating some...")
                # Try to generate some records first
                gen_response = self.session.post(f"{BASE_URL}/compliance/scheduling/generate-records")
                if gen_response.status_code == 200:
                    print("✅ Records generated successfully")
                    # Try again to get records
                    response = self.session.get(f"{BASE_URL}/compliance/records/upcoming?days_ahead=90")
                    if response.status_code == 200:
                        records = response.json()
                
                if not records:
                    self.log_result("Task Assignment Fix - Get Records", False, "No records available for assignment")
                    return
            
            record_id = records[0]["id"] if records else None
            if not record_id:
                self.log_result("Task Assignment Fix - Get Records", False, "No valid record ID found")
                return
            
            print(f"📝 Testing assignment with record: {record_id}")
            
            # Test task assignment with form data (not JSON)
            form_data = {
                'record_id': record_id,
                'assigned_to': 'test_inspector@madoc.gov',
                'assigned_by': 'admin@madoc.gov',
                'notes': 'Test assignment for compliance task'
            }
            
            response = self.session.post(f"{BASE_URL}/compliance/tasks/assign", data=form_data)
            
            print(f"📤 Assignment request sent, status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.log_result("Task Assignment Fix", True, 
                                  f"✅ FIXED: Task assignment working correctly. Assigned to: {result.get('assigned_to')}")
                else:
                    error_msg = result.get("error", "Unknown error")
                    if "foreign key" in error_msg.lower():
                        self.log_result("Task Assignment Fix", False, 
                                      f"❌ STILL FAILING: Foreign key constraint error: {error_msg}")
                    else:
                        self.log_result("Task Assignment Fix", False, 
                                      f"❌ OTHER ERROR: {error_msg}")
            elif response.status_code == 422:
                self.log_result("Task Assignment Fix", False, 
                              f"❌ STILL FAILING: 422 validation error. Response: {response.text}")
            else:
                self.log_result("Task Assignment Fix", False, 
                              f"❌ ENDPOINT ERROR: Status {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Task Assignment Fix", False, f"❌ EXCEPTION: {str(e)}")
    
    def test_comment_system_fix(self):
        """Test POST /api/compliance/comments - should work without validation errors"""
        print("\n" + "="*60)
        print("💬 TESTING COMMENT SYSTEM FIX")
        print("="*60)
        
        try:
            # First get a record to comment on
            response = self.session.get(f"{BASE_URL}/compliance/records/upcoming?days_ahead=90")
            if response.status_code != 200:
                self.log_result("Comment System Fix - Get Records", False, "Could not get records")
                return
            
            records = response.json()
            if not records:
                print("🔄 No records found, generating some...")
                # Try to generate some records first
                gen_response = self.session.post(f"{BASE_URL}/compliance/scheduling/generate-records")
                if gen_response.status_code == 200:
                    print("✅ Records generated successfully")
                    # Try again to get records
                    response = self.session.get(f"{BASE_URL}/compliance/records/upcoming?days_ahead=90")
                    if response.status_code == 200:
                        records = response.json()
                
                if not records:
                    self.log_result("Comment System Fix - Get Records", False, "No records available for comments")
                    return
            
            record_id = records[0]["id"] if records else None
            if not record_id:
                self.log_result("Comment System Fix - Get Records", False, "No valid record ID found")
                return
            
            print(f"💭 Testing comment with record: {record_id}")
            
            # Test adding a comment with form data (not JSON)
            form_data = {
                'record_id': record_id,
                'comment': 'This is a test comment for the compliance record',
                'user': 'admin@madoc.gov',
                'comment_type': 'general'
            }
            
            response = self.session.post(f"{BASE_URL}/compliance/comments", data=form_data)
            
            print(f"📤 Comment request sent, status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.log_result("Comment System Fix", True, 
                                  f"✅ FIXED: Comment system working correctly. Comment ID: {result.get('comment_id')}")
                else:
                    error_msg = result.get("error", "Unknown error")
                    self.log_result("Comment System Fix", False, 
                                  f"❌ BUSINESS LOGIC ERROR: {error_msg}")
            elif response.status_code == 422:
                self.log_result("Comment System Fix", False, 
                              f"❌ STILL FAILING: 422 validation error. Response: {response.text}")
            else:
                self.log_result("Comment System Fix", False, 
                              f"❌ ENDPOINT ERROR: Status {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Comment System Fix", False, f"❌ EXCEPTION: {str(e)}")
    
    def run_focused_tests(self):
        """Run the focused tests for the 4 fixed endpoints"""
        print("🚀 STARTING FOCUSED BACKEND FIX TESTING")
        print("="*80)
        print("Testing the 4 specific endpoints that were previously failing:")
        print("1. POST /api/compliance/scheduling/bulk-update")
        print("2. GET /api/compliance/documents/statistics")
        print("3. POST /api/compliance/tasks/assign")
        print("4. POST /api/compliance/comments")
        print("="*80)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ CRITICAL: Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run the 4 focused tests
        self.test_bulk_schedule_update_fix()
        self.test_document_statistics_fix()
        self.test_task_assignment_fix()
        self.test_comment_system_fix()
        
        # Print summary
        print("\n" + "="*80)
        print("📊 FOCUSED TEST SUMMARY")
        print("="*80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        
        if len(self.test_results) > 0:
            success_rate = (passed/len(self.test_results)*100)
            print(f"Success Rate: {success_rate:.1f}%")
            
            if success_rate == 100:
                print("\n🎉 ALL FIXES WORKING! 100% SUCCESS RATE ACHIEVED!")
            elif success_rate >= 75:
                print(f"\n✅ GOOD PROGRESS! {success_rate:.1f}% of fixes are working")
            else:
                print(f"\n⚠️  MORE WORK NEEDED: Only {success_rate:.1f}% of fixes are working")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return failed == 0

if __name__ == "__main__":
    tester = FixedEndpointTester()
    success = tester.run_focused_tests()
    sys.exit(0 if success else 1)