"""
Authentication Utilities
Decorators and helpers for authentication and authorization
"""
import logging
from functools import wraps
from flask import session, request
from utils.responses import error_response
from config import ROLE_ADMIN, ROLE_RENTER

logger = logging.getLogger(__name__)


def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning(f"Unauthorized access attempt to {request.path}")
            return error_response("Please log in to access this resource", 401)
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning(f"Unauthorized access attempt to {request.path}")
            return error_response("Please log in to access this resource", 401)
        if session.get('role') != ROLE_ADMIN:
            logger.warning(f"Non-admin access attempt to {request.path} by user {session.get('user_id')}")
            return error_response("Admin access required", 403)
        return f(*args, **kwargs)
    return decorated_function


def renter_required(f):
    """Decorator to require renter role for a route (excludes admin)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning(f"Unauthorized access attempt to {request.path}")
            return error_response("Please log in to access this resource", 401)
        if session.get('role') != ROLE_RENTER:
            logger.warning(f"Non-renter access attempt to {request.path} by user {session.get('user_id')} (role: {session.get('role')})")
            return error_response("Only renters can perform this action. Admins should use the admin panel.", 403)
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get the current logged-in user from session"""
    from models.database import get_users_collection
    
    if 'user_id' not in session:
        return None
    try:
        users = get_users_collection()
        user = users.find_one({'id': session['user_id']}, {'_id': 0, 'password_hash': 0})
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None


def get_current_user_id():
    """Get the current user's ID from session"""
    return session.get('user_id')


def get_current_user_role():
    """Get the current user's role from session"""
    return session.get('role')


def is_admin():
    """Check if current user is an admin"""
    return session.get('role') == ROLE_ADMIN


def is_renter():
    """Check if current user is a renter"""
    return session.get('role') == ROLE_RENTER


def set_user_session(user):
    """Set session data for a logged-in user"""
    session['user_id'] = user['id']
    session['email'] = user['email']
    session['role'] = user['role']
    session['name'] = user['name']


def clear_user_session():
    """Clear all session data"""
    session.clear()

