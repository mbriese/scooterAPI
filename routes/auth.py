"""
Authentication Routes
Handles user registration, login, logout, and profile
"""
import logging
import uuid
from datetime import datetime
from flask import Blueprint, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import errors as mongo_errors

from models.database import get_users_collection
from utils.validators import validate_email, validate_password, validate_required_fields
from utils.responses import (
    success_response, error_response, created_response,
    validation_error, unauthorized_response, server_error_response
)
from utils.auth import login_required, get_current_user, set_user_session, clear_user_session
from config import ROLE_RENTER, ROLE_ADMIN, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_NAME

logger = logging.getLogger(__name__)

# Create Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user account"""
    logger.info("Request received: POST /auth/register")
    
    try:
        data = request.get_json()
        if not data:
            return validation_error("Request body must be JSON")
        
        # Validate required fields
        is_valid, missing = validate_required_fields(data, ['email', 'password', 'name'])
        if not is_valid:
            return validation_error(f"Missing required fields: {', '.join(missing)}")
        
        # Validate email
        is_valid, result = validate_email(data['email'])
        if not is_valid:
            return validation_error(result)
        email = result
        
        # Validate password
        is_valid, result = validate_password(data['password'])
        if not is_valid:
            return validation_error(result)
        password = data['password']
        
        name = data['name'].strip()
        if not name:
            return validation_error("Name cannot be empty")
        
        users = get_users_collection()
        
        # Check if email already exists
        if users.find_one({'email': email}):
            logger.warning(f"Registration failed: Email {email} already exists")
            return validation_error("Email already registered")
        
        # Create new user
        user_id = str(uuid.uuid4())
        new_user = {
            'id': user_id,
            'email': email,
            'password_hash': generate_password_hash(password),
            'name': name,
            'role': ROLE_RENTER,
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True
        }
        
        users.insert_one(new_user)
        logger.info(f"New user registered: {email} (id: {user_id})")
        
        # Auto-login after registration
        set_user_session({
            'id': user_id,
            'email': email,
            'role': ROLE_RENTER,
            'name': name
        })
        
        return created_response({
            'user': {
                'id': user_id,
                'email': email,
                'name': name,
                'role': ROLE_RENTER
            }
        }, "Registration successful")
        
    except mongo_errors.DuplicateKeyError:
        logger.warning("Registration failed: Duplicate email")
        return validation_error("Email already registered")
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return server_error_response("Registration failed")


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with email and password"""
    logger.info("Request received: POST /auth/login")
    
    try:
        data = request.get_json()
        if not data:
            return validation_error("Request body must be JSON")
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return validation_error("Email and password are required")
        
        users = get_users_collection()
        user = users.find_one({'email': email})
        
        if not user or not check_password_hash(user['password_hash'], password):
            logger.warning(f"Login failed for email: {email}")
            return unauthorized_response("Invalid email or password")
        
        if not user.get('is_active', True):
            logger.warning(f"Login attempt for deactivated account: {email}")
            return unauthorized_response("Account is deactivated")
        
        # Set session
        set_user_session(user)
        
        logger.info(f"User logged in: {email} (role: {user['role']})")
        
        return success_response({
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'role': user['role']
            }
        }, "Login successful")
        
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return server_error_response("Login failed")


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout current user"""
    logger.info(f"Request received: POST /auth/logout (user: {session.get('email', 'unknown')})")
    
    clear_user_session()
    return success_response(message="Logged out successfully")


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_me():
    """Get current user information"""
    logger.info(f"Request received: GET /auth/me (user: {session.get('email')})")
    
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)
    
    return success_response({'user': user})


def create_default_admin():
    """Create a default admin user if none exists"""
    try:
        users = get_users_collection()
        
        # Check if any admin exists
        admin_exists = users.find_one({'role': ROLE_ADMIN})
        if admin_exists:
            logger.info("Admin user already exists")
            return
        
        # Create default admin
        admin_id = str(uuid.uuid4())
        default_admin = {
            'id': admin_id,
            'email': DEFAULT_ADMIN_EMAIL,
            'password_hash': generate_password_hash(DEFAULT_ADMIN_PASSWORD),
            'name': DEFAULT_ADMIN_NAME,
            'role': ROLE_ADMIN,
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True
        }
        
        users.insert_one(default_admin)
        logger.info(f"Default admin user created: {DEFAULT_ADMIN_EMAIL} (password: {DEFAULT_ADMIN_PASSWORD})")
        logger.warning("IMPORTANT: Change the default admin password in production!")
        
    except mongo_errors.DuplicateKeyError:
        logger.info("Default admin already exists")
    except Exception as e:
        logger.error(f"Error creating default admin: {e}")

