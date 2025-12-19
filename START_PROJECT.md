# 🚀 How to Start Your Scooter API Project

## Quick Start (If Everything is Already Set Up)

### Step 1: Make Sure MongoDB is Running
```powershell
# Check if MongoDB is running
Get-Service -Name MongoDB

# If it shows "Stopped", start it:
net start MongoDB
```

### Step 2: Activate Virtual Environment & Start the API
```powershell
# Navigate to project directory
cd C:\Users\mindi\tekInnov8rs\scooterAPI

# Start the API server
.\venv\Scripts\python.exe app.py
```

### Step 3: Open Your Browser
```
http://localhost:5000
```

**That's it!** Your Scooter Rental App is now running! 🎉

---

## First Time Setup (Complete Guide)

### Prerequisites Check

#### 1. Python Installed? ✓
You have Python 3.13 installed at: `C:\Python313\`

#### 2. MongoDB Installed? ✓
You have MongoDB 8.2.1 installed at: `C:\Program Files\MongoDB\Server\8.2\`

#### 3. Virtual Environment? ✓
Located at: `.\venv\`

### Setup Steps

#### Step 1: Start MongoDB
```powershell
# Start MongoDB service (run as Administrator if needed)
net start MongoDB

# Verify it's running
Get-Service -Name MongoDB
```

Expected output:
```
Status   Name               DisplayName
------   ----               -----------
Running  MongoDB            MongoDB Server (MongoDB)
```

#### Step 2: Install/Update Dependencies
```powershell
# Make sure you're in the project directory
cd C:\Users\mindi\tekInnov8rs\scooterAPI

# Install all required packages
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- Flask-CORS (cross-origin support)
- pymongo (MongoDB driver)
- geopy (distance calculations)
- All other dependencies

#### Step 3: Verify MongoDB Has Data
```powershell
# Check if data was migrated
.\venv\Scripts\python.exe -c "from app import get_mongodb_collection; print(f'Scooters in DB: {get_mongodb_collection().count_documents({})}')"
```

If it shows 0 scooters, run migration:
```powershell
.\venv\Scripts\python.exe migrate_to_mongodb.py
```

#### Step 4: Start the Application
```powershell
.\venv\Scripts\python.exe app.py
```

You should see:
```
2025-11-03 10:46:34 - INFO - Starting Scooter API server on localhost:5000
2025-11-03 10:46:34 - INFO - Initializing MongoDB connection...
2025-11-03 10:46:34 - INFO - MongoDB connection established successfully
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server...
 * Running on http://localhost:5000
```

#### Step 5: Open the Web Interface
Open your browser and visit:
```
http://localhost:5000
```

---

## Stopping the Project

### Stop the Flask Server
Press `Ctrl+C` in the terminal where app.py is running

### Stop MongoDB (Optional)
```powershell
net stop MongoDB
```

**Note:** You usually don't need to stop MongoDB - it can run in the background.

---

## Troubleshooting

### Problem: "MongoDB service not found"
**Solution:**
```powershell
# Check if MongoDB is installed
Test-Path "C:\Program Files\MongoDB"

# If False, install MongoDB from:
# https://www.mongodb.com/try/download/community
```

### Problem: "No module named 'flask'"
**Solution:**
```powershell
# Install dependencies
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Problem: "Port 5000 is already in use"
**Solution 1:** Stop the other process using port 5000
```powershell
# Find what's using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

**Solution 2:** Change the port in app.py (line 872):
```python
app.run('localhost', 5001)  # Use port 5001 instead
```

### Problem: "Failed to connect to MongoDB"
**Solution:**
```powershell
# Start MongoDB
net start MongoDB

# Check if it's running
Get-Service -Name MongoDB
```

### Problem: Web page loads but no scooters appear
**Solution:**
1. Check if data is in MongoDB:
   ```powershell
   & "C:\Program Files\MongoDB\Server\8.2\bin\mongosh.exe"
   # In MongoDB shell:
   use scooter_db
   db.scooters.count()
   ```

2. If count is 0, run migration:
   ```powershell
   .\venv\Scripts\python.exe migrate_to_mongodb.py
   ```

3. Check logs:
   ```powershell
   Get-Content scooter_api.log -Tail 50
   ```

---

## Daily Workflow

### Morning (Starting Work)
```powershell
# 1. Navigate to project
cd C:\Users\mindi\tekInnov8rs\scooterAPI

# 2. Check MongoDB is running
Get-Service -Name MongoDB

# 3. Start the API
.\venv\Scripts\python.exe app.py

# 4. Open browser to http://localhost:5000
```

### Evening (Done for the Day)
```powershell
# 1. Press Ctrl+C to stop Flask

# 2. (Optional) Stop MongoDB
net stop MongoDB
```

---

## Environment Variables (Optional)

If you want to use a different MongoDB server:

```powershell
# Set MongoDB connection string
$env:MONGO_URI = "mongodb://localhost:27017/"
$env:MONGO_DB_NAME = "scooter_db"

# Then start the app
.\venv\Scripts\python.exe app.py
```

For MongoDB Atlas (cloud):
```powershell
$env:MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net/"
```

---

## Useful Commands

### View Logs
```powershell
# View last 50 lines
Get-Content scooter_api.log -Tail 50

# Watch logs in real-time
Get-Content scooter_api.log -Wait -Tail 10
```

### Check API Status
```powershell
# Test if API is responding
curl http://localhost:5000/view_all_available
```

### View MongoDB Data
```powershell
# Connect to MongoDB
& "C:\Program Files\MongoDB\Server\8.2\bin\mongosh.exe"

# In MongoDB shell:
use scooter_db
db.scooters.find().pretty()
```

### Export Data
```powershell
# Export MongoDB data to JSON
.\venv\Scripts\python.exe -c "from app import export_mongodb_to_json; export_mongodb_to_json('backup.json')"
```

---

## Running in Background (Advanced)

### Option 1: Using PowerShell
```powershell
# Start in background
Start-Process -FilePath ".\venv\Scripts\python.exe" -ArgumentList "app.py" -WindowStyle Hidden

# Find and stop it later
Get-Process python | Stop-Process
```

### Option 2: Using Task Scheduler
Create a scheduled task to auto-start on boot (see Windows Task Scheduler)

---

## Development vs Production

### Development (Current Setup)
```powershell
.\venv\Scripts\python.exe app.py
```
- Debug mode
- Auto-reload on code changes
- Detailed error messages

### Production (Future)
```powershell
# Use Gunicorn (production server)
.\venv\Scripts\gunicorn.exe -w 4 -b 0.0.0.0:5000 app:app
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start MongoDB | `net start MongoDB` |
| Stop MongoDB | `net stop MongoDB` |
| Start API | `.\venv\Scripts\python.exe app.py` |
| View Logs | `Get-Content scooter_api.log -Tail 50` |
| Test API | `curl http://localhost:5000/view_all_available` |
| Open Web App | `http://localhost:5000` |

---

## File Structure

```
scooterAPI/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── migrate_to_mongodb.py       # Data migration script
├── scooter_db.json            # Original JSON data (backup)
├── scooter_api.log            # Application logs
├── static/                     # Web interface
│   ├── index.html             # Main page
│   ├── style.css              # Styling
│   └── app.js                 # JavaScript logic
├── venv/                       # Virtual environment
├── db_backups/                 # Automatic backups
├── MONGODB_SETUP.md           # MongoDB guide
├── MONGODB_QUICKSTART.txt     # Quick reference
├── FRONTEND_GUIDE.md          # Web interface guide
└── START_PROJECT.md           # This file

MongoDB Data Location:
- Database: scooter_db
- Collection: scooters
```

---

## Next Steps After Starting

1. ✅ Open `http://localhost:5000`
2. ✅ Click "View All Available" to see scooters on map
3. ✅ Try searching for scooters near a location
4. ✅ Reserve a scooter by clicking a marker
5. ✅ Test the API endpoints

---

**You're all set! Happy coding!** 🛴🚀


