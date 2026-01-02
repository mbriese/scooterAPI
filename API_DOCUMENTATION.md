# Scooter API Documentation

## Quick Start

### Base URL
```
http://localhost:5000
```

### Authentication
The API uses session-based authentication. Login first, then include cookies in subsequent requests.

---

## Command-Line Testing (PowerShell / curl)

### Setup
```powershell
# Start the server (if not running)
cd C:\Users\mindi\tekInnov8rs\scooterAPI
.\venv\Scripts\Activate.ps1
python app.py
```

### Testing with PowerShell (Invoke-RestMethod)

```powershell
# Create a session to store cookies
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

# 1. Register a new user
Invoke-RestMethod -Uri "http://localhost:5000/auth/register" -Method POST -ContentType "application/json" -Body '{"email":"testuser@example.com","password":"test123","name":"Test User"}' -WebSession $session

# 2. Login
Invoke-RestMethod -Uri "http://localhost:5000/auth/login" -Method POST -ContentType "application/json" -Body '{"email":"testuser@example.com","password":"test123"}' -WebSession $session

# 3. View available scooters
Invoke-RestMethod -Uri "http://localhost:5000/view_all_available" -WebSession $session

# 4. Search for scooters near a location
Invoke-RestMethod -Uri "http://localhost:5000/search?lat=30.2672&lng=-97.7431&radius=5000" -WebSession $session

# 5. Get pricing info
Invoke-RestMethod -Uri "http://localhost:5000/pricing" -WebSession $session

# 6. Start a reservation (renter only)
Invoke-RestMethod -Uri "http://localhost:5000/reservation/start?id=SCO001" -Method POST -WebSession $session

# 7. End a reservation
Invoke-RestMethod -Uri "http://localhost:5000/reservation/end?id=SCO001&lat=30.2672&lng=-97.7431" -Method POST -WebSession $session

# 8. Logout
Invoke-RestMethod -Uri "http://localhost:5000/auth/logout" -Method POST -WebSession $session
```

### Testing with curl (Windows/Linux/Mac)

```bash
# Store cookies in a file for session persistence
COOKIE_FILE="cookies.txt"

# 1. Register a new user
curl -c $COOKIE_FILE -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@example.com","password":"test123","name":"Test User"}'

# 2. Login
curl -c $COOKIE_FILE -b $COOKIE_FILE -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@example.com","password":"test123"}'

# 3. View available scooters
curl -b $COOKIE_FILE http://localhost:5000/view_all_available

# 4. Search for scooters
curl -b $COOKIE_FILE "http://localhost:5000/search?lat=30.2672&lng=-97.7431&radius=5000"

# 5. Get pricing
curl http://localhost:5000/pricing

# 6. Start reservation
curl -b $COOKIE_FILE -X POST "http://localhost:5000/reservation/start?id=SCO001"

# 7. End reservation
curl -b $COOKIE_FILE -X POST "http://localhost:5000/reservation/end?id=SCO001&lat=30.27&lng=-97.74"

# 8. Logout
curl -b $COOKIE_FILE -X POST http://localhost:5000/auth/logout
```

---

## API Reference

### Authentication Endpoints

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Registration successful",
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "renter"
    }
  }
}
```

**Validation Rules:**
- Email: Valid format, unique
- Password: 6-128 characters
- Name: 1-100 characters, no HTML/scripts

---

#### POST /auth/login
Login with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "renter"
    }
  }
}
```

---

#### POST /auth/logout
Logout current user.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

#### GET /auth/me
Get current user info. *Requires authentication.*

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "renter"
    }
  }
}
```

---

### Scooter Endpoints

#### GET /view_all_available
Get all available (non-reserved) scooters.

**Response (200 OK):**
```json
{
  "success": true,
  "count": 5,
  "data": [
    {
      "id": "SCO001",
      "lat": 30.2672,
      "lng": -97.7431,
      "is_reserved": false
    }
  ]
}
```

---

#### GET /search
Search for scooters within a radius of a location.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| lat | float | Yes | Latitude (-90 to 90) |
| lng | float | Yes | Longitude (-180 to 180) |
| radius | float | Yes | Search radius in meters (max 50000) |

**Example:**
```
GET /search?lat=30.2672&lng=-97.7431&radius=5000
```

**Response (200 OK):**
```json
{
  "success": true,
  "count": 3,
  "data": [
    {
      "id": "SCO001",
      "lat": 30.2680,
      "lng": -97.7425,
      "distance": 150.5
    }
  ]
}
```

---

#### GET /pricing
Get current rental pricing information.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "pricing": {
      "unlock_fee": 1.0,
      "hourly_rate": 3.5,
      "daily_rate": 25.0,
      "weekly_rate": 99.0,
      "monthly_rate": 299.0
    },
    "summary": {
      "unlock_fee": "$1.00",
      "hourly": "$3.50/hr",
      "daily": "$25.00/day",
      "weekly": "$99.00/week",
      "monthly": "$299.00/month"
    }
  }
}
```

---

### Reservation Endpoints (Renter Only)

#### POST /reservation/start
Start a scooter reservation. *Requires renter authentication.*

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Scooter ID (alphanumeric, dashes, underscores) |

**Example:**
```
POST /reservation/start?id=SCO001
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Scooter SCO001 was reserved successfully. Unlock fee: $1.00",
  "data": {
    "rental_id": "uuid",
    "scooter_id": "SCO001",
    "start_time": "2024-01-02T15:30:00",
    "pricing": { ... }
  }
}
```

---

#### POST /reservation/end
End a scooter reservation and process payment. *Requires renter authentication.*

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Scooter ID |
| lat | float | Yes | Drop-off latitude |
| lng | float | Yes | Drop-off longitude |

**Example:**
```
POST /reservation/end?id=SCO001&lat=30.2700&lng=-97.7400
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Rental completed! Total charge: $5.50",
  "data": {
    "rental_id": "uuid",
    "scooter_id": "SCO001",
    "duration": {
      "minutes": 75,
      "hours": 1.25
    },
    "cost": {
      "unlock_fee": 1.0,
      "rental_fee": 4.5,
      "total": 5.5,
      "pricing_tier": "hourly"
    },
    "receipt": { ... }
  }
}
```

---

#### GET /rentals/active
Get current active rental. *Requires authentication.*

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "has_active_rental": true,
    "rental": {
      "id": "uuid",
      "scooter_id": "SCO001",
      "start_time": "2024-01-02T15:30:00",
      "status": "active"
    },
    "current_cost_estimate": { ... }
  }
}
```

---

#### GET /rentals/history
Get rental history for current user. *Requires authentication.*

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "rentals": [ ... ],
    "summary": {
      "total_rentals": 10,
      "total_spent": 125.50
    }
  }
}
```

---

### Profile Endpoints (Authenticated Users)

#### GET /profile
Get user profile.

#### PUT /profile/address
Update user address.

**Request Body:**
```json
{
  "street": "123 Main St",
  "city": "Austin",
  "state": "TX",
  "zip": "78701"
}
```

#### PUT /profile/payment-method
Add/update payment method.

**Request Body:**
```json
{
  "card_number": "4111111111111111",
  "expiry": "12/25",
  "cvv": "123",
  "name_on_card": "John Doe"
}
```

---

### Admin Endpoints (Admin Only)

#### GET /admin/scooters
Get all scooters with fleet statistics.

#### POST /admin/scooters
Add a new scooter.

**Request Body:**
```json
{
  "id": "SCO-NEW-001",
  "lat": 30.2672,
  "lng": -97.7431
}
```

**Validation:**
- ID: Alphanumeric, dashes, underscores only
- Coordinates: Must be within US territory

#### PUT /admin/scooters/{id}
Update scooter location.

**Request Body:**
```json
{
  "lat": 30.2700,
  "lng": -97.7400
}
```

#### PUT /admin/scooters/{id}/release
Force-release a reserved scooter.

#### DELETE /admin/scooters/{id}
Delete a scooter (must not be reserved).

#### GET /admin/users
Get all users.

#### PUT /admin/users/{id}/role
Change user role.

---

### Admin Reports (Admin Only)

#### GET /admin/reports/revenue
Get revenue summary.

#### GET /admin/reports/transactions
Get transaction log.

#### GET /admin/reports/rentals
Get rental history.

---

## Error Responses

All errors follow this format:

```json
{
  "success": false,
  "error": "Error message here"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 401 | Unauthorized - Please login |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found |
| 422 | Validation Error - Check input |
| 500 | Server Error |

---

## Input Validation

### Coordinate Rules
- Latitude: -90 to 90
- Longitude: -180 to 180
- Cannot be (0, 0) - "Null Island"
- For scooter operations: Must be within US territory

### Security
All inputs are sanitized to prevent:
- NoSQL Injection (`$where`, `$gt`, etc.)
- XSS attacks (`<script>`, `onclick=`, etc.)
- Invalid data structures

### Scooter ID Rules
- Allowed: Letters, numbers, dashes, underscores
- Max length: 100 characters
- No special characters or spaces

---

## Rate Limits

Currently no rate limits are enforced. For production, implement:
- 100 requests/minute for authenticated users
- 20 requests/minute for unauthenticated users

---

## Example: Complete Rental Flow

```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

# 1. Login
Invoke-RestMethod -Uri "http://localhost:5000/auth/login" -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"minnie@scooter.com","password":"test123"}' `
  -WebSession $session

# 2. Find nearby scooters
$scooters = Invoke-RestMethod -Uri "http://localhost:5000/search?lat=30.2672&lng=-97.7431&radius=2000" -WebSession $session
$scooters.data | Format-Table

# 3. Reserve first scooter
$scooterId = $scooters.data[0].id
$reservation = Invoke-RestMethod -Uri "http://localhost:5000/reservation/start?id=$scooterId" -Method POST -WebSession $session
Write-Host "Reserved: $($reservation.data.scooter_id)"

# 4. (Use the scooter...)

# 5. End reservation
$receipt = Invoke-RestMethod -Uri "http://localhost:5000/reservation/end?id=$scooterId&lat=30.27&lng=-97.74" -Method POST -WebSession $session
Write-Host "Total charge: $($receipt.data.cost.total)"
```

---

## Support

For issues or questions, contact the API administrator.

