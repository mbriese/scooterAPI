"""
Input Validation Helpers
Reusable validation functions for API inputs
"""
from config import MAX_SEARCH_RADIUS, MAX_SCOOTER_ID_LENGTH, MIN_PASSWORD_LENGTH


def validate_coordinates(lat, lng):
    """
    Validate latitude and longitude values
    Returns: (is_valid: bool, result: tuple(lat, lng) or error_message: str)
    """
    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        return False, "Coordinates must be valid numbers"
    
    if not (-90 <= lat <= 90):
        return False, f"Latitude must be in range [-90, 90], got {lat}"
    
    if not (-180 <= lng <= 180):
        return False, f"Longitude must be in range [-180, 180], got {lng}"
    
    return True, (lat, lng)


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
    
    # Convert to string and strip whitespace
    scooter_id = str(scooter_id).strip()
    
    if not scooter_id:
        return False, "Scooter ID cannot be empty or whitespace only"
    
    if len(scooter_id) > MAX_SCOOTER_ID_LENGTH:
        return False, f"Scooter ID is too long (max {MAX_SCOOTER_ID_LENGTH} characters)"
    
    return True, scooter_id


def validate_email(email):
    """
    Basic email validation
    Returns: (is_valid: bool, result: str or error_message: str)
    """
    if not email:
        return False, "Email cannot be empty"
    
    email = str(email).strip().lower()
    
    if '@' not in email or '.' not in email:
        return False, "Invalid email format"
    
    return True, email


def validate_password(password):
    """
    Validate password strength
    Returns: (is_valid: bool, result: str or error_message: str)
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    
    return True, password


def validate_required_fields(data, required_fields):
    """
    Check if all required fields are present in data
    Returns: (is_valid: bool, missing_fields: list)
    """
    if not data:
        return False, required_fields
    
    missing = [f for f in required_fields if f not in data or not data[f]]
    return len(missing) == 0, missing

