# MongoDB Setup Guide for Scooter API

This guide will help you migrate your Scooter API from JSON file storage to MongoDB.

## Prerequisites

1. **Install MongoDB**
   - **Windows**: Download from [MongoDB Downloads](https://www.mongodb.com/try/download/community)
   - **Mac**: `brew install mongodb-community`
   - **Linux**: Follow [MongoDB installation guide](https://docs.mongodb.com/manual/installation/)

2. **Install pymongo** (already in requirements.txt)
   ```bash
   .\venv\Scripts\python.exe -m pip install pymongo==4.6.1
   ```

## Quick Start

### 1. Start MongoDB

**Windows:**
```bash
# Start MongoDB service
net start MongoDB
```

**Mac/Linux:**
```bash
# Start MongoDB
brew services start mongodb-community
# OR
sudo systemctl start mongod
```

### 2. Verify MongoDB is Running

```bash
# Connect to MongoDB shell
mongosh
# or
mongo

# You should see a connection prompt
# Type 'exit' to quit the shell
```

### 3. Configure Connection (Optional)

By default, the API connects to `mongodb://localhost:27017/`. To use a different MongoDB server, set environment variables:

**Windows PowerShell:**
```powershell
$env:MONGO_URI = "mongodb://localhost:27017/"
$env:MONGO_DB_NAME = "scooter_db"
```

**Windows CMD:**
```cmd
set MONGO_URI=mongodb://localhost:27017/
set MONGO_DB_NAME=scooter_db
```

**Mac/Linux:**
```bash
export MONGO_URI="mongodb://localhost:27017/"
export MONGO_DB_NAME="scooter_db"
```

**For MongoDB Atlas (Cloud):**
```powershell
$env:MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net/"
```

### 4. Migrate Existing Data

If you have existing data in `scooter_db.json`, run the migration script:

```bash
.\venv\Scripts\python.exe migrate_to_mongodb.py
```

This will:
- Connect to MongoDB
- Read your existing JSON data
- Import all scooters into MongoDB
- Preserve all scooter states

### 5. Run the API

```bash
.\venv\Scripts\python.exe app.py
```

The API will now use MongoDB instead of the JSON file!

## MongoDB Collections

Your scooter data is stored in:
- **Database**: `scooter_db` (or your custom name)
- **Collection**: `scooters`

### Document Structure

```json
{
  "id": "scooter_001",
  "lat": 40.7128,
  "lng": -74.0060,
  "is_reserved": false
}
```

### Indexes

The following indexes are automatically created for performance:
- `id` (unique)
- `is_reserved`
- `lat, lng` (compound index)

## MongoDB Operations

### View Data

```javascript
// Connect to MongoDB shell
mongosh

// Switch to database
use scooter_db

// View all scooters
db.scooters.find().pretty()

// View available scooters
db.scooters.find({is_reserved: false}).pretty()

// Count scooters
db.scooters.countDocuments()
```

### Backup Data

**Export to JSON:**
```bash
.\venv\Scripts\python.exe
>>> from app import export_mongodb_to_json
>>> export_mongodb_to_json('backup.json')
```

**Using mongodump:**
```bash
mongodump --db scooter_db --out ./mongodb_backup
```

### Restore Data

**Using mongorestore:**
```bash
mongorestore --db scooter_db ./mongodb_backup/scooter_db
```

## Benefits of MongoDB

✅ **Better Performance**: Indexed queries are much faster
✅ **Atomic Operations**: Race-condition-free reservations
✅ **Scalability**: Can handle millions of scooters
✅ **Replication**: Built-in data redundancy
✅ **Geospatial Queries**: Future support for location-based features
✅ **No File Locking**: Multiple processes can access the database

## Troubleshooting

### Connection Failed

**Error**: `Failed to connect to MongoDB: Connection timeout`

**Solutions**:
1. Make sure MongoDB is running:
   ```bash
   # Windows
   net start MongoDB
   
   # Mac/Linux
   sudo systemctl status mongod
   ```

2. Check if port 27017 is open:
   ```bash
   netstat -an | findstr 27017
   ```

3. Check firewall settings

### Authentication Error

If your MongoDB requires authentication:

```powershell
$env:MONGO_URI = "mongodb://username:password@localhost:27017/"
```

### Import Error

**Error**: `Duplicate key error`

This means scooter IDs are not unique in your JSON file. Fix the JSON data and try again.

## Advanced Configuration

### Custom Connection Options

Edit `app.py` to add more connection options:

```python
mongo_client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    maxPoolSize=50,
    retryWrites=True
)
```

### Enable MongoDB Authentication

```bash
# Start MongoDB with auth
mongod --auth
```

Create a user:
```javascript
use admin
db.createUser({
  user: "scooter_admin",
  pwd: "secure_password",
  roles: [{role: "readWrite", db: "scooter_db"}]
})
```

## Monitoring

View connection status in logs:
```
2025-11-02 10:30:15 - __main__ - INFO - Connecting to MongoDB at mongodb://localhost:27017/
2025-11-02 10:30:15 - __main__ - INFO - MongoDB connection successful
2025-11-02 10:30:15 - __main__ - INFO - MongoDB initialized: database='scooter_db', collection='scooters'
```

## Support

For MongoDB documentation: https://docs.mongodb.com/
For issues: Check scooter_api.log for detailed error messages



