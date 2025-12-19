# 🛴 Scooter Rental API - Quick Start

## ⚡ Super Fast Start (3 Steps)

### Option 1: Double-Click Method (Easiest)
1. Double-click `START_APP.bat` (or right-click `START_APP.ps1` → "Run with PowerShell")
2. Wait for "Running on http://localhost:5000"
3. Open browser: http://localhost:5000

### Option 2: Command Line Method
```powershell
# Start MongoDB (if not running)
net start MongoDB

# Start the application
.\venv\Scripts\python.exe app.py

# Open browser to http://localhost:5000
```

**That's it!** 🎉

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **START_PROJECT.md** | Complete setup & troubleshooting guide |
| **MONGODB_SETUP.md** | MongoDB installation & configuration |
| **MONGODB_QUICKSTART.txt** | MongoDB quick reference |
| **FRONTEND_GUIDE.md** | Web interface features & customization |
| **START_APP.bat** | Windows batch startup script |
| **START_APP.ps1** | PowerShell startup script |

---

## 🎯 What This Application Does

- **Web Interface**: Beautiful map-based UI at http://localhost:5000
- **View Scooters**: See all available scooters on an interactive map
- **Search**: Find scooters near any location
- **Reserve**: Book scooters with one click
- **Track**: Monitor reservations and payments

---

## 🛠️ Technology Stack

- **Backend**: Flask + MongoDB
- **Frontend**: HTML5 + CSS3 + JavaScript + Leaflet.js
- **Database**: MongoDB 8.2.1
- **Python**: 3.13

---

## 📍 Key URLs

| URL | Purpose |
|-----|---------|
| http://localhost:5000 | Main web interface |
| http://localhost:5000/view_all_available | API: List all scooters |
| http://localhost:5000/search?lat=0&lng=0&radius=5000 | API: Search scooters |

---

## 🔧 Common Commands

```powershell
# Start everything
.\START_APP.bat

# Or manually:
net start MongoDB
.\venv\Scripts\python.exe app.py

# View logs
Get-Content scooter_api.log -Tail 50

# Test API
curl http://localhost:5000/view_all_available

# Connect to MongoDB
& "C:\Program Files\MongoDB\Server\8.2\bin\mongosh.exe"
```

---

## ❓ Need Help?

1. **Problem starting?** → See `START_PROJECT.md`
2. **MongoDB issues?** → See `MONGODB_SETUP.md`
3. **Frontend questions?** → See `FRONTEND_GUIDE.md`
4. **Check logs:** `scooter_api.log`

---

## 🎨 Project Structure

```
scooterAPI/
├── START_APP.bat          ← Double-click this to start!
├── START_APP.ps1          ← Or this (PowerShell)
├── app.py                 ← Main Flask application
├── requirements.txt       ← Dependencies
├── scooter_api.log       ← Application logs
├── static/               ← Web interface files
│   ├── index.html
│   ├── style.css
│   └── app.js
└── venv/                 ← Python virtual environment
```

---

## ✅ Is Everything Working?

1. MongoDB running? → `Get-Service -Name MongoDB`
2. Server started? → Look for "Running on http://localhost:5000"
3. Web interface loads? → Open http://localhost:5000
4. Scooters visible? → Should see them on the map

If all YES → **You're good to go!** 🚀

---

**Quick tip:** Bookmark http://localhost:5000 for easy access!


