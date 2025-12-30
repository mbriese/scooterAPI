"""
Application Configuration
Centralized configuration settings for the Scooter API
"""
import os
import uuid

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production-' + str(uuid.uuid4()))
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# MongoDB Configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'scooter_db')
SCOOTERS_COLLECTION = 'scooters'
USERS_COLLECTION = 'users'

# User Roles
ROLE_ADMIN = 'admin'
ROLE_RENTER = 'renter'

# Default Admin Credentials (change in production!)
DEFAULT_ADMIN_EMAIL = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@scooter.com')
DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
DEFAULT_ADMIN_NAME = 'Admin User'

# Validation Limits
MAX_SEARCH_RADIUS = 50000  # meters (50km)
MAX_SCOOTER_ID_LENGTH = 100
MIN_PASSWORD_LENGTH = 6
MAX_PAYLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# ===========================================
# RENTAL PRICING CONFIGURATION
# ===========================================
# All prices in USD

# Base unlock fee (charged at start of every rental)
RENTAL_UNLOCK_FEE = 1.00

# Hourly rate (for rentals under 24 hours)
RENTAL_HOURLY_RATE = 3.50
RENTAL_MIN_CHARGE_MINUTES = 15  # Minimum billing increment

# Daily rate (24-hour period, better than 24 x hourly)
RENTAL_DAILY_RATE = 25.00

# Multi-day rates (discounted)
RENTAL_MULTIDAY_RATES = {
    2: 45.00,   # 2 days - 10% off
    3: 63.00,   # 3 days - 16% off
    4: 80.00,   # 4 days - 20% off
    5: 95.00,   # 5 days - 24% off
    6: 108.00,  # 6 days - 28% off
}

# Weekly rate (7 days)
RENTAL_WEEKLY_RATE = 99.00  # ~$14/day, 43% off daily rate

# Monthly rate (30 days)
RENTAL_MONTHLY_RATE = 299.00  # ~$10/day, 60% off daily rate

# Maximum rental duration (days)
RENTAL_MAX_DURATION_DAYS = 30

# Grace period (minutes) - no charge for very short accidental unlocks
RENTAL_GRACE_PERIOD_MINUTES = 2

# MongoDB Collection for rentals
RENTALS_COLLECTION = 'rentals'

# Legacy file-based DB (for migration)
DB_FILE = 'scooter_db.json'
DB_BACKUP_DIR = 'db_backups'

