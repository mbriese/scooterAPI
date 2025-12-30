"""
Admin Routes
Handles admin-only operations like user management and fleet management
"""
import logging
from flask import Blueprint, request, session
from pymongo import errors as mongo_errors

from models.database import get_users_collection, get_scooters_collection
from utils.validators import validate_coordinates, validate_required_fields
from utils.responses import (
    success_response, created_response, validation_error,
    not_found_response, server_error_response
)
from utils.auth import admin_required
from config import ROLE_ADMIN, ROLE_RENTER

logger = logging.getLogger(__name__)

# Create Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """Get all users (admin only)"""
    logger.info(f"Request received: GET /admin/users (admin: {session.get('email')})")
    
    try:
        users = get_users_collection()
        all_users = list(users.find({}, {'_id': 0, 'password_hash': 0}))
        
        return success_response({
            'count': len(all_users),
            'users': all_users
        })
        
    except Exception as e:
        logger.error(f"Error getting users: {e}", exc_info=True)
        return server_error_response("Failed to get users")


@admin_bp.route('/users/<user_id>/role', methods=['PUT'])
@admin_required
def update_user_role(user_id):
    """Update a user's role (admin only)"""
    logger.info(f"Request received: PUT /admin/users/{user_id}/role (admin: {session.get('email')})")
    
    try:
        data = request.get_json()
        if not data or 'role' not in data:
            return validation_error("Role is required")
        
        new_role = data['role']
        if new_role not in [ROLE_ADMIN, ROLE_RENTER]:
            return validation_error(f'Invalid role. Must be "{ROLE_ADMIN}" or "{ROLE_RENTER}"')
        
        # Prevent admin from demoting themselves
        if user_id == session.get('user_id') and new_role != ROLE_ADMIN:
            return validation_error("Cannot demote yourself")
        
        users = get_users_collection()
        result = users.update_one({'id': user_id}, {'$set': {'role': new_role}})
        
        if result.matched_count == 0:
            return not_found_response("User")
        
        logger.info(f"User {user_id} role updated to {new_role} by {session.get('email')}")
        return success_response(message=f"User role updated to {new_role}")
        
    except Exception as e:
        logger.error(f"Error updating user role: {e}", exc_info=True)
        return server_error_response("Failed to update role")


@admin_bp.route('/scooters', methods=['GET', 'POST'])
@admin_required
def manage_scooters():
    """Get all scooters (GET) or add a new scooter (POST) - admin only"""
    
    if request.method == 'GET':
        # Get all scooters in the fleet - both available and reserved
        logger.info(f"Request received: GET /admin/scooters (admin: {session.get('email')})")
        
        try:
            collection = get_scooters_collection()
            all_scooters = list(collection.find({}, {'_id': 0}))
            
            # Calculate stats
            total = len(all_scooters)
            available = sum(1 for s in all_scooters if not s.get('is_reserved', False))
            reserved = total - available
            
            return success_response({
                'stats': {
                    'total': total,
                    'available': available,
                    'reserved': reserved
                },
                'scooters': all_scooters
            })
            
        except Exception as e:
            logger.error(f"Error getting scooters: {e}", exc_info=True)
            return server_error_response("Failed to get scooters")
    
    # POST - Add a new scooter
    logger.info(f"Request received: POST /admin/scooters (admin: {session.get('email')})")
    
    try:
        data = request.get_json()
        if not data:
            return validation_error("Request body must be JSON")
        
        # Validate required fields
        is_valid, missing = validate_required_fields(data, ['id', 'lat', 'lng'])
        if not is_valid:
            return validation_error(f"Missing required fields: {', '.join(missing)}")
        
        # Validate coordinates
        is_valid, result = validate_coordinates(data['lat'], data['lng'])
        if not is_valid:
            return validation_error(result)
        
        lat, lng = result
        scooter_id = str(data['id']).strip()
        
        new_scooter = {
            'id': scooter_id,
            'lat': lat,
            'lng': lng,
            'is_reserved': False
        }
        
        collection = get_scooters_collection()
        collection.insert_one(new_scooter)
        
        logger.info(f"New scooter added: {scooter_id} at ({lat}, {lng}) by {session.get('email')}")
        return created_response({
            'scooter': {'id': scooter_id, 'lat': lat, 'lng': lng, 'is_reserved': False}
        }, "Scooter added successfully")
        
    except mongo_errors.DuplicateKeyError:
        return validation_error("Scooter ID already exists")
    except Exception as e:
        logger.error(f"Error adding scooter: {e}", exc_info=True)
        return server_error_response("Failed to add scooter")


@admin_bp.route('/scooters/<scooter_id>/release', methods=['PUT'])
@admin_required
def force_release_scooter(scooter_id):
    """Force release a reserved scooter (admin only)"""
    logger.info(f"Request received: PUT /admin/scooters/{scooter_id}/release (admin: {session.get('email')})")
    
    try:
        collection = get_scooters_collection()
        
        scooter = collection.find_one({'id': scooter_id})
        if not scooter:
            return not_found_response("Scooter")
        
        if not scooter.get('is_reserved', False):
            return validation_error("Scooter is not currently reserved")
        
        result = collection.update_one(
            {'id': scooter_id},
            {'$set': {'is_reserved': False}}
        )
        
        if result.modified_count > 0:
            logger.warning(f"Scooter {scooter_id} force released by admin {session.get('email')}")
            return success_response(message=f"Scooter {scooter_id} has been released")
        else:
            return server_error_response("Failed to release scooter")
        
    except Exception as e:
        logger.error(f"Error releasing scooter: {e}", exc_info=True)
        return server_error_response("Failed to release scooter")


@admin_bp.route('/scooters/<scooter_id>', methods=['DELETE'])
@admin_required
def delete_scooter(scooter_id):
    """Delete a scooter from the fleet (admin only)"""
    logger.info(f"Request received: DELETE /admin/scooters/{scooter_id} (admin: {session.get('email')})")
    
    try:
        collection = get_scooters_collection()
        
        # Check if scooter exists and is not reserved
        scooter = collection.find_one({'id': scooter_id})
        if not scooter:
            return not_found_response("Scooter")
        
        if scooter.get('is_reserved', False):
            return validation_error("Cannot delete a reserved scooter")
        
        result = collection.delete_one({'id': scooter_id})
        
        if result.deleted_count > 0:
            logger.info(f"Scooter {scooter_id} deleted by {session.get('email')}")
            return success_response(message=f"Scooter {scooter_id} deleted successfully")
        else:
            return not_found_response("Scooter")
        
    except Exception as e:
        logger.error(f"Error deleting scooter: {e}", exc_info=True)
        return server_error_response("Failed to delete scooter")


@admin_bp.route('/scooters/<scooter_id>', methods=['PUT'])
@admin_required
def update_scooter(scooter_id):
    """Update a scooter's details (admin only)"""
    logger.info(f"Request received: PUT /admin/scooters/{scooter_id} (admin: {session.get('email')})")
    
    try:
        data = request.get_json()
        if not data:
            return validation_error("Request body must be JSON")
        
        collection = get_scooters_collection()
        
        # Check if scooter exists
        scooter = collection.find_one({'id': scooter_id})
        if not scooter:
            return not_found_response("Scooter")
        
        # Build update document
        update_fields = {}
        
        if 'lat' in data and 'lng' in data:
            is_valid, result = validate_coordinates(data['lat'], data['lng'])
            if not is_valid:
                return validation_error(result)
            update_fields['lat'], update_fields['lng'] = result
        
        if not update_fields:
            return validation_error("No valid fields to update")
        
        collection.update_one({'id': scooter_id}, {'$set': update_fields})
        
        logger.info(f"Scooter {scooter_id} updated by {session.get('email')}")
        return success_response(message=f"Scooter {scooter_id} updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating scooter: {e}", exc_info=True)
        return server_error_response("Failed to update scooter")

