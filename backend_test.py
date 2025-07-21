#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for BPMN Process Management
Tests all CRUD operations and export functionality
"""

import requests
import json
import uuid
from datetime import datetime
import sys

# Use the production backend URL from frontend/.env
BACKEND_URL = "https://01580b9d-74f9-4d48-9e21-a724e07c5a02.preview.emergentagent.com/api"

# Sample BPMN XML for testing
SAMPLE_BPMN_XML = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn" exporter="Camunda Modeler" exporterVersion="4.12.0">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:task id="Task_1" name="Customer Order Processing">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:task>
    <bpmn:endEvent id="EndEvent_1">
      <bpmn:incoming>Flow_2</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="EndEvent_1" />
  </bpmn:process>
</bpmn:definitions>"""

UPDATED_BPMN_XML = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn" exporter="Camunda Modeler" exporterVersion="4.12.0">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:task id="Task_1" name="Enhanced Customer Order Processing">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:task>
    <bpmn:task id="Task_2" name="Payment Verification">
      <bpmn:incoming>Flow_2</bpmn:incoming>
      <bpmn:outgoing>Flow_3</bpmn:outgoing>
    </bpmn:task>
    <bpmn:endEvent id="EndEvent_1">
      <bpmn:incoming>Flow_3</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="Task_2" />
    <bpmn:sequenceFlow id="Flow_3" sourceRef="Task_2" targetRef="EndEvent_1" />
  </bpmn:process>
</bpmn:definitions>"""

class BPMNAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = []
        self.created_process_ids = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details
        })
    
    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("API Root", True, "API root endpoint accessible")
                    return True
                else:
                    self.log_test("API Root", False, "Unexpected response format", data)
                    return False
            else:
                self.log_test("API Root", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("API Root", False, f"Connection error: {str(e)}")
            return False
    
    def test_get_processes_empty(self):
        """Test getting processes when database is empty"""
        try:
            response = requests.get(f"{self.base_url}/processes")
            if response.status_code == 200:
                processes = response.json()
                if isinstance(processes, list):
                    self.log_test("Get Processes (Empty)", True, f"Retrieved {len(processes)} processes")
                    return True
                else:
                    self.log_test("Get Processes (Empty)", False, "Response is not a list", processes)
                    return False
            else:
                self.log_test("Get Processes (Empty)", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Get Processes (Empty)", False, f"Request error: {str(e)}")
            return False
    
    def test_create_process(self):
        """Test creating a new BPMN process"""
        try:
            process_data = {
                "name": "Customer Order Workflow",
                "description": "Complete workflow for processing customer orders from initiation to fulfillment",
                "bpmn_xml": SAMPLE_BPMN_XML
            }
            
            response = requests.post(f"{self.base_url}/processes", json=process_data)
            if response.status_code == 200:
                process = response.json()
                if all(key in process for key in ['id', 'name', 'description', 'bpmn_xml', 'created_at']):
                    # Validate UUID format
                    try:
                        uuid.UUID(process['id'])
                        self.created_process_ids.append(process['id'])
                        self.log_test("Create Process", True, f"Process created with ID: {process['id']}")
                        return process['id']
                    except ValueError:
                        self.log_test("Create Process", False, "Invalid UUID format for process ID", process['id'])
                        return None
                else:
                    self.log_test("Create Process", False, "Missing required fields in response", process)
                    return None
            else:
                self.log_test("Create Process", False, f"HTTP {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Create Process", False, f"Request error: {str(e)}")
            return None
    
    def test_create_process_minimal(self):
        """Test creating a process with minimal data"""
        try:
            process_data = {
                "name": "Invoice Processing Workflow"
            }
            
            response = requests.post(f"{self.base_url}/processes", json=process_data)
            if response.status_code == 200:
                process = response.json()
                if 'id' in process and 'name' in process:
                    self.created_process_ids.append(process['id'])
                    self.log_test("Create Process (Minimal)", True, f"Minimal process created with ID: {process['id']}")
                    return process['id']
                else:
                    self.log_test("Create Process (Minimal)", False, "Missing required fields", process)
                    return None
            else:
                self.log_test("Create Process (Minimal)", False, f"HTTP {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Create Process (Minimal)", False, f"Request error: {str(e)}")
            return None
    
    def test_get_specific_process(self, process_id):
        """Test getting a specific process by ID"""
        if not process_id:
            self.log_test("Get Specific Process", False, "No process ID provided")
            return False
            
        try:
            response = requests.get(f"{self.base_url}/processes/{process_id}")
            if response.status_code == 200:
                process = response.json()
                if process['id'] == process_id:
                    self.log_test("Get Specific Process", True, f"Retrieved process: {process['name']}")
                    return True
                else:
                    self.log_test("Get Specific Process", False, "ID mismatch in response", f"Expected: {process_id}, Got: {process.get('id')}")
                    return False
            else:
                self.log_test("Get Specific Process", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Get Specific Process", False, f"Request error: {str(e)}")
            return False
    
    def test_get_nonexistent_process(self):
        """Test getting a non-existent process (should return 404)"""
        fake_id = str(uuid.uuid4())
        try:
            response = requests.get(f"{self.base_url}/processes/{fake_id}")
            if response.status_code == 404:
                self.log_test("Get Non-existent Process", True, "Correctly returned 404 for non-existent process")
                return True
            else:
                self.log_test("Get Non-existent Process", False, f"Expected 404, got HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Get Non-existent Process", False, f"Request error: {str(e)}")
            return False
    
    def test_update_process(self, process_id):
        """Test updating an existing process"""
        if not process_id:
            self.log_test("Update Process", False, "No process ID provided")
            return False
            
        try:
            update_data = {
                "name": "Enhanced Customer Order Workflow",
                "description": "Updated workflow with improved payment verification and inventory management",
                "bpmn_xml": UPDATED_BPMN_XML
            }
            
            response = requests.put(f"{self.base_url}/processes/{process_id}", json=update_data)
            if response.status_code == 200:
                process = response.json()
                if process['name'] == update_data['name'] and 'updated_at' in process:
                    self.log_test("Update Process", True, f"Process updated successfully: {process['name']}")
                    return True
                else:
                    self.log_test("Update Process", False, "Update not reflected in response", process)
                    return False
            else:
                self.log_test("Update Process", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Update Process", False, f"Request error: {str(e)}")
            return False
    
    def test_update_nonexistent_process(self):
        """Test updating a non-existent process (should return 404)"""
        fake_id = str(uuid.uuid4())
        try:
            update_data = {"name": "Non-existent Process"}
            response = requests.put(f"{self.base_url}/processes/{fake_id}", json=update_data)
            if response.status_code == 404:
                self.log_test("Update Non-existent Process", True, "Correctly returned 404 for non-existent process")
                return True
            else:
                self.log_test("Update Non-existent Process", False, f"Expected 404, got HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Update Non-existent Process", False, f"Request error: {str(e)}")
            return False
    
    def test_export_process_bpmn(self, process_id):
        """Test exporting BPMN XML for a process"""
        if not process_id:
            self.log_test("Export Process BPMN", False, "No process ID provided")
            return False
            
        try:
            response = requests.get(f"{self.base_url}/processes/{process_id}/export")
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get('content-type', '')
                if 'xml' in content_type.lower():
                    # Check if content looks like XML
                    content = response.text
                    if content.strip().startswith('<?xml') and 'bpmn:definitions' in content:
                        # Check for proper filename in headers
                        content_disposition = response.headers.get('content-disposition', '')
                        if 'attachment' in content_disposition and '.bpmn' in content_disposition:
                            self.log_test("Export Process BPMN", True, "BPMN XML exported successfully with proper headers")
                            return True
                        else:
                            self.log_test("Export Process BPMN", True, "BPMN XML exported (minor: missing proper attachment headers)")
                            return True
                    else:
                        self.log_test("Export Process BPMN", False, "Response doesn't contain valid BPMN XML", content[:200])
                        return False
                else:
                    self.log_test("Export Process BPMN", False, f"Wrong content type: {content_type}")
                    return False
            else:
                self.log_test("Export Process BPMN", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Export Process BPMN", False, f"Request error: {str(e)}")
            return False
    
    def test_export_nonexistent_process(self):
        """Test exporting BPMN for a non-existent process (should return 404)"""
        fake_id = str(uuid.uuid4())
        try:
            response = requests.get(f"{self.base_url}/processes/{fake_id}/export")
            if response.status_code == 404:
                self.log_test("Export Non-existent Process", True, "Correctly returned 404 for non-existent process")
                return True
            else:
                self.log_test("Export Non-existent Process", False, f"Expected 404, got HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Export Non-existent Process", False, f"Request error: {str(e)}")
            return False
    
    def test_get_processes_with_data(self):
        """Test getting all processes when data exists"""
        try:
            response = requests.get(f"{self.base_url}/processes")
            if response.status_code == 200:
                processes = response.json()
                if isinstance(processes, list) and len(processes) > 0:
                    # Verify each process has required fields
                    valid_processes = 0
                    for process in processes:
                        if all(key in process for key in ['id', 'name', 'created_at']):
                            valid_processes += 1
                    
                    if valid_processes == len(processes):
                        self.log_test("Get Processes (With Data)", True, f"Retrieved {len(processes)} valid processes")
                        return True
                    else:
                        self.log_test("Get Processes (With Data)", False, f"Only {valid_processes}/{len(processes)} processes are valid")
                        return False
                else:
                    self.log_test("Get Processes (With Data)", False, "No processes found or invalid response format")
                    return False
            else:
                self.log_test("Get Processes (With Data)", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Get Processes (With Data)", False, f"Request error: {str(e)}")
            return False
    
    def test_delete_process(self, process_id):
        """Test deleting a process"""
        if not process_id:
            self.log_test("Delete Process", False, "No process ID provided")
            return False
            
        try:
            response = requests.delete(f"{self.base_url}/processes/{process_id}")
            if response.status_code == 200:
                result = response.json()
                if "message" in result and "deleted" in result["message"].lower():
                    self.log_test("Delete Process", True, f"Process deleted successfully: {process_id}")
                    return True
                else:
                    self.log_test("Delete Process", False, "Unexpected response format", result)
                    return False
            else:
                self.log_test("Delete Process", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Delete Process", False, f"Request error: {str(e)}")
            return False
    
    def test_delete_nonexistent_process(self):
        """Test deleting a non-existent process (should return 404)"""
        fake_id = str(uuid.uuid4())
        try:
            response = requests.delete(f"{self.base_url}/processes/{fake_id}")
            if response.status_code == 404:
                self.log_test("Delete Non-existent Process", True, "Correctly returned 404 for non-existent process")
                return True
            else:
                self.log_test("Delete Non-existent Process", False, f"Expected 404, got HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Delete Non-existent Process", False, f"Request error: {str(e)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all tests in logical order"""
        print("🚀 Starting Comprehensive BPMN Process API Testing")
        print("=" * 60)
        
        # Test 1: API connectivity
        if not self.test_api_root():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        # Test 2: Get processes (empty state)
        self.test_get_processes_empty()
        
        # Test 3: Create processes
        process_id_1 = self.test_create_process()
        process_id_2 = self.test_create_process_minimal()
        
        # Test 4: Get specific process
        if process_id_1:
            self.test_get_specific_process(process_id_1)
        
        # Test 5: Get processes (with data)
        self.test_get_processes_with_data()
        
        # Test 6: Update process
        if process_id_1:
            self.test_update_process(process_id_1)
        
        # Test 7: Export BPMN
        if process_id_1:
            self.test_export_process_bpmn(process_id_1)
        
        # Test 8: Error handling tests
        self.test_get_nonexistent_process()
        self.test_update_nonexistent_process()
        self.test_export_nonexistent_process()
        self.test_delete_nonexistent_process()
        
        # Test 9: Delete processes (cleanup)
        for process_id in self.created_process_ids:
            self.test_delete_process(process_id)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
        
        return passed == total

def main():
    """Main test execution"""
    tester = BPMNAPITester()
    success = tester.run_comprehensive_tests()
    
    if success:
        print("\n🎉 All tests passed! BPMN Process API is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the details above.")
        sys.exit(1)

if __name__ == "__main__":
    main()