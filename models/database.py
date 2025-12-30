"""
Database Connection Management
Handles MongoDB connection and collection access
"""
import logging
from pymongo import MongoClient, errors as mongo_errors
from config import MONGO_URI, MONGO_DB_NAME, SCOOTERS_COLLECTION, USERS_COLLECTION, RENTALS_COLLECTION

logger = logging.getLogger(__name__)

# MongoDB client and database (module-level singletons)
_mongo_client = None
_mongo_db = None
_scooters_collection = None
_users_collection = None
_rentals_collection = None


def init_mongodb():
    """Initialize MongoDB connection"""
    global _mongo_client, _mongo_db, _scooters_collection, _users_collection, _rentals_collection
    
    try:
        logger.info(f"Connecting to MongoDB at {MONGO_URI}")
        
        # Create MongoDB client
        _mongo_client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        
        # Test connection
        _mongo_client.admin.command('ping')
        logger.info("MongoDB connection successful")
        
        # Get database and collections
        _mongo_db = _mongo_client[MONGO_DB_NAME]
        _scooters_collection = _mongo_db[SCOOTERS_COLLECTION]
        _users_collection = _mongo_db[USERS_COLLECTION]
        _rentals_collection = _mongo_db[RENTALS_COLLECTION]
        
        # Create indexes for scooters
        _scooters_collection.create_index([("id", 1)], unique=True)
        _scooters_collection.create_index([("is_reserved", 1)])
        _scooters_collection.create_index([("lat", 1), ("lng", 1)])
        
        # Create indexes for users
        _users_collection.create_index([("email", 1)], unique=True)
        _users_collection.create_index([("id", 1)], unique=True)
        
        # Create indexes for rentals
        _rentals_collection.create_index([("id", 1)], unique=True)
        _rentals_collection.create_index([("user_id", 1)])
        _rentals_collection.create_index([("scooter_id", 1)])
        _rentals_collection.create_index([("status", 1)])
        _rentals_collection.create_index([("start_time", -1)])
        
        logger.info(f"MongoDB initialized: database='{MONGO_DB_NAME}'")
        return True
        
    except mongo_errors.ServerSelectionTimeoutError:
        logger.error("Failed to connect to MongoDB: Connection timeout")
        return False
    except mongo_errors.ConfigurationError as e:
        logger.error(f"MongoDB configuration error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}", exc_info=True)
        return False


def get_scooters_collection():
    """Get scooters collection with connection check"""
    global _scooters_collection
    
    if _scooters_collection is None:
        logger.warning("Scooters collection not initialized, attempting to connect...")
        if not init_mongodb():
            raise Exception("Failed to initialize MongoDB connection")
    
    return _scooters_collection


def get_users_collection():
    """Get users collection with connection check"""
    global _users_collection
    
    if _users_collection is None:
        logger.warning("Users collection not initialized, attempting to connect...")
        if not init_mongodb():
            raise Exception("Failed to initialize MongoDB connection")
    
    return _users_collection


def get_rentals_collection():
    """Get rentals collection with connection check"""
    global _rentals_collection
    
    if _rentals_collection is None:
        logger.warning("Rentals collection not initialized, attempting to connect...")
        if not init_mongodb():
            raise Exception("Failed to initialize MongoDB connection")
    
    return _rentals_collection


def get_database():
    """Get the MongoDB database instance"""
    global _mongo_db
    
    if _mongo_db is None:
        if not init_mongodb():
            raise Exception("Failed to initialize MongoDB connection")
    
    return _mongo_db

