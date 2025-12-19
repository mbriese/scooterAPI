"""
Routes Package
Contains all API route blueprints
"""
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.scooters import scooters_bp

__all__ = ['auth_bp', 'admin_bp', 'scooters_bp']

