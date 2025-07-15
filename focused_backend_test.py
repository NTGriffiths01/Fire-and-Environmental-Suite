#!/usr/bin/env python3
"""
Focused Backend Testing for Specific Fixed Endpoints
Tests the 4 specific endpoints that were previously failing and have been fixed
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

class FocusedBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        self.facility_id = None
        self.record_id = None
        
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
                self.log_result("Admin Authentication", True, "Admin login successful")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Login failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Login error: {str(e)}")
            return False
    
    def setup_test_data(self):
        """Setup test data needed for the focused tests"""
        try:
            # Get a facility ID
            response = self.session.get(f"{BASE_URL}/compliance/facilities")
            if response.status_code == 200:
                facilities = response.json()
                if facilities:
                    self.facility_id = facilities[0]["id"]
                    self.log_result("Test Data Setup - Facility", True, f"Got facility ID: {self.facility_id}")
                else:
                    self.log_result("Test Data Setup - Facility", False, "No facilities found")
                    return False
            else:
                self.log_result("Test Data Setup - Facility", False, f"Failed to get facilities: {response.status_code}")
                return False
            
            # Get a record ID for comment testing
            response = self.session.get(f"{BASE_URL}/compliance/records/upcoming?days_ahead=90")
            if response.status_code == 200:
                records = response.json()
                if records:
                    self.record_id = records[0]["id"]
                    self.log_result("Test Data Setup - Record", True, f"Got record ID: {self.record_id}")
                else:
                    # Try to generate some records first
                    gen_response = self.session.post(f"{BASE_URL}/compliance/scheduling/generate-records")
                    if gen_response.status_code == 200:
                        # Try again to get records
                        response = self.session.get(f"{BASE_URL}/compliance/records/upcoming?days_ahead=90")
                        if response.status_code == 200:
                            records = response.json()
                            if records:
                                self.record_id = records[0]["id"]
                                self.log_result("Test Data Setup - Record", True, f"Generated and got record ID: {self.record_id}")
                            else:
                                self.log_result("Test Data Setup - Record", False, "No records found even after generation")
                                return False
                        else:
                            self.log_result("Test Data Setup - Record", False, "Failed to get records after generation")
                            return False
                    else:
                        self.log_result("Test Data Setup - Record", False, "Failed to generate records")
                        return False
            else:
                self.log_result("Test Data Setup - Record", False, f"Failed to get records: {response.status_code}")
                return False
            
            return True
        except Exception as e:
            self.log_result("Test Data Setup", False, f"Setup error: {str(e)}")
            return False
    
    def test_comment_system_endpoint(self):
        """Test POST /api/compliance/comments - should now work without 'cannot access local variable json' error"""
        try:
            if not self.record_id:
                self.log_result("Comment System Test", False, "No record ID available for testing")
                return False
            
            # Test adding a comment using Form data
            form_data = {
                'record_id': self.record_id,
                'comment': 'Test comment for compliance record - testing fixed json variable scope issue',
                'user': 'test_user@madoc.gov',
                'comment_type': 'general'
            }
            
            response = self.session.post(f"{BASE_URL}/compliance/comments", data=form_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.log_result("Comment System - Add Comment", True, 
                                  f"Comment added successfully: {result.get('message')}")
                    return True
                else:
                    self.log_result("Comment System - Add Comment", False, 
                                  f"Comment addition failed: {result.get('error')}")
                    return False
            else:
                error_text = response.text
                self.log_result("Comment System - Add Comment", False, 
                              f"Failed with status {response.status_code}: {error_text}")
                return False
                
        except Exception as e:
            self.log_result("Comment System Test", False, f"Error: {str(e)}")
            return False
    
    def test_document_statistics_endpoint(self):
        """Test GET /api/compliance/documents/statistics - should now return statistics instead of 404"""
        try:
            # Test document statistics endpoint
            response = self.session.get(f"{BASE_URL}/compliance/documents/statistics")
            
            if response.status_code == 200:
                stats = response.json()
                expected_fields = ["total_documents", "total_size", "average_size", "type_breakdown", "category_breakdown"]
                
                if all(field in stats for field in expected_fields):
                    self.log_result("Document Statistics", True, 
                                  f"Statistics retrieved successfully: {stats}")
                    return True
                else:
                    self.log_result("Document Statistics", False, 
                                  f"Statistics missing expected fields. Got: {list(stats.keys())}")
                    return False
            else:
                error_text = response.text
                self.log_result("Document Statistics", False, 
                              f"Failed with status {response.status_code}: {error_text}")
                return False
                
        except Exception as e:
            self.log_result("Document Statistics Test", False, f"Error: {str(e)}")
            return False
    
    def test_facility_schedules_endpoint(self):
        """Test GET /api/compliance/facilities/{facility_id}/schedules - should now work without 500 errors"""
        try:
            if not self.facility_id:
                self.log_result("Facility Schedules Test", False, "No facility ID available for testing")
                return False
            
            # Test getting facility schedules
            response = self.session.get(f"{BASE_URL}/compliance/facilities/{self.facility_id}/schedules")
            
            if response.status_code == 200:
                schedules = response.json()
                self.log_result("Facility Schedules", True, 
                              f"Retrieved {len(schedules)} schedules for facility {self.facility_id}")
                
                # Verify schedule structure if schedules exist
                if schedules:
                    schedule = schedules[0]
                    expected_fields = ["id", "facility_id", "function_id", "frequency", "next_due_date"]
                    if all(field in schedule for field in expected_fields):
                        self.log_result("Facility Schedules Structure", True, "Schedule structure is correct")
                    else:
                        self.log_result("Facility Schedules Structure", False, 
                                      f"Schedule missing expected fields. Got: {list(schedule.keys())}")
                
                return True
            else:
                error_text = response.text
                self.log_result("Facility Schedules", False, 
                              f"Failed with status {response.status_code}: {error_text}")
                return False
                
        except Exception as e:
            self.log_result("Facility Schedules Test", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_update_endpoint(self):
        """Test POST /api/compliance/scheduling/bulk-update - should now work without NoneType + timedelta errors"""
        try:
            if not self.facility_id:
                self.log_result("Bulk Update Test", False, "No facility ID available for testing")
                return False
            
            # First get some schedules to update
            schedules_response = self.session.get(f"{BASE_URL}/compliance/facilities/{self.facility_id}/schedules")
            if schedules_response.status_code != 200:
                self.log_result("Bulk Update Test - Prerequisites", False, 
                              "Cannot get schedules for bulk update test")
                return False
            
            schedules = schedules_response.json()
            if not schedules:
                self.log_result("Bulk Update Test - Prerequisites", False, 
                              "No schedules available for bulk update test")
                return False
            
            # Test bulk update with form data
            test_schedule_ids = [schedules[0]["id"]]
            if len(schedules) > 1:
                test_schedule_ids.append(schedules[1]["id"])
            
            form_data = {
                'schedule_ids': test_schedule_ids,
                'frequencies': ['M'],  # Monthly frequency
                'assigned_tos': ['test_user@madoc.gov']
            }
            
            response = self.session.post(f"{BASE_URL}/compliance/scheduling/bulk-update", data=form_data)
            
            if response.status_code == 200:
                result = response.json()
                expected_fields = ["updated_count", "error_count", "errors"]
                
                if all(field in result for field in expected_fields):
                    self.log_result("Bulk Schedule Update", True, 
                                  f"Bulk update completed: {result['updated_count']} updated, {result['error_count']} errors")
                    
                    # Check if there were any NoneType + timedelta errors
                    errors = result.get("errors", [])
                    timedelta_errors = [err for err in errors if "NoneType" in str(err) and "timedelta" in str(err)]
                    
                    if timedelta_errors:
                        self.log_result("Bulk Update - NoneType Fix", False, 
                                      f"Still has NoneType + timedelta errors: {timedelta_errors}")
                    else:
                        self.log_result("Bulk Update - NoneType Fix", True, 
                                      "No NoneType + timedelta errors found")
                    
                    return True
                else:
                    self.log_result("Bulk Schedule Update", False, 
                                  f"Response missing expected fields. Got: {list(result.keys())}")
                    return False
            else:
                error_text = response.text
                self.log_result("Bulk Schedule Update", False, 
                              f"Failed with status {response.status_code}: {error_text}")
                return False
                
        except Exception as e:
            self.log_result("Bulk Update Test", False, f"Error: {str(e)}")
            return False
    
    def run_focused_tests(self):
        """Run all focused tests for the 4 specific endpoints"""
        print("=" * 80)
        print("FOCUSED BACKEND TESTING - SPECIFIC ENDPOINT FIXES")
        print("=" * 80)
        print()
        
        # Setup
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return False
        
        if not self.setup_test_data():
            print("❌ Cannot proceed without test data setup")
            return False
        
        print("\n" + "=" * 50)
        print("TESTING THE 4 SPECIFIC FIXED ENDPOINTS")
        print("=" * 50)
        
        # Test the 4 specific endpoints
        test_results = []
        
        print("\n1. Testing Comment System (POST /api/compliance/comments)")
        test_results.append(self.test_comment_system_endpoint())
        
        print("\n2. Testing Document Statistics (GET /api/compliance/documents/statistics)")
        test_results.append(self.test_document_statistics_endpoint())
        
        print("\n3. Testing Facility Schedules (GET /api/compliance/facilities/{facility_id}/schedules)")
        test_results.append(self.test_facility_schedules_endpoint())
        
        print("\n4. Testing Bulk Schedule Update (POST /api/compliance/scheduling/bulk-update)")
        test_results.append(self.test_bulk_update_endpoint())
        
        # Summary
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("FOCUSED TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if success_rate == 100:
            print("🎉 ALL TARGETED FIXES ARE WORKING!")
        elif success_rate >= 75:
            print("✅ Most fixes are working, minor issues remain")
        elif success_rate >= 50:
            print("⚠️  Some fixes are working, significant issues remain")
        else:
            print("❌ Major issues still exist with the fixes")
        
        return success_rate == 100

def main():
    tester = FocusedBackendTester()
    success = tester.run_focused_tests()
    
    if success:
        print("\n✅ All focused tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some focused tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()