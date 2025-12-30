"""
Scooter Routes
Handles scooter viewing, searching, and reservations
"""
import logging
import json
from datetime import datetime
from uuid import uuid4
from flask import Blueprint, request, session
from geopy.distance import distance as geodesic
from pymongo import errors as mongo_errors

from models.database import get_scooters_collection, get_rentals_collection, get_users_collection
from utils.validators import validate_coordinates, validate_radius, validate_scooter_id
from utils.responses import (
    success_response, list_response, validation_error,
    not_found_response, server_error_response
)
from utils.pricing import calculate_rental_cost, get_pricing_info
from utils.payment import simulate_charge, generate_receipt
from utils.auth import login_required
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


@scooters_bp.route('/reservation/start', methods=['GET', 'POST'])
@login_required
def start_reservation():
    """Start a reservation for a scooter (requires login)"""
    logger.info(f"Request received: {request.method} /reservation/start - params: {dict(request.args)}")
    
    user_id = session.get('user_id')
    user_email = session.get('email')
    
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
    
    logger.info(f"User {user_email} attempting to reserve scooter: {reserve_id}")
    
    try:
        scooters = get_scooters_collection()
        rentals = get_rentals_collection()
        
        # Check if user already has an active rental
        active_rental = rentals.find_one({
            "user_id": user_id,
            "status": "active"
        })
        if active_rental:
            logger.warning(f"User {user_email} already has active rental: {active_rental['scooter_id']}")
            return validation_error(f"You already have an active rental (Scooter {active_rental['scooter_id']}). Please end it first.")
        
        # Get scooter details first
        scooter = scooters.find_one({"id": reserve_id}, {"_id": 0})
        if scooter is None:
            logger.warning(f"Reservation failed: Scooter {reserve_id} not found")
            return validation_error(f"No scooter with id {reserve_id} was found.")
        
        # Try to atomically update the scooter if it's not reserved
        start_time = datetime.utcnow()
        rental_id = str(uuid4())
        
        result = scooters.update_one(
            {"id": reserve_id, "is_reserved": False},
            {"$set": {
                "is_reserved": True,
                "current_rental_id": rental_id,
                "rented_by": user_id,
                "rental_start_time": start_time.isoformat()
            }}
        )
        
        if result.matched_count == 0:
            logger.warning(f"Reservation failed: Scooter {reserve_id} is already reserved")
            return validation_error(f"Scooter with id {reserve_id} is already reserved.")
        
        # Create rental record
        rental_record = {
            "id": rental_id,
            "user_id": user_id,
            "user_email": user_email,
            "scooter_id": reserve_id,
            "start_time": start_time.isoformat(),
            "start_location": {
                "lat": scooter['lat'],
                "lng": scooter['lng']
            },
            "end_time": None,
            "end_location": None,
            "status": "active",
            "cost": None,
            "created_at": start_time.isoformat()
        }
        
        rentals.insert_one(rental_record)
        
        # Get pricing info to return to user
        pricing = get_pricing_info()
        
        logger.info(f"Scooter {reserve_id} reserved successfully by {user_email} (rental: {rental_id})")
        return success_response({
            'rental_id': rental_id,
            'scooter_id': reserve_id,
            'start_time': start_time.isoformat(),
            'pricing': pricing
        }, f"Scooter {reserve_id} was reserved successfully. Unlock fee: ${pricing['unlock_fee']:.2f}")
        
    except mongo_errors.PyMongoError as e:
        logger.error(f"MongoDB error during reservation: {e}")
        return server_error_response("Database error")
    except Exception as e:
        logger.error(f"Failed to start reservation: {e}", exc_info=True)
        return server_error_response("Failed to save reservation")


@scooters_bp.route('/reservation/end', methods=['GET', 'POST'])
@login_required
def end_reservation():
    """End a reservation, calculate charges, and update scooter location"""
    logger.info(f"Request received: {request.method} /reservation/end - params: {dict(request.args)}")
    
    user_id = session.get('user_id')
    user_email = session.get('email')
    
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
    
    logger.info(f"User {user_email} ending reservation for scooter {scooter_id} at ({end_lat}, {end_lng})")
    
    try:
        scooters = get_scooters_collection()
        rentals = get_rentals_collection()
        
        # Find the scooter
        scooter = scooters.find_one({"id": scooter_id}, {"_id": 0})
        
        if scooter is None:
            logger.warning(f"Reservation end failed: Scooter {scooter_id} not found")
            return validation_error(f"No scooter with id {scooter_id} was found.")
        
        if not scooter.get('is_reserved', False):
            logger.warning(f"Reservation end failed: Scooter {scooter_id} is not reserved")
            return validation_error(f"No reservation for scooter {scooter_id} presently exists.")
        
        # Verify this user owns the rental (or is admin)
        rental_id = scooter.get('current_rental_id')
        rental = rentals.find_one({"id": rental_id}) if rental_id else None
        
        if rental and rental.get('user_id') != user_id and session.get('role') != 'admin':
            logger.warning(f"User {user_email} tried to end rental owned by {rental.get('user_email')}")
            return validation_error("You can only end your own rentals.")
        
        # Calculate end time and cost
        end_time = datetime.utcnow()
        
        # Get start time from rental record or scooter
        start_time_str = rental.get('start_time') if rental else scooter.get('rental_start_time')
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        else:
            # Fallback: assume rental just started (shouldn't happen)
            logger.warning(f"No start time found for rental, using current time")
            start_time = end_time
        
        # Calculate rental cost
        cost_breakdown = calculate_rental_cost(start_time, end_time)
        
        # Calculate distance traveled
        start_location = rental.get('start_location', {'lat': scooter['lat'], 'lng': scooter['lng']}) if rental else {'lat': scooter['lat'], 'lng': scooter['lng']}
        distance_traveled = geodesic(
            (start_location['lat'], start_location['lng']),
            (end_lat, end_lng)
        ).m
        
        logger.info(f"Rental cost for scooter {scooter_id}: ${cost_breakdown['total_cost']:.2f} ({cost_breakdown['pricing_tier']})")
        
        # Get user's payment method
        users = get_users_collection()
        user = users.find_one({"id": user_id}, {"_id": 0})
        payment_method = user.get('payment_method') if user else None
        
        # Process payment (simulation)
        transaction = simulate_charge(
            amount=cost_breakdown['total_cost'],
            payment_method=payment_method,
            description=f"Scooter Rental - {scooter_id}"
        )
        
        if not transaction['success']:
            logger.warning(f"Payment failed for rental {rental_id}: {transaction.get('error')}")
            # Even if payment fails, we'll complete the rental (in real app, might handle differently)
            # For simulation, we'll just note it
        
        # Prepare rental data for receipt
        rental_data = {
            'id': rental_id,
            'scooter_id': scooter_id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'start_location': start_location,
            'end_location': {'lat': end_lat, 'lng': end_lng},
            'distance_traveled_m': round(distance_traveled),
            'cost': cost_breakdown
        }
        
        # Generate receipt
        receipt = generate_receipt(rental_data, transaction, user or {})
        
        # Update rental record with payment and receipt info
        if rental:
            rentals.update_one(
                {"id": rental_id},
                {"$set": {
                    "end_time": end_time.isoformat(),
                    "end_location": {"lat": end_lat, "lng": end_lng},
                    "status": "completed",
                    "cost": cost_breakdown,
                    "distance_traveled_m": round(distance_traveled),
                    "transaction": transaction,
                    "receipt": receipt,
                    "completed_at": end_time.isoformat()
                }}
            )
        
        # Update scooter - release it and move to new location
        scooters.update_one(
            {"id": scooter_id},
            {"$set": {
                "is_reserved": False,
                "lat": end_lat,
                "lng": end_lng
            },
            "$unset": {
                "current_rental_id": "",
                "rented_by": "",
                "rental_start_time": ""
            }}
        )
        
        logger.info(f"Reservation ended for scooter {scooter_id} by {user_email}, cost: ${cost_breakdown['total_cost']:.2f}, txn: {transaction.get('transaction_id')}")
        
        return success_response({
            'rental_id': rental_id,
            'scooter_id': scooter_id,
            'transaction': {
                'id': transaction.get('transaction_id'),
                'authorization_code': transaction.get('authorization_code'),
                'status': transaction.get('status'),
                'card': f"{transaction.get('card_type', 'Card')} ****{transaction.get('card_last_four', '****')}",
                'is_simulation': True
            },
            'duration': {
                'minutes': cost_breakdown['duration_minutes'],
                'hours': cost_breakdown['duration_hours'],
                'days': cost_breakdown['duration_days']
            },
            'distance_traveled_m': round(distance_traveled),
            'cost': {
                'unlock_fee': cost_breakdown['unlock_fee'],
                'rental_fee': cost_breakdown['rental_fee'],
                'total': cost_breakdown['total_cost'],
                'pricing_tier': cost_breakdown['pricing_tier'],
                'description': cost_breakdown['description']
            },
            'receipt': receipt
        }, f"Rental completed! Total charge: ${cost_breakdown['total_cost']:.2f}")
            
    except mongo_errors.PyMongoError as e:
        logger.error(f"MongoDB error during reservation end: {e}")
        return server_error_response("Database error")
    except Exception as e:
        logger.error(f"Failed to end reservation: {e}", exc_info=True)
        return server_error_response("Failed to end reservation")


@scooters_bp.route('/pricing', methods=['GET'])
def get_pricing():
    """Get current rental pricing information"""
    logger.info("Request received: GET /pricing")
    pricing = get_pricing_info()
    return success_response({
        'pricing': pricing,
        'summary': {
            'unlock_fee': f"${pricing['unlock_fee']:.2f}",
            'hourly': f"${pricing['hourly_rate']:.2f}/hr",
            'daily': f"${pricing['daily_rate']:.2f}/day",
            'weekly': f"${pricing['weekly_rate']:.2f}/week",
            'monthly': f"${pricing['monthly_rate']:.2f}/month"
        }
    })


@scooters_bp.route('/rentals/history', methods=['GET'])
@login_required
def get_rental_history():
    """Get rental history for the current user"""
    user_id = session.get('user_id')
    user_email = session.get('email')
    
    logger.info(f"Request received: GET /rentals/history for user {user_email}")
    
    try:
        rentals = get_rentals_collection()
        
        # Get user's rentals, sorted by start_time descending (newest first)
        user_rentals = list(rentals.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("start_time", -1).limit(50))  # Limit to last 50 rentals
        
        # Calculate totals
        total_spent = sum(
            r.get('cost', {}).get('total_cost', 0) 
            for r in user_rentals 
            if r.get('status') == 'completed'
        )
        total_rentals = len([r for r in user_rentals if r.get('status') == 'completed'])
        active_rental = next((r for r in user_rentals if r.get('status') == 'active'), None)
        
        logger.info(f"Found {len(user_rentals)} rentals for user {user_email}")
        
        return success_response({
            'rentals': user_rentals,
            'summary': {
                'total_rentals': total_rentals,
                'total_spent': round(total_spent, 2),
                'has_active_rental': active_rental is not None,
                'active_rental': active_rental
            }
        })
        
    except mongo_errors.PyMongoError as e:
        logger.error(f"MongoDB error getting rental history: {e}")
        return server_error_response("Database error")
    except Exception as e:
        logger.error(f"Failed to get rental history: {e}", exc_info=True)
        return server_error_response("Failed to get rental history")


@scooters_bp.route('/rentals/active', methods=['GET'])
@login_required
def get_active_rental():
    """Get the current user's active rental (if any)"""
    user_id = session.get('user_id')
    user_email = session.get('email')
    
    logger.info(f"Request received: GET /rentals/active for user {user_email}")
    
    try:
        rentals = get_rentals_collection()
        
        active_rental = rentals.find_one(
            {"user_id": user_id, "status": "active"},
            {"_id": 0}
        )
        
        if active_rental:
            # Calculate current cost estimate
            start_time = datetime.fromisoformat(active_rental['start_time'].replace('Z', '+00:00'))
            current_cost = calculate_rental_cost(start_time)
            
            return success_response({
                'has_active_rental': True,
                'rental': active_rental,
                'current_cost_estimate': current_cost
            })
        else:
            return success_response({
                'has_active_rental': False,
                'rental': None
            })
        
    except mongo_errors.PyMongoError as e:
        logger.error(f"MongoDB error getting active rental: {e}")
        return server_error_response("Database error")
    except Exception as e:
        logger.error(f"Failed to get active rental: {e}", exc_info=True)
        return server_error_response("Failed to get active rental")

