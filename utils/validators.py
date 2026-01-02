"""
Input Validation Helpers
Reusable validation functions for API inputs
Includes security sanitization to prevent NoSQL injection and XSS attacks
"""
import math
import re
from config import MAX_SEARCH_RADIUS, MAX_SCOOTER_ID_LENGTH, MIN_PASSWORD_LENGTH

# ===========================================
# SECURITY: Patterns to detect malicious input
# ===========================================

# MongoDB operator injection patterns
MONGODB_OPERATORS = re.compile(r'\$[a-zA-Z]+')  # Matches $gt, $ne, $where, etc.

# Common injection patterns
INJECTION_PATTERNS = [
    r'\$where',           # JavaScript execution
    r'\$regex',           # Regex DoS
    r'\$expr',            # Aggregation expressions
    r'\$function',        # Server-side JavaScript
    r'{\s*["\']?\$',      # JSON with MongoDB operators
    r'\[\s*{',            # Array of objects (potential injection)
]

# HTML/Script injection patterns (XSS)
XSS_PATTERNS = [
    r'<script',
    r'javascript:',
    r'on\w+\s*=',         # onclick=, onerror=, etc.
    r'<iframe',
    r'<object',
    r'<embed',
]

# Compiled patterns for efficiency
INJECTION_REGEX = re.compile('|'.join(INJECTION_PATTERNS), re.IGNORECASE)
XSS_REGEX = re.compile('|'.join(XSS_PATTERNS), re.IGNORECASE)


def sanitize_string(value, field_name="input"):
    """
    Sanitize a string input to prevent injection attacks
    Returns: (is_safe: bool, sanitized_value: str or error_message: str)
    """
    if value is None:
        return True, None
    
    # Must be a string (not dict, list, etc.)
    if not isinstance(value, str):
        # If it's a dict or list, it could be an injection attempt
        if isinstance(value, (dict, list)):
            return False, f"{field_name} contains invalid data structure (possible injection attempt)"
        # Try to convert to string
        value = str(value)
    
    # Check for MongoDB operator injection
    if MONGODB_OPERATORS.search(value):
        return False, f"{field_name} contains invalid characters ($ operator not allowed)"
    
    # Check for common injection patterns
    if INJECTION_REGEX.search(value):
        return False, f"{field_name} contains potentially malicious content"
    
    # Check for XSS patterns
    if XSS_REGEX.search(value):
        return False, f"{field_name} contains invalid HTML/script content"
    
    return True, value


def sanitize_input(data, field_name="input"):
    """
    Sanitize any input (handles strings, dicts, lists)
    For dicts/lists from JSON body, ensures no MongoDB operators are present
    """
    if data is None:
        return True, None
    
    if isinstance(data, str):
        return sanitize_string(data, field_name)
    
    if isinstance(data, (int, float)):
        # Numbers are safe, but check for special values
        if isinstance(data, float) and (math.isnan(data) or math.isinf(data)):
            return False, f"{field_name} contains invalid number (NaN or Infinity)"
        return True, data
    
    if isinstance(data, dict):
        # Check all keys and values in dict
        for key, value in data.items():
            # Keys should not contain $ (MongoDB operators)
            if isinstance(key, str) and key.startswith('$'):
                return False, f"Invalid field name in {field_name} ($ prefix not allowed)"
            
            # Recursively check values
            is_safe, result = sanitize_input(value, f"{field_name}.{key}")
            if not is_safe:
                return False, result
        return True, data
    
    if isinstance(data, list):
        # Check all items in list
        for i, item in enumerate(data):
            is_safe, result = sanitize_input(item, f"{field_name}[{i}]")
            if not is_safe:
                return False, result
        return True, data
    
    # For other types, convert to string and check
    return sanitize_string(str(data), field_name)

# US Geographic Bounds (Continental US + some buffer for border areas)
US_BOUNDS = {
    'lat_min': 24.396308,   # Southern tip of Florida Keys
    'lat_max': 49.384358,   # Northern border with Canada
    'lng_min': -125.0,      # West coast (Washington)
    'lng_max': -66.93457    # East coast (Maine)
}

# Extended bounds including Alaska, Hawaii, Puerto Rico
EXTENDED_US_BOUNDS = {
    'lat_min': 17.5,        # Puerto Rico / US Virgin Islands
    'lat_max': 71.5,        # Northern Alaska
    'lng_min': -180.0,      # Alaska (crosses date line)
    'lng_max': -65.0        # Puerto Rico
}


def validate_coordinates(lat, lng, check_us_bounds=False, allow_null_island=False):
    """
    Validate latitude and longitude values with comprehensive checks
    
    Args:
        lat: Latitude value (string or number)
        lng: Longitude value (string or number)
        check_us_bounds: If True, validates coordinates are within US territory
        allow_null_island: If True, allows (0, 0) coordinates
    
    Returns: (is_valid: bool, result: tuple(lat, lng) or error_message: str)
    """
    # Check for None/empty values
    if lat is None or lng is None:
        return False, "Latitude and longitude are required"
    
    if lat == '' or lng == '':
        return False, "Latitude and longitude cannot be empty"
    
    # Try to convert to float
    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        return False, "Coordinates must be valid numbers (e.g., 30.2672, -97.7431)"
    
    # Check for NaN or Infinity
    if math.isnan(lat) or math.isnan(lng):
        return False, "Coordinates cannot be NaN (Not a Number)"
    
    if math.isinf(lat) or math.isinf(lng):
        return False, "Coordinates cannot be infinite"
    
    # Basic range validation
    if not (-90 <= lat <= 90):
        return False, f"Latitude must be between -90 and 90 degrees (got {lat})"
    
    if not (-180 <= lng <= 180):
        return False, f"Longitude must be between -180 and 180 degrees (got {lng})"
    
    # Check for Null Island (0, 0) - common data entry error
    if not allow_null_island and lat == 0 and lng == 0:
        return False, "Coordinates (0, 0) appear to be invalid - this is 'Null Island' in the Atlantic Ocean"
    
    # Optional: Check if within US bounds
    if check_us_bounds:
        is_valid, error = _check_us_bounds(lat, lng)
        if not is_valid:
            return False, error
    
    # Round to reasonable precision (6 decimal places = ~11cm accuracy)
    lat = round(lat, 6)
    lng = round(lng, 6)
    
    return True, (lat, lng)


def _check_us_bounds(lat, lng):
    """
    Check if coordinates are within US territory (including Alaska, Hawaii, Puerto Rico)
    Returns: (is_valid: bool, error_message: str or None)
    """
    # Check Continental US first
    if (US_BOUNDS['lat_min'] <= lat <= US_BOUNDS['lat_max'] and 
        US_BOUNDS['lng_min'] <= lng <= US_BOUNDS['lng_max']):
        return True, None
    
    # Check Hawaii (roughly)
    if 18.5 <= lat <= 22.5 and -160.5 <= lng <= -154.5:
        return True, None
    
    # Check Alaska (roughly - complex due to Aleutian Islands crossing date line)
    if 51.0 <= lat <= 71.5:
        # Main Alaska
        if -180.0 <= lng <= -129.0:
            return True, None
        # Aleutian Islands (wrap around)
        if 170.0 <= lng <= 180.0:
            return True, None
    
    # Check Puerto Rico / US Virgin Islands
    if 17.5 <= lat <= 18.6 and -68.0 <= lng <= -64.5:
        return True, None
    
    return False, f"Coordinates ({lat}, {lng}) appear to be outside US territory. Please verify the location."


def validate_coordinates_strict(lat, lng):
    """
    Strict coordinate validation for scooter placement (US bounds enforced)
    """
    return validate_coordinates(lat, lng, check_us_bounds=True, allow_null_island=False)


def get_coordinate_suggestions(lat, lng):
    """
    Provide helpful suggestions for coordinate issues
    Returns a list of suggestion strings
    """
    suggestions = []
    
    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        suggestions.append("Make sure coordinates are numbers, not text")
        suggestions.append("Example format: 30.2672 for latitude, -97.7431 for longitude")
        return suggestions
    
    # Check if lat/lng might be swapped (common error)
    if -180 <= lat <= 180 and -90 <= lng <= 90:
        if abs(lat) > 90 or abs(lng) > 180:
            suggestions.append("Latitude and longitude may be swapped. Latitude should be between -90 and 90.")
    
    # Check for missing negative sign on longitude (common for US)
    if 66 <= lng <= 125:
        suggestions.append(f"US longitudes are typically negative. Did you mean -{lng}?")
    
    # Check for common city coordinate mistakes
    if lat == 0 and lng == 0:
        suggestions.append("(0, 0) is 'Null Island' in the Atlantic. Enter actual coordinates.")
    
    return suggestions


def validate_radius(radius):
    """
    Validate search radius
    Returns: (is_valid: bool, result: float or error_message: str)
    """
    try:
        radius = float(radius)
    except (ValueError, TypeError):
        return False, "Radius must be a valid number"
    
    if radius <= 0:
        return False, "Radius must be greater than 0"
    
    if radius > MAX_SEARCH_RADIUS:
        return False, f"Radius must be less than {MAX_SEARCH_RADIUS} meters"
    
    return True, radius


def validate_scooter_id(scooter_id):
    """
    Validate and sanitize scooter ID
    Returns: (is_valid: bool, result: str or error_message: str)
    """
    if not scooter_id:
        return False, "Scooter ID cannot be empty"
    
    # Security: Must be a simple string, not a dict/list (injection prevention)
    if isinstance(scooter_id, (dict, list)):
        return False, "Invalid scooter ID format (possible injection attempt)"
    
    # Convert to string and strip whitespace
    scooter_id = str(scooter_id).strip()
    
    if not scooter_id:
        return False, "Scooter ID cannot be empty or whitespace only"
    
    if len(scooter_id) > MAX_SCOOTER_ID_LENGTH:
        return False, f"Scooter ID is too long (max {MAX_SCOOTER_ID_LENGTH} characters)"
    
    # Security: Check for injection patterns
    is_safe, result = sanitize_string(scooter_id, "Scooter ID")
    if not is_safe:
        return False, result
    
    # Only allow alphanumeric, dashes, and underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', scooter_id):
        return False, "Scooter ID can only contain letters, numbers, dashes, and underscores"
    
    return True, scooter_id


def validate_email(email):
    """
    Validate and sanitize email address
    Returns: (is_valid: bool, result: str or error_message: str)
    """
    if not email:
        return False, "Email cannot be empty"
    
    # Security: Must be a string
    if isinstance(email, (dict, list)):
        return False, "Invalid email format (possible injection attempt)"
    
    email = str(email).strip().lower()
    
    # Security: Check for injection patterns
    is_safe, result = sanitize_string(email, "Email")
    if not is_safe:
        return False, result
    
    # Basic format validation
    if '@' not in email or '.' not in email:
        return False, "Invalid email format"
    
    # More strict email validation
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(email):
        return False, "Invalid email format"
    
    # Check length
    if len(email) > 254:  # RFC 5321
        return False, "Email address is too long"
    
    return True, email


def validate_password(password):
    """
    Validate password strength
    Returns: (is_valid: bool, result: str or error_message: str)
    """
    if not password:
        return False, "Password cannot be empty"
    
    # Security: Must be a string
    if isinstance(password, (dict, list)):
        return False, "Invalid password format"
    
    password = str(password)
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    
    if len(password) > 128:
        return False, "Password is too long (max 128 characters)"
    
    return True, password


def validate_request_json(data, allowed_fields=None):
    """
    Validate and sanitize an entire JSON request body
    
    Args:
        data: The parsed JSON data (dict)
        allowed_fields: Optional list of allowed field names
    
    Returns: (is_valid: bool, sanitized_data: dict or error_message: str)
    """
    if data is None:
        return False, "Request body is required"
    
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object"
    
    # Check for MongoDB operators in keys
    for key in data.keys():
        if isinstance(key, str) and key.startswith('$'):
            return False, f"Invalid field name: {key} ($ prefix not allowed)"
    
    # If allowed_fields specified, check for unknown fields
    if allowed_fields:
        unknown_fields = set(data.keys()) - set(allowed_fields)
        if unknown_fields:
            return False, f"Unknown fields: {', '.join(unknown_fields)}"
    
    # Recursively sanitize all values
    is_safe, result = sanitize_input(data, "request body")
    if not is_safe:
        return False, result
    
    return True, data


def validate_required_fields(data, required_fields):
    """
    Check if all required fields are present in data
    Returns: (is_valid: bool, missing_fields: list)
    """
    if not data:
        return False, required_fields
    
    missing = [f for f in required_fields if f not in data or not data[f]]
    return len(missing) == 0, missing

