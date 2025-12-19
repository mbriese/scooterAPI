"""
Scooter Routes
Handles scooter viewing, searching, and reservations
"""
import logging
import json
from flask import Blueprint, request
from geopy.distance import distance as geodesic
from pymongo import errors as mongo_errors

from models.database import get_scooters_collection
from utils.validators import validate_coordinates, validate_radius, validate_scooter_id
from utils.responses import (
    success_response, list_response, validation_error,
    not_found_response, server_error_response
)
from config import ROLE_RENTER

logger = logging.getLogger(__name__)

# Create Blueprint
scooters_bp = Blueprint('scooters', __name__)


@scooters_bp.route('/view_all_available')
def view_all_available():
    """Get all available (non-reserved) scooters"""
    logger.info("[BREADCRUMB 1] Request received: GET /view_all_available")
    logger.debug(f"Request from: {request.remote_addr}")
    
    try:
        logger.info("[BREADCRUMB 2] Getting MongoDB collection")
        collection = get_scooters_collection()
        logger.info("[BREADCRUMB 2] Collection retrieved successfully")
        
        logger.info("[BREADCRUMB 3] Executing query for available scooters")
        available_scooters = list(collection.find(
            {"is_reserved": False},
            {"_id": 0}
        ))
        logger.info(f"[BREADCRUMB 3] Query complete - Found {len(available_scooters)} scooters")
        
        if not available_scooters:
            logger.warning("No available scooters found in database")
        else:
            scooter_ids = [s.get('id', 'unknown') for s in available_scooters]
            logger.debug(f"Available scooter IDs: {scooter_ids}")
        
        logger.info(f"[BREADCRUMB 4] Returning {len(available_scooters)} available scooters")
        return list_response(available_scooters)
        
    except mongo_errors.PyMongoError as e:
        logger.error(f"[ERROR] MongoDB error: {e}")
        return server_error_response("Database error")
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error: {e}", exc_info=True)
        return server_error_response("Failed to retrieve scooters")


@scooters_bp.route('/search', methods=['GET'])
def search():
    """Search for available scooters within a radius"""
    logger.info(f"Request received: GET /search - params: {dict(request.args)}")
    
    # Check for required parameters
    if not all(p in request.args for p in ['lat', 'lng', 'radius']):
        logger.warning("Search failed: Missing required parameters")
        return validation_error("Please include all required parameters (lat, lng, radius)")
    
    # Validate coordinates
    is_valid, result = validate_coordinates(request.args['lat'], request.args['lng'])
    if not is_valid:
        logger.warning(f"Search failed: {result}")
        return validation_error(result)
    search_lat, search_lng = result
    
    # Validate radius
    is_valid, result = validate_radius(request.args['radius'])
    if not is_valid:
        logger.warning(f"Search failed: {result}")
        return validation_error(result)
    search_radius = result
    
    logger.info(f"Search parameters: lat={search_lat}, lng={search_lng}, radius={search_radius}m")
    
    try:
        collection = get_scooters_collection()
        all_scooters = collection.find({"is_reserved": False}, {"_id": 0})
        
        search_results = []
        for scooter in all_scooters:
            try:
                distance = geodesic(
                    (scooter['lat'], scooter['lng']),
                    (search_lat, search_lng)
                ).m
                
                if distance <= search_radius:
                    search_results.append({
                        'id': scooter['id'],
                        'lat': scooter['lat'],
                        'lng': scooter['lng'],
                        'distance': round(distance, 2)
                    })
            except Exception as e:
                logger.warning(f"Error calculating distance for scooter {scooter.get('id')}: {e}")
                continue
        
        # Sort by distance
        search_results.sort(key=lambda x: x['distance'])
        
        logger.info(f"Search completed: Found {len(search_results)} scooters within {search_radius}m")
        return list_response(search_results)
        
    except mongo_errors.PyMongoError as e:
        logger.error(f"MongoDB error during search: {e}")
        return server_error_response("Database error")
    except Exception as e:
        logger.error(f"Failed to search: {e}", exc_info=True)
        return server_error_response("Search failed")


@scooters_bp.route('/reservation/start', methods=['GET'])
def start_reservation():
    """Start a reservation for a scooter"""
    logger.info(f"Request received: GET /reservation/start - params: {dict(request.args)}")
    
    # Check for required parameter
    if 'id' not in request.args:
        logger.warning("Reservation start failed: Missing 'id' parameter")
        return validation_error("Please include required parameter: id")
    
    # Validate scooter ID
    is_valid, result = validate_scooter_id(request.args['id'])
    if not is_valid:
        logger.warning(f"Reservation start failed: {result}")
        return validation_error(result)
    reserve_id = result
    
    logger.info(f"Attempting to reserve scooter: {reserve_id}")
    
    try:
        collection = get_scooters_collection()
        
        # Try to atomically update the scooter if it's not reserved
        result = collection.update_one(
            {"id": reserve_id, "is_reserved": False},
            {"$set": {"is_reserved": True}}
        )
        
        if result.matched_count == 0:
            # Either scooter doesn't exist or is already reserved
            scooter = collection.find_one({"id": reserve_id})
            if scooter is None:
                logger.warning(f"Reservation failed: Scooter {reserve_id} not found")
                return validation_error(f"No scooter with id {reserve_id} was found.")
            else:
                logger.warning(f"Reservation failed: Scooter {reserve_id} is already reserved")
                return validation_error(f"Scooter with id {reserve_id} is already reserved.")
        
        logger.info(f"Scooter {reserve_id} reserved successfully")
        return success_response(message=f"Scooter {reserve_id} was reserved successfully.")
        
    except mongo_errors.PyMongoError as e:
        logger.error(f"MongoDB error during reservation: {e}")
        return server_error_response("Database error")
    except Exception as e:
        logger.error(f"Failed to start reservation: {e}", exc_info=True)
        return server_error_response("Failed to save reservation")


@scooters_bp.route('/reservation/end', methods=['GET'])
def end_reservation():
    """End a reservation and update scooter location"""
    logger.info(f"Request received: GET /reservation/end - params: {dict(request.args)}")
    
    # Check for required parameters
    if not all(p in request.args for p in ['id', 'lat', 'lng']):
        logger.warning("Reservation end failed: Missing required parameters")
        return validation_error("Please include all required parameters (id, lat, lng)")
    
    # Validate scooter ID
    is_valid, result = validate_scooter_id(request.args['id'])
    if not is_valid:
        return validation_error(result)
    scooter_id = result
    
    # Validate coordinates
    is_valid, result = validate_coordinates(request.args['lat'], request.args['lng'])
    if not is_valid:
        return validation_error(result)
    end_lat, end_lng = result
    
    logger.info(f"Ending reservation for scooter {scooter_id} at ({end_lat}, {end_lng})")
    
    try:
        collection = get_scooters_collection()
        
        # Find the scooter
        scooter = collection.find_one({"id": scooter_id}, {"_id": 0})
        
        if scooter is None:
            logger.warning(f"Reservation end failed: Scooter {scooter_id} not found")
            return validation_error(f"No scooter with id {scooter_id} was found.")
        
        if not scooter.get('is_reserved', False):
            logger.warning(f"Reservation end failed: Scooter {scooter_id} is not reserved")
            return validation_error(f"No reservation for scooter {scooter_id} presently exists.")
        
        # Process payment
        logger.info(f"Processing payment for scooter {scooter_id}")
        payment_response = _process_payment(scooter, end_lat, end_lng)
        
        if payment_response['status']:
            # Update scooter
            collection.update_one(
                {"id": scooter_id, "is_reserved": True},
                {"$set": {
                    "is_reserved": False,
                    "lat": end_lat,
                    "lng": end_lng
                }}
            )
            
            logger.info(f"Reservation ended for scooter {scooter_id}, txn_id: {payment_response['txn_id']}")
            return success_response({
                'txn_id': payment_response['txn_id']
            }, f"Payment for scooter {scooter_id} was made successfully and the reservation was ended.")
        else:
            logger.error(f"Payment failed for scooter {scooter_id}")
            return server_error_response(payment_response.get('msg', 'Payment failed'))
            
    except mongo_errors.PyMongoError as e:
        logger.error(f"MongoDB error during reservation end: {e}")
        return server_error_response("Database error")
    except Exception as e:
        logger.error(f"Failed to end reservation: {e}", exc_info=True)
        return server_error_response("Failed to end reservation")


def _process_payment(scooter, end_lat, end_lng):
    """Process payment for a reservation (internal helper)"""
    try:
        # Calculate distance
        old_location = (scooter['lat'], scooter['lng'])
        new_location = (end_lat, end_lng)
        distance_ridden = geodesic(old_location, new_location).m
        distance_ridden = round(distance_ridden)
        
        logger.info(f"Distance calculation - Scooter {scooter['id']}: {distance_ridden}m")
        
        # Calculate cost (currently distance = cost)
        cost = distance_ridden
        logger.info(f"Cost calculation - Scooter {scooter['id']}: ${cost}")
        
        # Mock payment gateway
        # TODO: Implement real payment processing
        txn_id = 379892831
        
        return {'status': True, 'txn_id': txn_id}
        
    except Exception as e:
        logger.error(f"Payment processing error: {e}")
        return {'status': False, 'msg': 'Payment processing failed'}

