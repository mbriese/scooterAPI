"""
Models Package
Contains database models and connection management
"""
from models.database import (
    init_mongodb,
    get_scooters_collection,
    get_users_collection,
    get_database
)

__all__ = ['init_mongodb', 'get_scooters_collection', 'get_users_collection', 'get_database']

