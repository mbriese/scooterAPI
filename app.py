"""
Scooter API - Main Application
A Flask-based REST API for scooter rental management
"""
import logging
from flask import Flask, send_from_directory, request, json
from flask_cors import CORS
from datetime import datetime

# Import configuration
from config import SECRET_KEY, MAX_PAYLOAD_SIZE

# Import database initialization
from models.database import init_mongodb

# Import route blueprints
from routes.auth import auth_bp, create_default_admin
from routes.admin import admin_bp
from routes.scooters import scooters_bp
from routes.profile import profile_bp
from routes.reports import reports_bp

# ==================
# APP INITIALIZATION
# ==================

app = Flask(__name__, static_folder='static')
app.secret_key = SECRET_KEY
CORS(app, supports_credentials=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scooter_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ==================
# REGISTER BLUEPRINTS
# ==================

app.register_blueprint(auth_bp)      # /auth/*
app.register_blueprint(admin_bp)     # /admin/*
app.register_blueprint(scooters_bp)  # /view_all_available, /search, /reservation/*
app.register_blueprint(profile_bp)   # /profile/*
app.register_blueprint(reports_bp)   # /admin/reports/*


# ==================
# MIDDLEWARE
# ==================

@app.before_request
def before_request_handler():
    """Log and validate incoming requests"""
    logger.info(f"Incoming request: {request.method} {request.path} from {request.remote_addr}")
    
    # Check content length to prevent huge payloads
    if request.content_length and request.content_length > MAX_PAYLOAD_SIZE:
        logger.warning(f"Request rejected: payload too large ({request.content_length} bytes)")
        return json.dumps({'msg': 'Error 413 - Payload too large'}), 413, {'Content-Type': 'application/json'}
    
    # Track request start time
    request.start_time = datetime.now()


@app.after_request
def after_request_handler(response):
    """Log response and add security headers"""
    # Calculate request duration
    if hasattr(request, 'start_time'):
        duration = (datetime.now() - request.start_time).total_seconds()
        logger.info(f"Request completed: {request.method} {request.path} - Status: {response.status_code} - Duration: {duration:.3f}s")
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response


# ==================
# ERROR HANDLERS
# ==================

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 Error: {request.url} not found")
    return json.dumps({'msg': 'Error 404 - Resource not found'}), 404, {'Content-Type': 'application/json'}


@app.errorhandler(413)
def payload_too_large(error):
    logger.warning("413 Error: Payload too large")
    return json.dumps({'msg': 'Error 413 - Payload too large'}), 413, {'Content-Type': 'application/json'}


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Error: {str(error)}")
    return json.dumps({'msg': 'Error 500 - Internal server error'}), 500, {'Content-Type': 'application/json'}


@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
    return json.dumps({'msg': 'Error 500 - An unexpected error occurred'}), 500, {'Content-Type': 'application/json'}


# ==================
# ROOT ROUTE
# ==================

@app.route('/')
def home():
    """Serve the web interface"""
    return send_from_directory('static', 'index.html')


# ==================
# MAIN ENTRY POINT
# ==================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Scooter API server on localhost:5000")
    logger.info("=" * 60)
    
    # Initialize MongoDB connection
    logger.info("Initializing MongoDB connection...")
    if init_mongodb():
        logger.info("MongoDB connection established successfully")
        
        # Create default admin user if none exists
        create_default_admin()
    else:
        logger.error("Failed to connect to MongoDB - server starting anyway")
        logger.error("MongoDB operations will fail until connection is established")
    
    logger.info("=" * 60)
    logger.info("API Endpoints:")
    logger.info("  Auth:    /auth/register, /auth/login, /auth/logout, /auth/me")
    logger.info("  Admin:   /admin/users, /admin/scooters")
    logger.info("  Scooters: /view_all_available, /search, /reservation/*")
    logger.info("=" * 60)
    
    app.run('localhost', 5000)
