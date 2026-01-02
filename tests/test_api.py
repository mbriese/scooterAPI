"""
API Integration Tests
Tests the actual API endpoints with security scenarios
Requires the server to be running on localhost:5000

Run with: python tests/test_api.py
"""
import sys
import os
import requests
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:5000"


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(title):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}")
    print(f" {title}")
    print(f"{'='*60}{Colors.RESET}\n")


def print_test(name, passed, details=""):
    status = f"{Colors.GREEN}[PASS]{Colors.RESET}" if passed else f"{Colors.RED}[FAIL]{Colors.RESET}"
    print(f"  {status} {name}")
    if details:
        print(f"         {Colors.YELLOW}{details}{Colors.RESET}")


class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.passed = 0
        self.total = 0
    
    def check_server(self):
        """Check if server is running"""
        try:
            response = requests.get(f"{BASE_URL}/pricing", timeout=5)
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False
    
    def login_admin(self):
        """Login as admin"""
        response = self.session.post(f"{BASE_URL}/auth/login", json={
            "email": "admin@scooter.com",
            "password": "admin123"
        })
        return response.status_code == 200
    
    def login_renter(self, email="testuser@example.com", password="test123"):
        """Login as renter"""
        # First try to register
        self.session.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": password,
            "name": "Test User"
        })
        # Then login
        response = self.session.post(f"{BASE_URL}/auth/login", json={
            "email": email,
            "password": password
        })
        return response.status_code == 200
    
    def logout(self):
        """Logout"""
        self.session.post(f"{BASE_URL}/auth/logout")
    
    def run_test(self, name, condition, details=""):
        self.total += 1
        print_test(name, condition, details)
        if condition:
            self.passed += 1
        return condition

    # ===========================================
    # COORDINATE VALIDATION API TESTS
    # ===========================================
    
    def test_coordinate_validation(self):
        print_header("API COORDINATE VALIDATION TESTS")
        
        if not self.login_admin():
            print(f"  {Colors.RED}Failed to login as admin{Colors.RESET}")
            return
        
        # Test 1: Valid scooter creation
        response = self.session.post(f"{BASE_URL}/admin/scooters", json={
            "id": "TEST-VALID-001",
            "lat": 30.2672,
            "lng": -97.7431
        })
        self.run_test(
            "Create scooter with valid coordinates",
            response.status_code in [200, 201],
            f"Status: {response.status_code}"
        )
        
        # Test 2: Null Island rejection
        response = self.session.post(f"{BASE_URL}/admin/scooters", json={
            "id": "TEST-NULL-001",
            "lat": 0,
            "lng": 0
        })
        self.run_test(
            "Reject scooter at Null Island (0, 0)",
            response.status_code == 422 and "Null Island" in response.text,
            f"Status: {response.status_code}"
        )
        
        # Test 3: Invalid latitude
        response = self.session.post(f"{BASE_URL}/admin/scooters", json={
            "id": "TEST-LAT-001",
            "lat": 95,
            "lng": -97.7431
        })
        self.run_test(
            "Reject scooter with latitude > 90",
            response.status_code == 422 and "Latitude" in response.text,
            f"Status: {response.status_code}"
        )
        
        # Test 4: Outside US bounds
        response = self.session.post(f"{BASE_URL}/admin/scooters", json={
            "id": "TEST-LONDON-001",
            "lat": 51.5074,
            "lng": -0.1278
        })
        self.run_test(
            "Reject scooter outside US (London)",
            response.status_code == 422 and "outside US" in response.text,
            f"Status: {response.status_code}"
        )
        
        # Test 5: Non-numeric coordinates
        response = self.session.post(f"{BASE_URL}/admin/scooters", json={
            "id": "TEST-ABC-001",
            "lat": "abc",
            "lng": -97.7431
        })
        self.run_test(
            "Reject non-numeric latitude",
            response.status_code == 422,
            f"Status: {response.status_code}"
        )
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/admin/scooters/TEST-VALID-001")
        self.logout()

    # ===========================================
    # SECURITY INJECTION API TESTS
    # ===========================================
    
    def test_injection_prevention(self):
        print_header("API INJECTION PREVENTION TESTS")
        
        if not self.login_admin():
            print(f"  {Colors.RED}Failed to login as admin{Colors.RESET}")
            return
        
        # Test 1: MongoDB operator in scooter ID
        response = self.session.post(f"{BASE_URL}/admin/scooters", json={
            "id": "$where",
            "lat": 30.2672,
            "lng": -97.7431
        })
        self.run_test(
            "Block $where in scooter ID",
            response.status_code == 422,
            f"Status: {response.status_code}"
        )
        
        # Test 2: XSS in scooter ID
        response = self.session.post(f"{BASE_URL}/admin/scooters", json={
            "id": "<script>alert(1)</script>",
            "lat": 30.2672,
            "lng": -97.7431
        })
        self.run_test(
            "Block XSS in scooter ID",
            response.status_code == 422,
            f"Status: {response.status_code}"
        )
        
        # Test 3: Unknown fields in request
        response = self.session.post(f"{BASE_URL}/admin/scooters", json={
            "id": "TEST-EXTRA-001",
            "lat": 30.2672,
            "lng": -97.7431,
            "$where": "1==1",
            "malicious": "data"
        })
        self.run_test(
            "Block request with unknown/malicious fields",
            response.status_code == 422,
            f"Status: {response.status_code}"
        )
        
        self.logout()
        
        # Test 4: XSS in registration name
        response = self.session.post(f"{BASE_URL}/auth/register", json={
            "email": "xss@test.com",
            "password": "test123",
            "name": "<script>alert('xss')</script>"
        })
        self.run_test(
            "Block XSS in registration name",
            response.status_code == 422 and "script" in response.text.lower(),
            f"Status: {response.status_code}"
        )
        
        # Test 5: MongoDB operator in email
        response = self.session.post(f"{BASE_URL}/auth/register", json={
            "email": {"$gt": ""},
            "password": "test123",
            "name": "Test"
        })
        self.run_test(
            "Block dict injection in email field",
            response.status_code == 422,
            f"Status: {response.status_code}"
        )

    # ===========================================
    # SEARCH VALIDATION API TESTS
    # ===========================================
    
    def test_search_validation(self):
        print_header("API SEARCH VALIDATION TESTS")
        
        # Test 1: Valid search
        response = self.session.get(f"{BASE_URL}/search", params={
            "lat": 30.2672,
            "lng": -97.7431,
            "radius": 5000
        })
        self.run_test(
            "Valid search request",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        # Test 2: Invalid latitude
        response = self.session.get(f"{BASE_URL}/search", params={
            "lat": 95,
            "lng": -97.7431,
            "radius": 5000
        })
        self.run_test(
            "Reject search with invalid latitude",
            response.status_code == 422,
            f"Status: {response.status_code}"
        )
        
        # Test 3: Radius too large
        response = self.session.get(f"{BASE_URL}/search", params={
            "lat": 30.2672,
            "lng": -97.7431,
            "radius": 100000
        })
        self.run_test(
            "Reject search with radius > 50km",
            response.status_code == 422,
            f"Status: {response.status_code}"
        )
        
        # Test 4: Missing parameters
        response = self.session.get(f"{BASE_URL}/search", params={
            "lat": 30.2672
        })
        self.run_test(
            "Reject search with missing parameters",
            response.status_code == 422,
            f"Status: {response.status_code}"
        )

    # ===========================================
    # ROLE-BASED ACCESS TESTS
    # ===========================================
    
    def test_role_access(self):
        print_header("API ROLE-BASED ACCESS TESTS")
        
        # Test 1: Admin can access admin endpoints
        self.login_admin()
        response = self.session.get(f"{BASE_URL}/admin/scooters")
        self.run_test(
            "Admin can access /admin/scooters",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        self.logout()
        
        # Test 2: Renter cannot access admin endpoints
        self.login_renter("renter@test.com", "test123")
        response = self.session.get(f"{BASE_URL}/admin/scooters")
        self.run_test(
            "Renter cannot access /admin/scooters",
            response.status_code == 403,
            f"Status: {response.status_code}"
        )
        
        # Test 3: Renter can access reservations
        response = self.session.get(f"{BASE_URL}/rentals/active")
        self.run_test(
            "Renter can access /rentals/active",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        self.logout()
        
        # Test 4: Unauthenticated cannot reserve
        response = self.session.post(f"{BASE_URL}/reservation/start", params={"id": "SCO001"})
        self.run_test(
            "Unauthenticated cannot start reservation",
            response.status_code == 401,
            f"Status: {response.status_code}"
        )


def run_all_api_tests():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("+----------------------------------------------------------+")
    print("|           SCOOTER API INTEGRATION TEST SUITE             |")
    print("+----------------------------------------------------------+")
    print(f"{Colors.RESET}")
    
    tester = APITester()
    
    # Check if server is running
    if not tester.check_server():
        print(f"\n  {Colors.RED}{Colors.BOLD}ERROR: Server is not running!{Colors.RESET}")
        print(f"  {Colors.YELLOW}Please start the server first:{Colors.RESET}")
        print(f"  {Colors.BLUE}cd C:\\Users\\mindi\\tekInnov8rs\\scooterAPI")
        print(f"  .\\venv\\Scripts\\Activate.ps1")
        print(f"  python app.py{Colors.RESET}\n")
        return False
    
    print(f"  {Colors.GREEN}[OK] Server is running{Colors.RESET}")
    
    # Run all tests
    tester.test_coordinate_validation()
    tester.test_injection_prevention()
    tester.test_search_validation()
    tester.test_role_access()
    
    # Print summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(" FINAL RESULTS")
    print(f"{'='*60}{Colors.RESET}")
    
    percentage = (tester.passed / tester.total) * 100 if tester.total > 0 else 0
    color = Colors.GREEN if percentage == 100 else (Colors.YELLOW if percentage >= 80 else Colors.RED)
    
    print(f"\n  {color}{Colors.BOLD}Total: {tester.passed}/{tester.total} tests passed ({percentage:.1f}%){Colors.RESET}")
    
    if percentage == 100:
        print(f"\n  {Colors.GREEN}All API tests passed!{Colors.RESET}")
    else:
        print(f"\n  {Colors.YELLOW}Some tests need attention.{Colors.RESET}")
    
    print()
    return tester.passed == tester.total


if __name__ == "__main__":
    success = run_all_api_tests()
    sys.exit(0 if success else 1)

