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

# Legacy file-based DB (for migration)
DB_FILE = 'scooter_db.json'
DB_BACKUP_DIR = 'db_backups'

