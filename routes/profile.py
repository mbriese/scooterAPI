"""
User Profile Routes
Handles user profile, address, and payment method management
"""
import logging
import re
from datetime import datetime
from flask import Blueprint, request, session

from models.database import get_users_collection
from utils.responses import success_response, validation_error, server_error_response
from utils.auth import login_required

logger = logging.getLogger(__name__)

# Create Blueprint
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


def mask_card_number(card_number):
    """Mask credit card number, showing only last 4 digits"""
    if not card_number:
        return None
    clean = re.sub(r'\D', '', card_number)
    if len(clean) < 4:
        return '****'
    return '**** **** **** ' + clean[-4:]


def detect_card_type(card_number):
    """Detect credit card type from number"""
    if not card_number:
        return 'Unknown'
    clean = re.sub(r'\D', '', card_number)
    
    if clean.startswith('4'):
        return 'Visa'
    elif clean.startswith(('51', '52', '53', '54', '55')) or (2221 <= int(clean[:4]) <= 2720):
        return 'Mastercard'
    elif clean.startswith(('34', '37')):
        return 'American Express'
    elif clean.startswith('6011') or clean.startswith('65'):
        return 'Discover'
    else:
        return 'Credit Card'


def validate_card_number(card_number):
    """Basic credit card validation (Luhn algorithm)"""
    clean = re.sub(r'\D', '', card_number)
    if len(clean) < 13 or len(clean) > 19:
        return False, "Card number must be 13-19 digits"
    
    # Luhn algorithm
    total = 0
    reverse = clean[::-1]
    for i, digit in enumerate(reverse):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    
    if total % 10 != 0:
        return False, "Invalid card number"
    
    return True, clean


def validate_expiry(expiry):
    """Validate card expiry date (MM/YY format)"""
    if not expiry:
        return False, "Expiry date required"
    
    match = re.match(r'^(\d{1,2})/(\d{2})$', expiry.strip())
    if not match:
        return False, "Expiry must be in MM/YY format"
    
    month, year = int(match.group(1)), int(match.group(2))
    
    if month < 1 or month > 12:
        return False, "Invalid month"
    
    # Convert 2-digit year to 4-digit
    full_year = 2000 + year
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    if full_year < current_year or (full_year == current_year and month < current_month):
        return False, "Card has expired"
    
    return True, f"{month:02d}/{year:02d}"


@profile_bp.route('', methods=['GET'])
@login_required
def get_profile():
    """Get current user's profile"""
    user_id = session.get('user_id')
    
    try:
        users = get_users_collection()
        user = users.find_one({'id': user_id}, {'_id': 0, 'password_hash': 0})
        
        if not user:
            return validation_error("User not found")
        
        # Mask card number if present
        if user.get('payment_method', {}).get('card_number'):
            user['payment_method']['card_number_masked'] = user['payment_method'].get('card_number_masked')
            del user['payment_method']['card_number']
        
        return success_response({'profile': user})
        
    except Exception as e:
        logger.error(f"Error getting profile: {e}", exc_info=True)
        return server_error_response("Failed to get profile")


@profile_bp.route('/address', methods=['PUT'])
@login_required
def update_address():
    """Update user's address information"""
    user_id = session.get('user_id')
    
    try:
        data = request.get_json()
        if not data:
            return validation_error("Request body required")
        
        # Extract address fields
        address = {
            'street': data.get('street', '').strip(),
            'city': data.get('city', '').strip(),
            'state': data.get('state', '').strip(),
            'zip_code': data.get('zip_code', '').strip(),
            'country': data.get('country', 'USA').strip(),
            'phone': data.get('phone', '').strip()
        }
        
        # Basic validation
        if not address['city']:
            return validation_error("City is required")
        if not address['state']:
            return validation_error("State is required")
        
        users = get_users_collection()
        users.update_one(
            {'id': user_id},
            {'$set': {
                'address': address,
                'updated_at': datetime.utcnow().isoformat()
            }}
        )
        
        logger.info(f"User {user_id} updated address")
        return success_response({'address': address}, "Address updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating address: {e}", exc_info=True)
        return server_error_response("Failed to update address")


@profile_bp.route('/payment-method', methods=['PUT'])
@login_required
def update_payment_method():
    """Add or update payment method (credit card)"""
    user_id = session.get('user_id')
    user_email = session.get('email')
    
    try:
        data = request.get_json()
        if not data:
            return validation_error("Request body required")
        
        card_number = data.get('card_number', '')
        expiry = data.get('expiry', '')
        cvv = data.get('cvv', '')
        cardholder_name = data.get('cardholder_name', '').strip()
        
        # Validate card number
        is_valid, result = validate_card_number(card_number)
        if not is_valid:
            return validation_error(result)
        clean_card = result
        
        # Validate expiry
        is_valid, result = validate_expiry(expiry)
        if not is_valid:
            return validation_error(result)
        clean_expiry = result
        
        # Validate CVV (3-4 digits)
        cvv_clean = re.sub(r'\D', '', cvv)
        if len(cvv_clean) < 3 or len(cvv_clean) > 4:
            return validation_error("CVV must be 3-4 digits")
        
        # Validate cardholder name
        if not cardholder_name or len(cardholder_name) < 2:
            return validation_error("Cardholder name is required")
        
        # Detect card type
        card_type = detect_card_type(clean_card)
        
        # Create payment method object (store masked, NOT actual card number for security)
        # In a real app, you'd use a payment processor like Stripe
        payment_method = {
            'card_number_masked': mask_card_number(clean_card),
            'card_last_four': clean_card[-4:],
            'card_type': card_type,
            'expiry': clean_expiry,
            'cardholder_name': cardholder_name.upper(),
            'added_at': datetime.utcnow().isoformat(),
            # For simulation purposes, we'll store a token (NOT real card data)
            'token': f"sim_tok_{clean_card[-4:]}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        }
        
        users = get_users_collection()
        users.update_one(
            {'id': user_id},
            {'$set': {
                'payment_method': payment_method,
                'updated_at': datetime.utcnow().isoformat()
            }}
        )
        
        logger.info(f"User {user_email} added payment method: {card_type} ****{clean_card[-4:]}")
        
        # Return sanitized payment info
        return success_response({
            'payment_method': {
                'card_number_masked': payment_method['card_number_masked'],
                'card_type': payment_method['card_type'],
                'expiry': payment_method['expiry'],
                'cardholder_name': payment_method['cardholder_name']
            }
        }, f"{card_type} ending in {clean_card[-4:]} added successfully")
        
    except Exception as e:
        logger.error(f"Error updating payment method: {e}", exc_info=True)
        return server_error_response("Failed to update payment method")


@profile_bp.route('/payment-method', methods=['DELETE'])
@login_required
def remove_payment_method():
    """Remove payment method"""
    user_id = session.get('user_id')
    
    try:
        users = get_users_collection()
        users.update_one(
            {'id': user_id},
            {'$unset': {'payment_method': ''}}
        )
        
        logger.info(f"User {user_id} removed payment method")
        return success_response(message="Payment method removed")
        
    except Exception as e:
        logger.error(f"Error removing payment method: {e}", exc_info=True)
        return server_error_response("Failed to remove payment method")


@profile_bp.route('/payment-method', methods=['GET'])
@login_required
def get_payment_method():
    """Get current payment method (masked)"""
    user_id = session.get('user_id')
    
    try:
        users = get_users_collection()
        user = users.find_one({'id': user_id}, {'payment_method': 1})
        
        if not user or not user.get('payment_method'):
            return success_response({'has_payment_method': False, 'payment_method': None})
        
        pm = user['payment_method']
        return success_response({
            'has_payment_method': True,
            'payment_method': {
                'card_number_masked': pm.get('card_number_masked'),
                'card_type': pm.get('card_type'),
                'expiry': pm.get('expiry'),
                'cardholder_name': pm.get('cardholder_name')
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting payment method: {e}", exc_info=True)
        return server_error_response("Failed to get payment method")

