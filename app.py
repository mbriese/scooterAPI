from flask import Flask, render_template, request, redirect, url_for, make_response, send_from_directory
from flask_cors import CORS
from geopy.distance import distance as geodesic
import json, werkzeug
from http import HTTPStatus
import logging
import os
import shutil
from datetime import datetime
from pymongo import MongoClient, errors as mongo_errors
from pymongo.server_api import ServerApi

app=Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

# Constants
DB_FILE = 'scooter_db.json'  # Kept for migration/backup purposes
DB_BACKUP_DIR = 'db_backups'

# MongoDB Configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'scooter_db')
MONGO_COLLECTION_NAME = 'scooters'

# MongoDB client and database (initialized later)
mongo_client = None
mongo_db = None
scooters_collection = None

# Configure logging
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	handlers=[
		logging.FileHandler('scooter_api.log'),
		logging.StreamHandler()
	]
)
logger = logging.getLogger(__name__)

# MongoDB Connection Management
def init_mongodb():
	"""Initialize MongoDB connection"""
	global mongo_client, mongo_db, scooters_collection
	
	try:
		logger.info(f"Connecting to MongoDB at {MONGO_URI}")
		
		# Create MongoDB client
		mongo_client = MongoClient(
			MONGO_URI,
			serverSelectionTimeoutMS=5000,  # 5 second timeout
			connectTimeoutMS=5000
		)
		
		# Test connection
		mongo_client.admin.command('ping')
		logger.info("MongoDB connection successful")
		
		# Get database and collection
		mongo_db = mongo_client[MONGO_DB_NAME]
		scooters_collection = mongo_db[MONGO_COLLECTION_NAME]
		
		# Create indexes for better performance
		scooters_collection.create_index([("id", 1)], unique=True)
		scooters_collection.create_index([("is_reserved", 1)])
		scooters_collection.create_index([("lat", 1), ("lng", 1)])
		
		logger.info(f"MongoDB initialized: database='{MONGO_DB_NAME}', collection='{MONGO_COLLECTION_NAME}'")
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

def get_mongodb_collection():
	"""Get MongoDB collection with connection check"""
	global scooters_collection
	
	if scooters_collection is None:
		logger.warning("MongoDB collection not initialized, attempting to connect...")
		if not init_mongodb():
			raise Exception("Failed to initialize MongoDB connection")
	
	return scooters_collection

def migrate_json_to_mongodb():
	"""Migrate data from JSON file to MongoDB (one-time operation)"""
	try:
		logger.info("Starting data migration from JSON to MongoDB...")
		
		# Check if JSON file exists
		if not os.path.exists(DB_FILE):
			logger.error(f"JSON database file {DB_FILE} not found")
			return False, "JSON file not found"
		
		# Read JSON data
		with open(DB_FILE, 'r', encoding='utf-8') as f:
			data = json.loads(f.read())
		
		if not isinstance(data, list):
			logger.error("JSON data is not a list")
			return False, "Invalid JSON format"
		
		# Get MongoDB collection
		collection = get_mongodb_collection()
		
		# Check if collection already has data
		existing_count = collection.count_documents({})
		if existing_count > 0:
			logger.warning(f"MongoDB collection already contains {existing_count} documents")
			user_input = input(f"Collection already has {existing_count} documents. Overwrite? (yes/no): ")
			if user_input.lower() != 'yes':
				logger.info("Migration cancelled by user")
				return False, "Migration cancelled"
			# Clear existing data
			collection.delete_many({})
			logger.info(f"Cleared {existing_count} existing documents")
		
		# Insert data
		if data:
			# Ensure each document has required fields
			valid_docs = []
			for idx, doc in enumerate(data):
				if isinstance(doc, dict) and all(k in doc for k in ['id', 'lat', 'lng', 'is_reserved']):
					valid_docs.append(doc)
				else:
					logger.warning(f"Skipping invalid document at index {idx}")
			
			if valid_docs:
				result = collection.insert_many(valid_docs, ordered=False)
				logger.info(f"Successfully migrated {len(result.inserted_ids)} documents to MongoDB")
				return True, f"Migrated {len(result.inserted_ids)} scooters"
			else:
				logger.warning("No valid documents to migrate")
				return False, "No valid documents"
		else:
			logger.info("JSON file is empty, nothing to migrate")
			return True, "No data to migrate"
			
	except mongo_errors.DuplicateKeyError as e:
		logger.error(f"Duplicate key error during migration: {e}")
		return False, "Duplicate IDs in data"
	except mongo_errors.PyMongoError as e:
		logger.error(f"MongoDB error during migration: {e}")
		return False, str(e)
	except Exception as e:
		logger.error(f"Error during migration: {e}", exc_info=True)
		return False, str(e)

def export_mongodb_to_json(output_file='scooter_db_export.json'):
	"""Export MongoDB data to JSON file (for backup)"""
	try:
		logger.info("Exporting MongoDB data to JSON...")
		
		collection = get_mongodb_collection()
		all_scooters = list(collection.find({}, {"_id": 0}))
		
		# Write to JSON file
		with open(output_file, 'w', encoding='utf-8') as f:
			json.dump(all_scooters, f, indent=2, ensure_ascii=False)
		
		logger.info(f"Successfully exported {len(all_scooters)} scooters to {output_file}")
		return True, f"Exported {len(all_scooters)} scooters"
		
	except Exception as e:
		logger.error(f"Error during export: {e}", exc_info=True)
		return False, str(e)

# Request/Response middleware
@app.before_request
def before_request_handler():
	"""Log and validate incoming requests"""
	# Log request details
	logger.info(f"Incoming request: {request.method} {request.path} from {request.remote_addr}")
	
	# Check content length to prevent huge payloads
	if request.content_length and request.content_length > 10 * 1024 * 1024:  # 10MB limit
		logger.warning(f"Request rejected: payload too large ({request.content_length} bytes)")
		return json.dumps({'msg': 'Error 413 - Payload too large'}), 413, {'Content-Type': 'application/json'}
	
	# Track request start time for performance monitoring
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

# Global error handlers
@app.errorhandler(404)
def not_found(error):
	logger.warning(f"404 Error: {request.url} not found")
	return json.dumps({'msg': 'Error 404 - Resource not found'}), 404, {'Content-Type': 'application/json'}

@app.errorhandler(413)
def payload_too_large(error):
	logger.warning(f"413 Error: Payload too large")
	return json.dumps({'msg': 'Error 413 - Payload too large'}), 413, {'Content-Type': 'application/json'}

@app.errorhandler(500)
def internal_error(error):
	logger.error(f"500 Error: {str(error)}")
	return json.dumps({'msg': 'Error 500 - Internal server error'}), 500, {'Content-Type': 'application/json'}

@app.errorhandler(Exception)
def handle_exception(error):
	logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
	return json.dumps({'msg': 'Error 500 - An unexpected error occurred'}), 500, {'Content-Type': 'application/json'}

# root - serve the web interface
@app.route('/')
def home():
	return send_from_directory('static', 'index.html')
	
@app.route('/view_all_available')
def view_all_available():
	logger.info("🔍 BREADCRUMB 1: Request received: GET /view_all_available")
	logger.debug(f"Request details - Remote: {request.remote_addr}, User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
	
	try:
		logger.info("🔍 BREADCRUMB 2: Attempting to get MongoDB collection")
		collection = get_mongodb_collection()
		logger.info("✓ BREADCRUMB 2: MongoDB collection retrieved successfully")
		
		logger.info("🔍 BREADCRUMB 3: Executing query for non-reserved scooters")
		query = {"is_reserved": False}
		projection = {"_id": 0}
		logger.debug(f"Query: {query}, Projection: {projection}")
		
		# Query for all non-reserved scooters
		available_scooters = list(collection.find(query, projection))
		logger.info(f"✓ BREADCRUMB 3: Query executed successfully")
		
		logger.info(f"🔍 BREADCRUMB 4: Processing results - Found {len(available_scooters)} available scooters")
		
		# Log summary of scooters for debugging
		if available_scooters:
			scooter_ids = [s.get('id', 'unknown') for s in available_scooters]
			logger.debug(f"Available scooter IDs: {scooter_ids}")
		else:
			logger.warning("⚠️ No available scooters found in database")
		
		logger.info(f"✓ BREADCRUMB 5: Returning {len(available_scooters)} available scooters to client")
		return json.dumps(available_scooters), HTTPStatus.OK.value, {'Content-Type':'application/json'}
		
	except mongo_errors.ConnectionFailure as e:
		logger.error(f"❌ BREADCRUMB ERROR (MongoDB Connection): Failed to connect to MongoDB: {e}")
		logger.error(f"Error type: {type(e).__name__}, Details: {str(e)}")
		error = { 'msg': 'Error 500 - Database connection error', 'error_type': 'connection_failure' }
		return json.dumps(error), HTTPStatus.INTERNAL_SERVER_ERROR.value, {'Content-Type':'application/json'}
		
	except mongo_errors.PyMongoError as e:
		logger.error(f"❌ BREADCRUMB ERROR (MongoDB): Error retrieving available scooters: {e}")
		logger.error(f"Error type: {type(e).__name__}, Details: {str(e)}")
		error = { 'msg': 'Error 500 - Database error', 'error_type': 'database_error' }
		return json.dumps(error), HTTPStatus.INTERNAL_SERVER_ERROR.value, {'Content-Type':'application/json'}
		
	except json.JSONDecodeError as e:
		logger.error(f"❌ BREADCRUMB ERROR (JSON): Failed to serialize response: {e}")
		logger.error(f"Error at line {e.lineno}, column {e.colno}")
		error = { 'msg': 'Error 500 - Response serialization error', 'error_type': 'json_error' }
		return json.dumps(error), HTTPStatus.INTERNAL_SERVER_ERROR.value, {'Content-Type':'application/json'}
		
	except Exception as e:
		logger.error(f"❌ BREADCRUMB ERROR (Unexpected): Failed to retrieve available scooters: {e}")
		logger.error(f"Error type: {type(e).__name__}, Details: {str(e)}", exc_info=True)
		error = { 'msg': 'Error 500 - Unexpected error occurred', 'error_type': 'unexpected_error' }
		return json.dumps(error), HTTPStatus.INTERNAL_SERVER_ERROR.value, {'Content-Type':'application/json'}


# Search for scooters
@app.route('/search', methods=['GET'])
def search():
	# Search for scooters in the database
	logger.info(f"Request received: GET /search - params: {dict(request.args)}")
	
	# Check for required parameters
	if 'lat' not in request.args or 'lng' not in request.args or 'radius' not in request.args:
		logger.warning("Search failed: Missing required parameters")
		error = { 'msg': 'Error 422 - Please include all required parameters (lat, lng, radius) in search query' }
		return json.dumps(error), HTTPStatus.UNPROCESSABLE_ENTITY.value, {'Content-Type':'application/json'}
	
	# Validate coordinates
	valid, result = validate_coordinates(request.args['lat'], request.args['lng'])
	if not valid:
		logger.warning(f"Search failed: {result}")
		error = { 'msg': f'Error 422 - {result}' }
		return json.dumps(error), HTTPStatus.UNPROCESSABLE_ENTITY.value, {'Content-Type':'application/json'}
	
	search_lat, search_lng = result
	
	# Validate radius
	valid, result = validate_radius(request.args['radius'])
	if not valid:
		logger.warning(f"Search failed: {result}")
		error = { 'msg': f'Error 422 - {result}' }
		return json.dumps(error), HTTPStatus.UNPROCESSABLE_ENTITY.value, {'Content-Type':'application/json'}
	
	search_radius = result
	logger.info(f"Search parameters validated - lat: {search_lat}, lng: {search_lng}, radius: {search_radius}m")
	
	try:
		collection = get_mongodb_collection()
		# Query for all non-reserved scooters
		all_scooters = collection.find(
			{"is_reserved": False},
			{"_id": 0}
		)
	except mongo_errors.PyMongoError as e:
		logger.error(f"MongoDB error during search: {e}")
		error = { 'msg': 'Error 500 - Database error' }
		return json.dumps(error), HTTPStatus.INTERNAL_SERVER_ERROR.value, {'Content-Type':'application/json'}
	except Exception as e:
		logger.error(f"Failed to query database: {e}")
		error = { 'msg': 'Error 500 - Database error' }
		return json.dumps(error), HTTPStatus.INTERNAL_SERVER_ERROR.value, {'Content-Type':'application/json'}

	search_results = []
	for scooter in all_scooters:
		try:
			# Calculate distance between the scooter location point and the search location point, in metres
			distance = geodesic((scooter['lat'], scooter['lng']), (search_lat, search_lng)).m
			if distance <= search_radius:
				# this scooter is available and within the search area
				search_results.append({	'id': scooter['id'], 
										'lat': scooter['lat'], 
										'lng': scooter['lng']
									  })
		except Exception as e:
			logger.warning(f"Error calculating distance for scooter {scooter.get('id', 'unknown')}: {e}")
			continue
	
	logger.info(f"Search completed: Found {len(search_results)} scooters within {search_radius}m radius")
	return json.dumps(search_results), HTTPStatus.OK.value, {'Content-Type':'application/json'}

	
# Start a reservation 
@app.route('/reservation/start', methods=['GET'])
def start_reservation():
	logger.info(f"Request received: GET /reservation/start - params: {dict(request.args)}")
	
	# Check for required parameter
	if 'id' not in request.args:
		logger.warning("Reservation start failed: Missing required parameter 'id'")
		error = { 'msg': 'Error 422 - Please include required parameter: id' }
		return json.dumps(error), HTTPStatus.UNPROCESSABLE_ENTITY.value, {'Content-Type':'application/json'}
	
	# Validate scooter ID
	valid, result = validate_scooter_id(request.args['id'])
	if not valid:
		logger.warning(f"Reservation start failed: {result}")
		error = { 'msg': f'Error 422 - {result}' }
		return json.dumps(error), HTTPStatus.UNPROCESSABLE_ENTITY.value, {'Content-Type':'application/json'}
	
	reserve_id = result
	logger.info(f"Attempting to reserve scooter: {reserve_id}")
	
	try:
		collection = get_mongodb_collection()
		
		# Try to atomically update the scooter if it's not reserved
		result = collection.update_one(
			{"id": reserve_id, "is_reserved": False},  # Only update if not already reserved
			{"$set": {"is_reserved": True}}
		)
		
		if result.matched_count == 0:
			# Either scooter doesn't exist or is already reserved
			scooter = collection.find_one({"id": reserve_id}, {"_id": 0})
			if scooter is None:
				# Scooter doesn't exist
				logger.warning(f"Reservation failed: Scooter {reserve_id} not found")
				error = { 'msg': f'Error 422 - No scooter with id {reserve_id} was found.' }
				return json.dumps(error), HTTPStatus.UNPROCESSABLE_ENTITY.value, {'Content-Type':'application/json'}
			else:
				# Scooter is already reserved
				logger.warning(f"Reservation failed: Scooter {reserve_id} is already reserved")
				error = { 'msg': f'Error 422 - Scooter with id {reserve_id} is already reserved.' }
				return json.dumps(error), HTTPStatus.UNPROCESSABLE_ENTITY.value, {'Content-Type':'application/json'}
		
		# Success
		logger.info(f"Scooter {reserve_id} reserved successfully")
		success = { 'msg': f'Scooter {reserve_id} was reserved successfully.' }
		return json.dumps(success), HTTPStatus.OK.value, {'Content-Type':'application/json'}
		
	except mongo_errors.PyMongoError as e:
		logger.error(f"MongoDB error during reservation: {e}")
		error = { 'msg': 'Error 500 - Database error' }
		return json.dumps(error), HTTPStatus.INTERNAL_SERVER_ERROR.value, {'Content-Type':'application/json'}
	except Exception as e:
		logger.error(f"Failed to save reservation: {e}")
		error = { 'msg': 'Error 500 - Failed to save reservation' }
		return json.dumps(error), HTTPStatus.INTERNAL_SERVER_ERROR.value, {'Content-Type':'application/json'}


# End a reservation
@app.route('/reservation/end', methods=['GET'])
def end_reservation():
	logger.info(f"Request received: GET /reservation/end - params: {dict(request.args)}")
	
	# Check for required parameters
	if 'id' not in request.args or 'lat' not in request.args or 'lng' not in request.args:
		logger.warning("Reservation end failed: Missing required parameters")
		error = { 'msg': 'Error 422 - Please include all required parameters (id, lat, lng)' }
		return json.dumps(error), HTTPStatus.UNPROCESSABLE_ENTITY.value, {'Content-Type':'application/json'}
	
	# Validate scooter ID
	valid, result = validate_scooter_id(request.args['id'])
	if not valid:
		logger.warning(f"Reservation end failed: {result}")
		error = { 'msg': f'Error 422 - {result}' }
		return json.dumps(error), HTTPStatus.UNPROCESSABLE_ENTITY.value, {'Content-Type':'application/json'}
	
	scooter_id_to_end = result
	
	# Validate coordinates
	valid, result = validate_coordinates(request.args['lat'], request.args['lng'])
	if not valid:
		logger.warning(f"Reservation end failed: {result}")
		error = { 'msg': f'Error 422 - {result}' }
		return json.dumps(error), HTTPStatus.UNPROCESSABLE_ENTITY.value, {'Content-Type':'application/json'}
	
	end_lat, end_lng = result
	logger.info(f"Ending reservation for scooter {scooter_id_to_end} at location ({end_lat}, {end_lng})")
	
	try:
		collection = get_mongodb_collection()
		
		# Find the scooter
		scooter = collection.find_one({"id": scooter_id_to_end}, {"_id": 0})
		
		if scooter is None:
			# Scooter doesn't exist
			logger.warning(f"Reservation end failed: Scooter {scooter_id_to_end} not found")
			error = { 'msg': f'Error 422 - No scooter with id {scooter_id_to_end} was found.' }
			return json.dumps(error), HTTPStatus.UNPROCESSABLE_ENTITY.value, {'Content-Type':'application/json'}
		
		if not scooter.get('is_reserved', False):
			# Scooter is not currently reserved
			logger.warning(f"Reservation end failed: Scooter {scooter_id_to_end} is not currently reserved")
			error = { 'msg': f'Error 422 - No reservation for scooter {scooter_id_to_end} presently exists.' }
			return json.dumps(error), HTTPStatus.UNPROCESSABLE_ENTITY.value, {'Content-Type':'application/json'}
		
		# Process payment
		logger.info(f"Processing payment for scooter {scooter_id_to_end}")
		
		try:
			# initiate payment
			payment_response = pay(scooter, end_lat, end_lng)
			if payment_response['status']:
				# the payment was completed successfully
				logger.info(f"Payment successful for scooter {scooter_id_to_end}, txn_id: {payment_response['txn_id']}")
				
				# Update scooter's reserved status and location atomically
				update_result = collection.update_one(
					{"id": scooter_id_to_end, "is_reserved": True},  # Only update if still reserved
					{"$set": {
						"is_reserved": False,
						"lat": end_lat,
						"lng": end_lng
					}}
				)
				
				if update_result.modified_count > 0:
					logger.info(f"Reservation ended successfully for scooter {scooter_id_to_end}")
					# construct successful response
					success = {	
						'msg': f'Payment for scooter {scooter_id_to_end} was made successfully and the reservation was ended.',
						'txn_id': payment_response['txn_id']
					}
					return json.dumps(success), HTTPStatus.OK.value, {'Content-Type':'application/json'}
				else:
					logger.error(f"Failed to update scooter {scooter_id_to_end} after payment")
					error = { 'msg': 'Error 500 - Failed to save reservation end' }
					return json.dumps(error), HTTPStatus.INTERNAL_SERVER_ERROR.value, {'Content-Type':'application/json'}
			else:
				# the payment failed for some reason
				logger.error(f"Payment failed for scooter {scooter_id_to_end}: {payment_response.get('msg', 'Unknown error')}")
				error = { 'msg': payment_response.get('msg', 'Payment failed') }
				response_code = payment_response.get('code', HTTPStatus.INTERNAL_SERVER_ERROR.value)
				return json.dumps(error), response_code, {'Content-Type':'application/json'}
		except Exception as e:
			logger.error(f"Error during payment processing: {e}", exc_info=True)
			error = { 'msg': 'Error 500 - Payment processing error' }
			return json.dumps(error), HTTPStatus.INTERNAL_SERVER_ERROR.value, {'Content-Type':'application/json'}
			
	except mongo_errors.PyMongoError as e:
		logger.error(f"MongoDB error during reservation end: {e}")
		error = { 'msg': 'Error 500 - Database error' }
		return json.dumps(error), HTTPStatus.INTERNAL_SERVER_ERROR.value, {'Content-Type':'application/json'}
	except Exception as e:
		logger.error(f"Failed to end reservation: {e}")
		error = { 'msg': 'Error 500 - Database error' }
		return json.dumps(error), HTTPStatus.INTERNAL_SERVER_ERROR.value, {'Content-Type':'application/json'}


# ==================
#  HELPER FUNCTIONS	
# ==================

# Response helper
def create_json_response(data, status_code=200):
	"""Create a consistent JSON response"""
	try:
		response_json = json.dumps(data, ensure_ascii=False)
		return response_json, status_code, {'Content-Type': 'application/json'}
	except (TypeError, ValueError) as e:
		logger.error(f"Failed to create JSON response: {e}")
		error_json = json.dumps({'msg': 'Error 500 - Failed to create response'})
		return error_json, 500, {'Content-Type': 'application/json'}

# Validation helpers
def validate_coordinates(lat, lng):
	"""Validate latitude and longitude values"""
	try:
		lat = float(lat)
		lng = float(lng)
	except (ValueError, TypeError):
		return False, "Coordinates must be valid numbers"
	
	if not (-90 <= lat <= 90):
		return False, f"Latitude must be in range [-90, 90], got {lat}"
	
	if not (-180 <= lng <= 180):
		return False, f"Longitude must be in range [-180, 180], got {lng}"
	
	return True, (lat, lng)

def validate_radius(radius):
	"""Validate search radius"""
	try:
		radius = float(radius)
	except (ValueError, TypeError):
		return False, "Radius must be a valid number"
	
	if radius <= 0:
		return False, "Radius must be greater than 0"
	
	if radius > 50000:  # 50km max
		return False, "Radius must be less than 50000 meters"
	
	return True, radius

def validate_scooter_id(scooter_id):
	"""Validate and sanitize scooter ID"""
	if not scooter_id:
		return False, "Scooter ID cannot be empty"
	
	# Convert to string and strip whitespace
	scooter_id = str(scooter_id).strip()
	
	if not scooter_id:
		return False, "Scooter ID cannot be empty or whitespace only"
	
	# Limit length to prevent abuse
	if len(scooter_id) > 100:
		return False, "Scooter ID is too long (max 100 characters)"
	
	return True, scooter_id


def pay(scooter, end_lat, end_lng):
	"""Initialise the payment process with error handling"""
	try:
		# Validate input parameters
		if not scooter:
			logger.error("Payment failed: scooter object is None")
			return {'status': False, 'msg': 'Error 500 - Invalid scooter data', 'code': 500}
		
		# Validate coordinates (scooter is now a dict from MongoDB)
		try:
			old_lat = float(scooter.get('lat') if isinstance(scooter, dict) else scooter.lat)
			old_lng = float(scooter.get('lng') if isinstance(scooter, dict) else scooter.lng)
			new_lat, new_lng = float(end_lat), float(end_lng)
			scooter_id = scooter.get('id') if isinstance(scooter, dict) else scooter.id
		except (ValueError, TypeError, AttributeError, KeyError) as e:
			logger.error(f"Payment failed: Invalid coordinates - {e}")
			return {'status': False, 'msg': 'Error 500 - Invalid location data', 'code': 500}
		
		# construct location point tuples
		old_location = (old_lat, old_lng)
		new_location = (new_lat, new_lng)
		
		# calculate distance between points, in metres
		try:
			distance_ridden = geodesic(old_location, new_location).m
		except Exception as e:
			logger.error(f"Distance calculation failed: {e}")
			return {'status': False, 'msg': 'Error 500 - Distance calculation error', 'code': 500}
		
		# Validate distance is reasonable
		if distance_ridden < 0:
			logger.warning(f"Negative distance calculated: {distance_ridden}m")
			distance_ridden = 0
		
		if distance_ridden > 100000:  # More than 100km seems suspicious
			logger.warning(f"Suspiciously large distance: {distance_ridden}m")
		
		distance_ridden = round(distance_ridden)
		logger.info(f"Distance calculation - Scooter {scooter_id}: {distance_ridden}m traveled")
		
		# calculate cost (currently a dummy function that returns the distance as the cost)
		try:
			cost = calculate_cost(distance_ridden)
			if cost < 0:
				logger.warning(f"Negative cost calculated: ${cost}")
				cost = 0
		except Exception as e:
			logger.error(f"Cost calculation failed: {e}")
			return {'status': False, 'msg': 'Error 500 - Cost calculation error', 'code': 500}
		
		logger.info(f"Cost calculation - Scooter {scooter_id}: ${cost}")
		
		# redirect to payment gateway and return response
		try:
			return payment_gateway(cost)
		except Exception as e:
			logger.error(f"Payment gateway error: {e}")
			return {'status': False, 'msg': 'Error 500 - Payment gateway error', 'code': 500}
			
	except Exception as e:
		logger.error(f"Unexpected error in payment processing: {e}", exc_info=True)
		return {'status': False, 'msg': 'Error 500 - Payment processing failed', 'code': 500}
	
def payment_gateway(cost):
	# TODO: Implement real payment processing in future
	txn_id = 379892831
	return 	{	'status': True,
				'txn_id': txn_id
			}

def calculate_cost(distance):
	# TODO: Implement meaningful cost calculation in future
	return distance


# ==================================================================================
# LEGACY CODE - File-based Database Functions (Deprecated, kept for migration only)
# ==================================================================================
# These functions are no longer used by the API but are kept for:
# - Data migration from JSON to MongoDB
# - Emergency fallback scenarios
# - Reference purposes
# Do not use these in new code - use MongoDB functions instead
# ==================================================================================

def init_db():
	"""Load database with comprehensive error handling and validation"""
	logger.debug(f"Loading database from {DB_FILE}")
	
	try:
		# Check if database file exists
		if not os.path.exists(DB_FILE):
			logger.error(f"Database file {DB_FILE} not found")
			raise FileNotFoundError(f"Database file {DB_FILE} does not exist")
		
		# Check if file is readable
		if not os.access(DB_FILE, os.R_OK):
			logger.error(f"Database file {DB_FILE} is not readable")
			raise PermissionError(f"Cannot read database file {DB_FILE}")
		
		# Read database file with context manager
		with open(DB_FILE, 'r', encoding='utf-8') as f:
			db_json = f.read()
		
		# Check for empty file
		if not db_json.strip():
			logger.warning(f"Database file {DB_FILE} is empty, initializing empty database")
			return []
		
		# Parse JSON with error handling
		try:
			db_list = json.loads(db_json)
		except json.JSONDecodeError as e:
			logger.error(f"Invalid JSON in database file: {e}")
			raise ValueError(f"Database file contains invalid JSON: {e}")
		
		# Validate that db_list is a list
		if not isinstance(db_list, list):
			logger.error(f"Database root must be a list, got {type(db_list)}")
			raise ValueError("Database must contain a JSON array")
		
		# populate Scooter objects with validation
		db = []
		for idx, scooter in enumerate(db_list):
			try:
				# Validate required fields
				if not isinstance(scooter, dict):
					logger.warning(f"Skipping invalid scooter at index {idx}: not a dictionary")
					continue
				
				required_fields = ['id', 'lat', 'lng', 'is_reserved']
				missing_fields = [field for field in required_fields if field not in scooter]
				if missing_fields:
					logger.warning(f"Skipping scooter at index {idx}: missing fields {missing_fields}")
					continue
				
				# Validate data types and ranges
				scooter_id = str(scooter['id'])  # Ensure ID is string
				
				try:
					lat = float(scooter['lat'])
					lng = float(scooter['lng'])
				except (ValueError, TypeError) as e:
					logger.warning(f"Skipping scooter {scooter.get('id')}: invalid coordinates - {e}")
					continue
				
				# Validate coordinate ranges
				if not (-90 <= lat <= 90):
					logger.warning(f"Skipping scooter {scooter_id}: invalid latitude {lat}")
					continue
				if not (-180 <= lng <= 180):
					logger.warning(f"Skipping scooter {scooter_id}: invalid longitude {lng}")
					continue
				
				# Validate is_reserved is boolean
				is_reserved = bool(scooter['is_reserved'])
				
				scooter_obj = Scooter(scooter_id, lat, lng, is_reserved)
				db.append(scooter_obj)
				
			except Exception as e:
				logger.warning(f"Skipping scooter at index {idx} due to error: {e}")
				continue
		
		logger.debug(f"Database loaded: {len(db)} valid scooters from {len(db_list)} entries")
		return db
		
	except FileNotFoundError:
		logger.error(f"Database file {DB_FILE} not found")
		raise
	except PermissionError:
		logger.error(f"Permission denied reading {DB_FILE}")
		raise
	except Exception as e:
		logger.error(f"Unexpected error loading database: {e}", exc_info=True)
		raise
	
	
def get_scooter_with_id(search_id, db):
	try:
		scooter = next(scooter for scooter in db if scooter.id == search_id)	# get the scooter with specified id
		return scooter
	except StopIteration:
		# no scooter with the id was found
		return None
	

def write_db(db):
	"""Write database with backup and error handling"""
	logger.debug(f"Writing database to {DB_FILE}")
	
	try:
		# Ensure backup directory exists
		if not os.path.exists(DB_BACKUP_DIR):
			os.makedirs(DB_BACKUP_DIR)
			logger.info(f"Created backup directory: {DB_BACKUP_DIR}")
		
		# Create backup of existing database before writing
		if os.path.exists(DB_FILE):
			timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
			backup_file = os.path.join(DB_BACKUP_DIR, f'scooter_db_{timestamp}.json')
			try:
				shutil.copy2(DB_FILE, backup_file)
				logger.debug(f"Created backup: {backup_file}")
				
				# Keep only last 10 backups
				cleanup_old_backups()
			except Exception as e:
				logger.warning(f"Failed to create backup: {e}")
				# Continue anyway - backup failure shouldn't stop operation
		
		# Serialize Scooter objects with validation
		db_list = convert_db_to_dictlist(db)
		
		# Validate serialized data
		if not isinstance(db_list, list):
			raise ValueError("Database serialization failed: result is not a list")
		
		# Convert to JSON with pretty printing for readability
		try:
			db_json = json.dumps(db_list, indent=2, ensure_ascii=False)
		except (TypeError, ValueError) as e:
			logger.error(f"Failed to serialize database to JSON: {e}")
			raise
		
		# Write to temporary file first (atomic write pattern)
		temp_file = f"{DB_FILE}.tmp"
		try:
			with open(temp_file, 'w', encoding='utf-8') as f:
				f.write(db_json)
			
			# Verify the write by reading it back
			with open(temp_file, 'r', encoding='utf-8') as f:
				verify_json = f.read()
				json.loads(verify_json)  # Verify it's valid JSON
			
			# If verification passed, replace the original file
			if os.path.exists(DB_FILE):
				os.replace(temp_file, DB_FILE)
			else:
				os.rename(temp_file, DB_FILE)
			
			logger.debug(f"Database written successfully: {len(db)} scooters")
			return True
			
		except Exception as e:
			# Clean up temp file if it exists
			if os.path.exists(temp_file):
				try:
					os.remove(temp_file)
				except:
					pass
			raise
			
	except PermissionError as e:
		logger.error(f"Permission denied writing to {DB_FILE}: {e}")
		raise
	except Exception as e:
		logger.error(f"Unexpected error writing database: {e}", exc_info=True)
		raise

def cleanup_old_backups(max_backups=10):
	"""Keep only the most recent backups"""
	try:
		if not os.path.exists(DB_BACKUP_DIR):
			return
		
		backups = [f for f in os.listdir(DB_BACKUP_DIR) if f.startswith('scooter_db_') and f.endswith('.json')]
		backups.sort(reverse=True)  # Most recent first
		
		# Remove old backups
		for old_backup in backups[max_backups:]:
			old_path = os.path.join(DB_BACKUP_DIR, old_backup)
			try:
				os.remove(old_path)
				logger.debug(f"Removed old backup: {old_backup}")
			except Exception as e:
				logger.warning(f"Failed to remove old backup {old_backup}: {e}")
	except Exception as e:
		logger.warning(f"Error during backup cleanup: {e}")

def verify_database_integrity():
	"""Verify database file integrity and structure"""
	try:
		if not os.path.exists(DB_FILE):
			logger.error(f"Database file {DB_FILE} does not exist")
			return False, "Database file not found"
		
		# Check file size (empty or suspiciously small)
		file_size = os.path.getsize(DB_FILE)
		if file_size == 0:
			logger.error("Database file is empty")
			return False, "Database file is empty"
		
		if file_size < 10:  # Less than 10 bytes is suspicious
			logger.warning(f"Database file is suspiciously small: {file_size} bytes")
		
		# Try to load and parse
		with open(DB_FILE, 'r', encoding='utf-8') as f:
			content = f.read()
		
		try:
			data = json.loads(content)
		except json.JSONDecodeError as e:
			logger.error(f"Database contains invalid JSON: {e}")
			return False, f"Invalid JSON: {e}"
		
		# Verify it's a list
		if not isinstance(data, list):
			logger.error(f"Database root must be a list, got {type(data)}")
			return False, "Database must be a JSON array"
		
		# Count valid scooters
		valid_count = 0
		for item in data:
			if isinstance(item, dict) and all(k in item for k in ['id', 'lat', 'lng', 'is_reserved']):
				valid_count += 1
		
		logger.info(f"Database integrity check passed: {valid_count}/{len(data)} valid scooters")
		return True, f"Valid: {valid_count} scooters"
		
	except Exception as e:
		logger.error(f"Error during integrity check: {e}")
		return False, str(e)

def restore_from_backup():
	"""Attempt to restore database from most recent backup"""
	try:
		if not os.path.exists(DB_BACKUP_DIR):
			logger.error("No backup directory found")
			return False, "No backups available"
		
		backups = [f for f in os.listdir(DB_BACKUP_DIR) if f.startswith('scooter_db_') and f.endswith('.json')]
		if not backups:
			logger.error("No backup files found")
			return False, "No backup files available"
		
		# Sort to get most recent backup
		backups.sort(reverse=True)
		most_recent = backups[0]
		backup_path = os.path.join(DB_BACKUP_DIR, most_recent)
		
		logger.info(f"Attempting to restore from backup: {most_recent}")
		
		# Verify backup integrity before restoring
		try:
			with open(backup_path, 'r', encoding='utf-8') as f:
				backup_data = json.loads(f.read())
			
			if not isinstance(backup_data, list):
				raise ValueError("Backup is not a valid database format")
		except Exception as e:
			logger.error(f"Backup file is corrupted: {e}")
			return False, f"Backup corrupted: {e}"
		
		# Restore the backup
		shutil.copy2(backup_path, DB_FILE)
		logger.info(f"Successfully restored database from {most_recent}")
		return True, f"Restored from {most_recent}"
		
	except Exception as e:
		logger.error(f"Failed to restore from backup: {e}")
		return False, str(e)

def check_and_recover_database():
	"""Check database integrity and attempt recovery if needed"""
	valid, msg = verify_database_integrity()
	
	if not valid:
		logger.warning(f"Database integrity check failed: {msg}")
		logger.info("Attempting to restore from backup...")
		
		success, restore_msg = restore_from_backup()
		if success:
			logger.info(f"Database restored successfully: {restore_msg}")
			# Verify restored database
			valid, verify_msg = verify_database_integrity()
			if valid:
				return True, f"Recovered: {restore_msg}"
			else:
				return False, f"Restored database still invalid: {verify_msg}"
		else:
			logger.error(f"Failed to restore database: {restore_msg}")
			return False, f"Recovery failed: {restore_msg}"
	
	return True, "Database is valid"
		
# class scooter for internal use
class Scooter:
	def __init__(self, scooter_id, lat, lng, is_reserved):
		self.id = scooter_id
		self.lat = lat
		self.lng = lng
		self.is_reserved = is_reserved
	
	def to_dict(self):
		return {	'id':self.id, 
					'lat':self.lat, 
					'lng':self.lng, 
					'is_reserved':self.is_reserved
			   }
		
def convert_db_to_dictlist(db):
	db_list = []
	for scooter in db:
		db_list.append(scooter.to_dict())
	return db_list
		


if __name__== "__main__":
	# TODO: Turn debug flag off for production system
	logger.info("Starting Scooter API server on localhost:5000")
	
	# Initialize MongoDB connection on startup
	logger.info("Initializing MongoDB connection...")
	if init_mongodb():
		logger.info("MongoDB connection established successfully")
	else:
		logger.error("Failed to connect to MongoDB - server starting anyway")
		logger.error("MongoDB operations will fail until connection is established")
	
	app.run('localhost', 5000)