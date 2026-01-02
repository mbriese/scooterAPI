"""
Test Suite for Validators and Security
Run with: python -m pytest tests/ -v
Or run directly: python tests/test_validators.py
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validators import (
    validate_coordinates,
    validate_coordinates_strict,
    validate_radius,
    validate_scooter_id,
    validate_email,
    validate_password,
    validate_required_fields,
    validate_request_json,
    sanitize_string,
    sanitize_input,
    get_coordinate_suggestions
)


class Colors:
    """ANSI color codes for terminal output"""
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
    if details and not passed:
        print(f"         {Colors.YELLOW}{details}{Colors.RESET}")


def run_test(name, condition, details=""):
    """Run a single test and print result"""
    print_test(name, condition, details)
    return condition


# ===========================================
# COORDINATE VALIDATION TESTS
# ===========================================

def test_coordinates():
    print_header("COORDINATE VALIDATION TESTS")
    passed = 0
    total = 0
    
    # Test 1: Valid coordinates
    total += 1
    is_valid, result = validate_coordinates(30.2672, -97.7431)
    if run_test("Valid Austin, TX coordinates", is_valid and result == (30.2672, -97.7431)):
        passed += 1
    
    # Test 2: Valid coordinates as strings
    total += 1
    is_valid, result = validate_coordinates("30.2672", "-97.7431")
    if run_test("String coordinates converted to float", is_valid and isinstance(result[0], float)):
        passed += 1
    
    # Test 3: Latitude out of range
    total += 1
    is_valid, result = validate_coordinates(91, -97)
    if run_test("Reject latitude > 90", not is_valid and "Latitude" in result):
        passed += 1
    
    # Test 4: Latitude out of range (negative)
    total += 1
    is_valid, result = validate_coordinates(-91, -97)
    if run_test("Reject latitude < -90", not is_valid and "Latitude" in result):
        passed += 1
    
    # Test 5: Longitude out of range
    total += 1
    is_valid, result = validate_coordinates(30, 181)
    if run_test("Reject longitude > 180", not is_valid and "Longitude" in result):
        passed += 1
    
    # Test 6: Null Island (0, 0)
    total += 1
    is_valid, result = validate_coordinates(0, 0)
    if run_test("Reject Null Island (0, 0)", not is_valid and "Null Island" in result):
        passed += 1
    
    # Test 7: Allow Null Island when specified
    total += 1
    is_valid, result = validate_coordinates(0, 0, allow_null_island=True)
    if run_test("Allow Null Island when flag set", is_valid):
        passed += 1
    
    # Test 8: Empty values
    total += 1
    is_valid, result = validate_coordinates("", -97)
    if run_test("Reject empty latitude", not is_valid and "empty" in result.lower()):
        passed += 1
    
    # Test 9: None values
    total += 1
    is_valid, result = validate_coordinates(None, -97)
    if run_test("Reject None latitude", not is_valid and "required" in result.lower()):
        passed += 1
    
    # Test 10: Non-numeric values
    total += 1
    is_valid, result = validate_coordinates("abc", -97)
    if run_test("Reject non-numeric latitude", not is_valid and "valid numbers" in result.lower()):
        passed += 1
    
    # Test 11: NaN values
    total += 1
    is_valid, result = validate_coordinates(float('nan'), -97)
    if run_test("Reject NaN latitude", not is_valid and "NaN" in result):
        passed += 1
    
    # Test 12: Infinity values
    total += 1
    is_valid, result = validate_coordinates(float('inf'), -97)
    if run_test("Reject Infinity latitude", not is_valid and "infinite" in result.lower()):
        passed += 1
    
    # Test 13: US bounds check - valid US location
    total += 1
    is_valid, result = validate_coordinates(30.2672, -97.7431, check_us_bounds=True)
    if run_test("Accept Austin, TX (within US bounds)", is_valid):
        passed += 1
    
    # Test 14: US bounds check - outside US (London)
    total += 1
    is_valid, result = validate_coordinates(51.5074, -0.1278, check_us_bounds=True)
    if run_test("Reject London (outside US bounds)", not is_valid and "outside US" in result):
        passed += 1
    
    # Test 15: Hawaii coordinates
    total += 1
    is_valid, result = validate_coordinates(21.3069, -157.8583, check_us_bounds=True)
    if run_test("Accept Honolulu, HI (within US bounds)", is_valid):
        passed += 1
    
    # Test 16: Alaska coordinates
    total += 1
    is_valid, result = validate_coordinates(61.2181, -149.9003, check_us_bounds=True)
    if run_test("Accept Anchorage, AK (within US bounds)", is_valid):
        passed += 1
    
    # Test 17: Puerto Rico coordinates
    total += 1
    is_valid, result = validate_coordinates(18.4655, -66.1057, check_us_bounds=True)
    if run_test("Accept San Juan, PR (within US bounds)", is_valid):
        passed += 1
    
    # Test 18: Precision rounding
    total += 1
    is_valid, result = validate_coordinates(30.26720000001, -97.74310000001)
    if run_test("Coordinates rounded to 6 decimal places", is_valid and result == (30.2672, -97.7431)):
        passed += 1
    
    print(f"\n  {Colors.BOLD}Coordinate Tests: {passed}/{total} passed{Colors.RESET}")
    return passed, total


# ===========================================
# SECURITY SANITIZATION TESTS
# ===========================================

def test_security():
    print_header("SECURITY SANITIZATION TESTS")
    passed = 0
    total = 0
    
    # Test 1: MongoDB $where operator
    total += 1
    is_safe, result = sanitize_string("$where", "test")
    if run_test("Block MongoDB $where operator", not is_safe and "$" in result):
        passed += 1
    
    # Test 2: MongoDB $gt operator
    total += 1
    is_safe, result = sanitize_string("$gt", "test")
    if run_test("Block MongoDB $gt operator", not is_safe):
        passed += 1
    
    # Test 3: MongoDB $regex operator
    total += 1
    is_safe, result = sanitize_string("$regex", "test")
    if run_test("Block MongoDB $regex operator", not is_safe):
        passed += 1
    
    # Test 4: XSS script tag
    total += 1
    is_safe, result = sanitize_string("<script>alert('xss')</script>", "test")
    if run_test("Block XSS <script> tag", not is_safe and "script" in result.lower()):
        passed += 1
    
    # Test 5: XSS javascript: URL
    total += 1
    is_safe, result = sanitize_string("javascript:alert(1)", "test")
    if run_test("Block javascript: URL", not is_safe):
        passed += 1
    
    # Test 6: XSS onclick handler
    total += 1
    is_safe, result = sanitize_string("onclick=alert(1)", "test")
    if run_test("Block onclick= handler", not is_safe):
        passed += 1
    
    # Test 7: XSS iframe
    total += 1
    is_safe, result = sanitize_string("<iframe src='evil.com'>", "test")
    if run_test("Block <iframe> tag", not is_safe):
        passed += 1
    
    # Test 8: Valid normal text
    total += 1
    is_safe, result = sanitize_string("Normal text 123", "test")
    if run_test("Allow normal text", is_safe and result == "Normal text 123"):
        passed += 1
    
    # Test 9: Valid text with special chars
    total += 1
    is_safe, result = sanitize_string("Hello, World! 123 @#%", "test")
    if run_test("Allow safe special characters", is_safe):
        passed += 1
    
    # Test 10: Dict input (potential injection)
    total += 1
    is_safe, result = sanitize_string({"$gt": ""}, "test")
    if run_test("Block dict input (injection attempt)", not is_safe and "invalid data structure" in result.lower()):
        passed += 1
    
    # Test 11: List input
    total += 1
    is_safe, result = sanitize_string(["item1", "item2"], "test")
    if run_test("Block list input (injection attempt)", not is_safe):
        passed += 1
    
    # Test 12: Nested sanitize_input with dict
    total += 1
    is_safe, result = sanitize_input({"name": "John", "age": 25}, "data")
    if run_test("Allow valid dict in sanitize_input", is_safe):
        passed += 1
    
    # Test 13: Nested dict with $ key
    total += 1
    is_safe, result = sanitize_input({"$gt": "", "name": "test"}, "data")
    if run_test("Block dict with $ prefixed key", not is_safe and "$" in result):
        passed += 1
    
    # Test 14: None value is safe
    total += 1
    is_safe, result = sanitize_string(None, "test")
    if run_test("Allow None value", is_safe and result is None):
        passed += 1
    
    print(f"\n  {Colors.BOLD}Security Tests: {passed}/{total} passed{Colors.RESET}")
    return passed, total


# ===========================================
# SCOOTER ID VALIDATION TESTS
# ===========================================

def test_scooter_id():
    print_header("SCOOTER ID VALIDATION TESTS")
    passed = 0
    total = 0
    
    # Test 1: Valid scooter ID
    total += 1
    is_valid, result = validate_scooter_id("SCO001")
    if run_test("Valid alphanumeric ID", is_valid and result == "SCO001"):
        passed += 1
    
    # Test 2: Valid ID with dash
    total += 1
    is_valid, result = validate_scooter_id("SCO-001")
    if run_test("Valid ID with dash", is_valid and result == "SCO-001"):
        passed += 1
    
    # Test 3: Valid ID with underscore
    total += 1
    is_valid, result = validate_scooter_id("SCO_001")
    if run_test("Valid ID with underscore", is_valid and result == "SCO_001"):
        passed += 1
    
    # Test 4: Empty ID
    total += 1
    is_valid, result = validate_scooter_id("")
    if run_test("Reject empty ID", not is_valid and "empty" in result.lower()):
        passed += 1
    
    # Test 5: None ID
    total += 1
    is_valid, result = validate_scooter_id(None)
    if run_test("Reject None ID", not is_valid):
        passed += 1
    
    # Test 6: ID with $ (injection attempt)
    total += 1
    is_valid, result = validate_scooter_id("$where")
    if run_test("Reject ID with $ operator", not is_valid):
        passed += 1
    
    # Test 7: ID with spaces
    total += 1
    is_valid, result = validate_scooter_id("SCO 001")
    if run_test("Reject ID with spaces", not is_valid and "only contain" in result.lower()):
        passed += 1
    
    # Test 8: ID with special characters
    total += 1
    is_valid, result = validate_scooter_id("SCO@001")
    if run_test("Reject ID with @ symbol", not is_valid):
        passed += 1
    
    # Test 9: Dict input (injection)
    total += 1
    is_valid, result = validate_scooter_id({"$gt": ""})
    if run_test("Reject dict input (injection)", not is_valid and "injection" in result.lower()):
        passed += 1
    
    # Test 10: Very long ID
    total += 1
    is_valid, result = validate_scooter_id("A" * 200)
    if run_test("Reject overly long ID", not is_valid and "too long" in result.lower()):
        passed += 1
    
    # Test 11: Whitespace trimming
    total += 1
    is_valid, result = validate_scooter_id("  SCO001  ")
    if run_test("Trim whitespace from ID", is_valid and result == "SCO001"):
        passed += 1
    
    print(f"\n  {Colors.BOLD}Scooter ID Tests: {passed}/{total} passed{Colors.RESET}")
    return passed, total


# ===========================================
# EMAIL VALIDATION TESTS
# ===========================================

def test_email():
    print_header("EMAIL VALIDATION TESTS")
    passed = 0
    total = 0
    
    # Test 1: Valid email
    total += 1
    is_valid, result = validate_email("user@example.com")
    if run_test("Valid email format", is_valid and result == "user@example.com"):
        passed += 1
    
    # Test 2: Email with subdomain
    total += 1
    is_valid, result = validate_email("user@mail.example.com")
    if run_test("Valid email with subdomain", is_valid):
        passed += 1
    
    # Test 3: Email with plus
    total += 1
    is_valid, result = validate_email("user+tag@example.com")
    if run_test("Valid email with + tag", is_valid):
        passed += 1
    
    # Test 4: Email lowercase conversion
    total += 1
    is_valid, result = validate_email("USER@EXAMPLE.COM")
    if run_test("Email converted to lowercase", is_valid and result == "user@example.com"):
        passed += 1
    
    # Test 5: Empty email
    total += 1
    is_valid, result = validate_email("")
    if run_test("Reject empty email", not is_valid):
        passed += 1
    
    # Test 6: Email without @
    total += 1
    is_valid, result = validate_email("userexample.com")
    if run_test("Reject email without @", not is_valid):
        passed += 1
    
    # Test 7: Email without domain
    total += 1
    is_valid, result = validate_email("user@")
    if run_test("Reject email without domain", not is_valid):
        passed += 1
    
    # Test 8: Email with XSS
    total += 1
    is_valid, result = validate_email("<script>@example.com")
    if run_test("Reject email with XSS", not is_valid):
        passed += 1
    
    # Test 9: Dict input (injection)
    total += 1
    is_valid, result = validate_email({"$gt": ""})
    if run_test("Reject dict input (injection)", not is_valid and "injection" in result.lower()):
        passed += 1
    
    print(f"\n  {Colors.BOLD}Email Tests: {passed}/{total} passed{Colors.RESET}")
    return passed, total


# ===========================================
# PASSWORD VALIDATION TESTS
# ===========================================

def test_password():
    print_header("PASSWORD VALIDATION TESTS")
    passed = 0
    total = 0
    
    # Test 1: Valid password
    total += 1
    is_valid, result = validate_password("securePass123")
    if run_test("Valid password", is_valid):
        passed += 1
    
    # Test 2: Too short
    total += 1
    is_valid, result = validate_password("12345")
    if run_test("Reject short password (< 6 chars)", not is_valid and "at least" in result):
        passed += 1
    
    # Test 3: Empty password
    total += 1
    is_valid, result = validate_password("")
    if run_test("Reject empty password", not is_valid):
        passed += 1
    
    # Test 4: Very long password
    total += 1
    is_valid, result = validate_password("A" * 150)
    if run_test("Reject overly long password (> 128 chars)", not is_valid and "too long" in result.lower()):
        passed += 1
    
    # Test 5: Dict input
    total += 1
    is_valid, result = validate_password({"$gt": ""})
    if run_test("Reject dict input", not is_valid):
        passed += 1
    
    print(f"\n  {Colors.BOLD}Password Tests: {passed}/{total} passed{Colors.RESET}")
    return passed, total


# ===========================================
# REQUEST JSON VALIDATION TESTS
# ===========================================

def test_request_json():
    print_header("REQUEST JSON VALIDATION TESTS")
    passed = 0
    total = 0
    
    # Test 1: Valid JSON
    total += 1
    is_valid, result = validate_request_json({"name": "John", "age": 25})
    if run_test("Valid JSON object", is_valid):
        passed += 1
    
    # Test 2: JSON with allowed fields
    total += 1
    is_valid, result = validate_request_json(
        {"lat": 30.0, "lng": -97.0},
        allowed_fields=['lat', 'lng']
    )
    if run_test("JSON with allowed fields only", is_valid):
        passed += 1
    
    # Test 3: JSON with unknown fields
    total += 1
    is_valid, result = validate_request_json(
        {"lat": 30.0, "lng": -97.0, "extra": "field"},
        allowed_fields=['lat', 'lng']
    )
    if run_test("Reject JSON with unknown fields", not is_valid and "Unknown fields" in result):
        passed += 1
    
    # Test 4: JSON with $ key
    total += 1
    is_valid, result = validate_request_json({"$where": "1==1"})
    if run_test("Reject JSON with $ prefixed key", not is_valid and "$" in result):
        passed += 1
    
    # Test 5: Nested JSON with injection
    total += 1
    is_valid, result = validate_request_json({
        "user": {"name": "John", "query": "$gt"}
    })
    if run_test("Reject nested $ operator in value", not is_valid):
        passed += 1
    
    # Test 6: None body
    total += 1
    is_valid, result = validate_request_json(None)
    if run_test("Reject None body", not is_valid and "required" in result.lower()):
        passed += 1
    
    # Test 7: List instead of dict
    total += 1
    is_valid, result = validate_request_json(["item1", "item2"])
    if run_test("Reject list body (must be object)", not is_valid and "object" in result.lower()):
        passed += 1
    
    print(f"\n  {Colors.BOLD}Request JSON Tests: {passed}/{total} passed{Colors.RESET}")
    return passed, total


# ===========================================
# RADIUS VALIDATION TESTS
# ===========================================

def test_radius():
    print_header("RADIUS VALIDATION TESTS")
    passed = 0
    total = 0
    
    # Test 1: Valid radius
    total += 1
    is_valid, result = validate_radius(1000)
    if run_test("Valid radius (1000m)", is_valid and result == 1000):
        passed += 1
    
    # Test 2: String radius
    total += 1
    is_valid, result = validate_radius("2500")
    if run_test("String radius converted to float", is_valid and result == 2500):
        passed += 1
    
    # Test 3: Zero radius
    total += 1
    is_valid, result = validate_radius(0)
    if run_test("Reject zero radius", not is_valid and "greater than 0" in result):
        passed += 1
    
    # Test 4: Negative radius
    total += 1
    is_valid, result = validate_radius(-100)
    if run_test("Reject negative radius", not is_valid):
        passed += 1
    
    # Test 5: Radius too large
    total += 1
    is_valid, result = validate_radius(100000)
    if run_test("Reject radius > 50000m", not is_valid and "less than" in result):
        passed += 1
    
    # Test 6: Non-numeric radius
    total += 1
    is_valid, result = validate_radius("abc")
    if run_test("Reject non-numeric radius", not is_valid):
        passed += 1
    
    print(f"\n  {Colors.BOLD}Radius Tests: {passed}/{total} passed{Colors.RESET}")
    return passed, total


# ===========================================
# COORDINATE SUGGESTIONS TESTS
# ===========================================

def test_suggestions():
    print_header("COORDINATE SUGGESTION TESTS")
    passed = 0
    total = 0
    
    # Test 1: Swapped coordinates suggestion
    total += 1
    suggestions = get_coordinate_suggestions(-97.7431, 30.2672)
    has_swap_suggestion = any("swap" in s.lower() for s in suggestions)
    if run_test("Suggest swapped lat/lng", has_swap_suggestion):
        passed += 1
    
    # Test 2: Missing negative sign
    total += 1
    suggestions = get_coordinate_suggestions(30.2672, 97.7431)
    has_negative_suggestion = any("-97" in s for s in suggestions)
    if run_test("Suggest missing negative for US longitude", has_negative_suggestion):
        passed += 1
    
    # Test 3: Null Island suggestion
    total += 1
    suggestions = get_coordinate_suggestions(0, 0)
    has_null_island = any("null island" in s.lower() for s in suggestions)
    if run_test("Suggest Null Island issue", has_null_island):
        passed += 1
    
    # Test 4: Invalid input suggestion
    total += 1
    suggestions = get_coordinate_suggestions("abc", "def")
    has_format_suggestion = any("numbers" in s.lower() for s in suggestions)
    if run_test("Suggest format for non-numeric input", has_format_suggestion):
        passed += 1
    
    print(f"\n  {Colors.BOLD}Suggestion Tests: {passed}/{total} passed{Colors.RESET}")
    return passed, total


# ===========================================
# RUN ALL TESTS
# ===========================================

def run_all_tests():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("+----------------------------------------------------------+")
    print("|           SCOOTER API VALIDATION TEST SUITE              |")
    print("+----------------------------------------------------------+")
    print(f"{Colors.RESET}")
    
    total_passed = 0
    total_tests = 0
    
    # Run all test suites
    p, t = test_coordinates()
    total_passed += p
    total_tests += t
    
    p, t = test_security()
    total_passed += p
    total_tests += t
    
    p, t = test_scooter_id()
    total_passed += p
    total_tests += t
    
    p, t = test_email()
    total_passed += p
    total_tests += t
    
    p, t = test_password()
    total_passed += p
    total_tests += t
    
    p, t = test_request_json()
    total_passed += p
    total_tests += t
    
    p, t = test_radius()
    total_passed += p
    total_tests += t
    
    p, t = test_suggestions()
    total_passed += p
    total_tests += t
    
    # Print summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(" FINAL RESULTS")
    print(f"{'='*60}{Colors.RESET}")
    
    percentage = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    color = Colors.GREEN if percentage == 100 else (Colors.YELLOW if percentage >= 80 else Colors.RED)
    
    print(f"\n  {color}{Colors.BOLD}Total: {total_passed}/{total_tests} tests passed ({percentage:.1f}%){Colors.RESET}")
    
    if percentage == 100:
        print(f"\n  {Colors.GREEN}All tests passed! Your validators are secure.{Colors.RESET}")
    elif percentage >= 80:
        print(f"\n  {Colors.YELLOW}Most tests passed, but some need attention.{Colors.RESET}")
    else:
        print(f"\n  {Colors.RED}Many tests failed. Please review the validators.{Colors.RESET}")
    
    print()
    return total_passed == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

