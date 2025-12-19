#!/usr/bin/env python3
"""
Data Migration Script: JSON File to MongoDB
This script migrates scooter data from the JSON file database to MongoDB.
Run this once after setting up MongoDB.

Usage:
    python migrate_to_mongodb.py

Environment Variables:
    MONGO_URI - MongoDB connection string (default: mongodb://localhost:27017/)
    MONGO_DB_NAME - Database name (default: scooter_db)
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the migration function from app
try:
    from app import init_mongodb, migrate_json_to_mongodb, export_mongodb_to_json
except ImportError as e:
    logger.error(f"Failed to import app module: {e}")
    logger.error("Make sure this script is in the same directory as app.py")
    sys.exit(1)

def main():
    """Main migration function"""
    print("=" * 60)
    print("Scooter API - JSON to MongoDB Migration Tool")
    print("=" * 60)
    print()
    
    # Show configuration
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    mongo_db = os.environ.get('MONGO_DB_NAME', 'scooter_db')
    
    print(f"MongoDB URI: {mongo_uri}")
    print(f"Database: {mongo_db}")
    print()
    
    # Initialize MongoDB
    logger.info("Step 1: Connecting to MongoDB...")
    if not init_mongodb():
        logger.error("Failed to connect to MongoDB")
        print("\nMigration failed! Check your MongoDB connection.")
        print("Make sure MongoDB is running and accessible.")
        sys.exit(1)
    
    print("[OK] Connected to MongoDB successfully")
    print()
    
    # Run migration
    logger.info("Step 2: Migrating data from JSON to MongoDB...")
    success, message = migrate_json_to_mongodb()
    
    if success:
        print(f"[SUCCESS] Migration successful: {message}")
        print()
        print("Your scooter API is now using MongoDB!")
        print()
        print("Next steps:")
        print("1. Backup your scooter_db.json file")
        print("2. Test the API endpoints")
        print("3. You can now run: python app.py")
        return 0
    else:
        print(f"[ERROR] Migration failed: {message}")
        print()
        print("Please check the error messages above and try again.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)

