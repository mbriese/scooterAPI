"""
Utils Package
Contains utility functions for validation, authentication, and responses
"""
from utils.validators import (
    validate_coordinates,
    validate_radius,
    validate_scooter_id,
    validate_email,
    validate_password,
    validate_required_fields
)
from utils.auth import (
    login_required,
    admin_required,
    get_current_user,
    get_current_user_id,
    is_admin
)
from utils.responses import (
    success_response,
    error_response,
    list_response,
    created_response,
    not_found_response,
    validation_error
)

__all__ = [
    # Validators
    'validate_coordinates', 'validate_radius', 'validate_scooter_id',
    'validate_email', 'validate_password', 'validate_required_fields',
    # Auth
    'login_required', 'admin_required', 'get_current_user', 'get_current_user_id', 'is_admin',
    # Responses
    'success_response', 'error_response', 'list_response', 'created_response',
    'not_found_response', 'validation_error'
]

