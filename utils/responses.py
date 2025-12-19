"""
Response Helpers
Standardized JSON response functions for API consistency
"""
import json
import logging

logger = logging.getLogger(__name__)

# Content type header for JSON responses
JSON_HEADERS = {'Content-Type': 'application/json'}


def success_response(data=None, message=None, status_code=200):
    """
    Create a successful JSON response
    """
    response = {}
    if message:
        response['msg'] = message
    if data is not None:
        if isinstance(data, dict):
            response.update(data)
        else:
            response['data'] = data
    
    return json.dumps(response), status_code, JSON_HEADERS


def error_response(message, status_code=400, error_type=None):
    """
    Create an error JSON response
    """
    response = {'msg': f'Error {status_code} - {message}'}
    if error_type:
        response['error_type'] = error_type
    
    return json.dumps(response), status_code, JSON_HEADERS


def list_response(items, count=None, status_code=200):
    """
    Create a response for a list of items
    """
    if count is None:
        count = len(items) if items else 0
    
    return json.dumps(items), status_code, JSON_HEADERS


def created_response(data=None, message="Created successfully"):
    """
    Create a 201 Created response
    """
    return success_response(data, message, 201)


def not_found_response(resource="Resource"):
    """
    Create a 404 Not Found response
    """
    return error_response(f"{resource} not found", 404)


def validation_error(message):
    """
    Create a 422 Unprocessable Entity response
    """
    return error_response(message, 422, 'validation_error')


def unauthorized_response(message="Authentication required"):
    """
    Create a 401 Unauthorized response
    """
    return error_response(message, 401, 'unauthorized')


def forbidden_response(message="Access denied"):
    """
    Create a 403 Forbidden response
    """
    return error_response(message, 403, 'forbidden')


def server_error_response(message="Internal server error"):
    """
    Create a 500 Internal Server Error response
    """
    return error_response(message, 500, 'server_error')

