"""
Payment Simulation Module
Simulates credit card charges and generates receipts
NOTE: This is a SIMULATION only - does NOT connect to real payment processors
"""
import logging
from datetime import datetime
from uuid import uuid4
import random

logger = logging.getLogger(__name__)


def generate_transaction_id():
    """Generate a unique transaction ID"""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    random_part = uuid4().hex[:8].upper()
    return f"TXN-{timestamp}-{random_part}"


def generate_authorization_code():
    """Generate a fake authorization code"""
    return f"AUTH{random.randint(100000, 999999)}"


def simulate_charge(amount, payment_method, description="Scooter Rental"):
    """
    Simulate a credit card charge.
    
    In a real application, this would call a payment processor like Stripe, Square, etc.
    This simulation always succeeds (for demo purposes) but mimics the response format
    of real payment processors.
    
    Args:
        amount: Amount to charge in USD
        payment_method: User's payment method dict (from profile)
        description: Charge description
    
    Returns:
        dict with transaction details
    """
    logger.info(f"[PAYMENT SIM] Processing charge of ${amount:.2f}")
    
    if not payment_method:
        logger.warning("[PAYMENT SIM] No payment method on file")
        return {
            'success': False,
            'error': 'No payment method on file',
            'error_code': 'NO_PAYMENT_METHOD'
        }
    
    # Simulate processing time (in real app, this would be an API call)
    # time.sleep(0.5)  # Uncomment to simulate network delay
    
    # Generate transaction details
    transaction_id = generate_transaction_id()
    auth_code = generate_authorization_code()
    
    # Simulate successful charge
    transaction = {
        'success': True,
        'transaction_id': transaction_id,
        'authorization_code': auth_code,
        'amount': round(amount, 2),
        'currency': 'USD',
        'description': description,
        'card_type': payment_method.get('card_type', 'Card'),
        'card_last_four': payment_method.get('card_last_four', '****'),
        'cardholder_name': payment_method.get('cardholder_name', 'CARDHOLDER'),
        'status': 'APPROVED',
        'processed_at': datetime.utcnow().isoformat(),
        'merchant': 'SCOOTER RENTAL CO',
        'merchant_id': 'SCOOT001',
        # Simulation flag
        'is_simulation': True,
        'simulation_note': 'This is a simulated transaction for demonstration purposes only.'
    }
    
    logger.info(f"[PAYMENT SIM] Charge approved: {transaction_id} for ${amount:.2f}")
    
    return transaction


def generate_receipt(rental_data, transaction_data, user_data):
    """
    Generate a detailed receipt for a completed rental.
    
    Args:
        rental_data: Rental record dict
        transaction_data: Transaction result from simulate_charge
        user_data: User profile dict
    
    Returns:
        dict with receipt details
    """
    receipt_number = f"RCP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
    
    cost = rental_data.get('cost', {})
    
    receipt = {
        'receipt_number': receipt_number,
        'date': datetime.utcnow().strftime('%B %d, %Y'),
        'time': datetime.utcnow().strftime('%I:%M %p'),
        
        # Customer info
        'customer': {
            'name': user_data.get('name', 'Customer'),
            'email': user_data.get('email', ''),
        },
        
        # Rental details
        'rental': {
            'scooter_id': rental_data.get('scooter_id'),
            'rental_id': rental_data.get('id'),
            'start_time': rental_data.get('start_time'),
            'end_time': rental_data.get('end_time'),
            'duration': {
                'minutes': cost.get('duration_minutes', 0),
                'hours': cost.get('duration_hours', 0),
                'display': format_duration(cost.get('duration_minutes', 0))
            },
            'start_location': rental_data.get('start_location'),
            'end_location': rental_data.get('end_location'),
            'distance_km': round(rental_data.get('distance_traveled_m', 0) / 1000, 2)
        },
        
        # Charges breakdown
        'charges': {
            'unlock_fee': cost.get('unlock_fee', 0),
            'rental_fee': cost.get('rental_fee', 0),
            'pricing_tier': cost.get('pricing_tier', 'standard'),
            'subtotal': cost.get('total_cost', 0),
            'tax': 0,  # Could add tax calculation
            'total': cost.get('total_cost', 0)
        },
        
        # Payment info
        'payment': {
            'method': f"{transaction_data.get('card_type', 'Card')} ****{transaction_data.get('card_last_four', '****')}",
            'transaction_id': transaction_data.get('transaction_id'),
            'authorization_code': transaction_data.get('authorization_code'),
            'status': transaction_data.get('status', 'APPROVED')
        },
        
        # Merchant info
        'merchant': {
            'name': 'Scooter Rental Co.',
            'address': '123 Main Street, City, ST 12345',
            'phone': '1-800-SCOOTER',
            'website': 'www.scooterrentals.example.com'
        },
        
        # Footer
        'footer': {
            'message': 'Thank you for riding with us!',
            'support': 'Questions? Contact support@scooterrentals.example.com',
            'is_simulation': True,
            'simulation_disclaimer': '*** THIS IS A SIMULATED RECEIPT FOR DEMONSTRATION PURPOSES ***'
        }
    }
    
    return receipt


def format_duration(minutes):
    """Format duration in human-readable format for receipt"""
    if minutes < 60:
        return f"{int(minutes)} minutes"
    elif minutes < 1440:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        if mins > 0:
            return f"{hours} hr {mins} min"
        return f"{hours} hour{'s' if hours > 1 else ''}"
    else:
        days = int(minutes // 1440)
        hours = int((minutes % 1440) // 60)
        if hours > 0:
            return f"{days} day{'s' if days > 1 else ''} {hours} hr"
        return f"{days} day{'s' if days > 1 else ''}"


def format_receipt_text(receipt):
    """
    Format receipt as plain text (for email or printing).
    """
    lines = [
        "=" * 50,
        "           SCOOTER RENTAL RECEIPT",
        "=" * 50,
        "",
        f"Receipt #: {receipt['receipt_number']}",
        f"Date: {receipt['date']} at {receipt['time']}",
        "",
        "-" * 50,
        "CUSTOMER",
        "-" * 50,
        f"Name: {receipt['customer']['name']}",
        f"Email: {receipt['customer']['email']}",
        "",
        "-" * 50,
        "RENTAL DETAILS",
        "-" * 50,
        f"Scooter ID: {receipt['rental']['scooter_id']}",
        f"Duration: {receipt['rental']['duration']['display']}",
        f"Distance: {receipt['rental']['distance_km']} km",
        "",
        "-" * 50,
        "CHARGES",
        "-" * 50,
        f"Unlock Fee:          ${receipt['charges']['unlock_fee']:.2f}",
        f"Rental ({receipt['charges']['pricing_tier']}):  ${receipt['charges']['rental_fee']:.2f}",
        "-" * 30,
        f"TOTAL:               ${receipt['charges']['total']:.2f}",
        "",
        "-" * 50,
        "PAYMENT",
        "-" * 50,
        f"Method: {receipt['payment']['method']}",
        f"Transaction: {receipt['payment']['transaction_id']}",
        f"Auth Code: {receipt['payment']['authorization_code']}",
        f"Status: {receipt['payment']['status']}",
        "",
        "=" * 50,
        receipt['footer']['message'],
        "",
        receipt['footer']['simulation_disclaimer'],
        "=" * 50
    ]
    
    return "\n".join(lines)


