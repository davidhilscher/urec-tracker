# API Documentation - UREC Capacity Tracker

## Base URL

```
Production:  https://api.urec-capacity.jmu.edu
Development: http://localhost:8000
```

## Authentication

Currently, the API is **publicly accessible** for read operations. Write operations (capacity updates) should be protected with API keys when deployed to production.

## Content Type

All requests and responses use JSON:
```
Content-Type: application/json
```

---

## Endpoints

### 1. Health Check

Check API and database health status.

**Endpoint**: `GET /api/health`

**Parameters**: None

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "timestamp": "2024-02-07T14:30:00.000Z",
  "database_connected": true
}
```

**Status Values**:
- `healthy` - All systems operational
- `degraded` - Some issues but functional
- `unhealthy` - Critical issues

**Example**:
```bash
curl http://localhost:8000/api/health
```

---

### 2. Get All Capacity Data

Retrieve current capacity information for all UREC areas.

**Endpoint**: `GET /api/capacity`

**Parameters**: None

**Response**: `200 OK`

```json
{
  "timestamp": "2024-02-07T14:30:00.000Z",
  "areas": [
    {
      "area_id": "weight-room",
      "name": "Weight Room",
      "current_count": 45,
      "max_capacity": 100,
      "is_open": true,
      "last_updated": "2024-02-07T14:30:00.000Z"
    },
    {
      "area_id": "cardio",
      "name": "Cardio Area",
      "current_count": 32,
      "max_capacity": 60,
      "is_open": true,
      "last_updated": "2024-02-07T14:28:00.000Z"
    },
    {
      "area_id": "pool",
      "name": "Swimming Pool",
      "current_count": 12,
      "max_capacity": 40,
      "is_open": true,
      "last_updated": "2024-02-07T14:25:00.000Z"
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/capacity
```

---

### 3. Get Specific Area Capacity

Retrieve capacity information for a single area.

**Endpoint**: `GET /api/capacity/{area_id}`

**Path Parameters**:
- `area_id` (string, required) - Area identifier

**Response**: `200 OK`

```json
{
  "area_id": "weight-room",
  "name": "Weight Room",
  "current_count": 45,
  "max_capacity": 100,
  "is_open": true,
  "last_updated": "2024-02-07T14:30:00.000Z"
}
```

**Error Response**: `404 Not Found`

```json
{
  "detail": "Area 'invalid-id' not found"
}
```

**Available Area IDs**:
- `weight-room`
- `cardio`
- `track`
- `pool`
- `basketball`
- `racquetball`
- `climbing`
- `group-fitness`

**Example**:
```bash
curl http://localhost:8000/api/capacity/weight-room
```

---

### 4. Update Capacity

Update the capacity count when students enter or exit an area.

**Endpoint**: `POST /api/update`

**Request Body**:

```json
{
  "area_id": "weight-room",
  "action": "enter",
  "count": 1,
  "timestamp": "2024-02-07T14:30:00.000Z"
}
```

**Request Fields**:
- `area_id` (string, required) - Area to update
- `action` (string, required) - Either `"enter"` or `"exit"`
- `count` (integer, optional) - Number of people (1-10, default: 1)
- `timestamp` (string, optional) - Client timestamp (ISO 8601)

**Response**: `200 OK`

```json
{
  "success": true,
  "area_id": "weight-room",
  "action": "enter",
  "new_count": 46,
  "timestamp": "2024-02-07T14:30:00.000Z"
}
```

**Error Responses**:

`400 Bad Request` - Invalid parameters
```json
{
  "detail": "Action must be 'enter' or 'exit'"
}
```

`404 Not Found` - Area doesn't exist
```json
{
  "detail": "Area 'invalid-id' not found"
}
```

`500 Internal Server Error` - Database error
```json
{
  "detail": "Failed to update capacity: [error details]"
}
```

**Examples**:

Enter one person:
```bash
curl -X POST http://localhost:8000/api/update \
  -H "Content-Type: application/json" \
  -d '{
    "area_id": "weight-room",
    "action": "enter"
  }'
```

Exit multiple people:
```bash
curl -X POST http://localhost:8000/api/update \
  -H "Content-Type: application/json" \
  -d '{
    "area_id": "pool",
    "action": "exit",
    "count": 3
  }'
```

---

### 5. Reset Area Capacity (Admin)

Reset the capacity count for an area to a specific value.

**Endpoint**: `POST /api/reset/{area_id}?count={count}`

**Path Parameters**:
- `area_id` (string, required) - Area to reset

**Query Parameters**:
- `count` (integer, optional) - New count value (default: 0)

**Response**: `200 OK`

```json
{
  "success": true,
  "area_id": "weight-room",
  "new_count": 0,
  "timestamp": "2024-02-07T14:30:00.000Z"
}
```

**Example**:

Reset to zero:
```bash
curl -X POST http://localhost:8000/api/reset/weight-room
```

Reset to specific value:
```bash
curl -X POST "http://localhost:8000/api/reset/cardio?count=25"
```

---

## Data Models

### AreaCapacity

```typescript
interface AreaCapacity {
  area_id: string;        // Unique identifier
  name: string;           // Display name
  current_count: number;  // Current occupancy (>= 0)
  max_capacity: number;   // Maximum allowed (> 0)
  is_open: boolean;       // Whether area is open
  last_updated: string;   // ISO 8601 timestamp
}
```

### CapacityResponse

```typescript
interface CapacityResponse {
  timestamp: string;       // Current server time (ISO 8601)
  areas: AreaCapacity[];   // Array of area data
}
```

### UpdateCapacityRequest

```typescript
interface UpdateCapacityRequest {
  area_id: string;                    // Required
  action: "enter" | "exit";           // Required
  count?: number;                     // Optional (1-10)
  timestamp?: string;                 // Optional (ISO 8601)
}
```

### HealthResponse

```typescript
interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;                  // ISO 8601
  database_connected: boolean;
}
```

---

## Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Area doesn't exist |
| 500 | Internal Server Error - Database or server issue |

---

## Rate Limiting

**Current Limits** (can be adjusted):
- Read operations: 100 requests per minute per IP
- Write operations: 50 requests per minute per IP

**Response Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1707318600
```

When rate limit is exceeded:
```json
{
  "detail": "Rate limit exceeded. Please try again in 30 seconds."
}
```

---

## CORS

The API supports Cross-Origin Resource Sharing (CORS) with the following configuration:

**Allowed Origins**:
- `http://localhost:8080` (development)
- `https://www.jmu.edu`
- Your production frontend URL

**Allowed Methods**: `GET, POST, OPTIONS`

**Allowed Headers**: `Content-Type, Authorization`

---

## Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Human-readable error message"
}
```

**Best Practices**:
1. Check the HTTP status code
2. Parse the error detail message
3. Display user-friendly message
4. Log technical details for debugging

---

## Integration Examples

### JavaScript (Frontend)

```javascript
// Get all capacity data
async function fetchCapacity() {
  try {
    const response = await fetch('http://localhost:8000/api/capacity');
    const data = await response.json();
    return data.areas;
  } catch (error) {
    console.error('Error fetching capacity:', error);
    return [];
  }
}

// Update capacity
async function updateCapacity(areaId, action) {
  try {
    const response = await fetch('http://localhost:8000/api/update', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        area_id: areaId,
        action: action,
        timestamp: new Date().toISOString()
      })
    });
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error updating capacity:', error);
    throw error;
  }
}
```

### Python (iPad App or Testing)

```python
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

# Get all capacity
def get_capacity():
    response = requests.get(f"{BASE_URL}/capacity")
    return response.json()

# Update capacity
def update_capacity(area_id, action):
    payload = {
        "area_id": area_id,
        "action": action,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    response = requests.post(
        f"{BASE_URL}/update",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    return response.json()

# Example usage
if __name__ == "__main__":
    # Get current capacity
    data = get_capacity()
    print(f"Found {len(data['areas'])} areas")
    
    # Student enters weight room
    result = update_capacity("weight-room", "enter")
    print(f"New count: {result['new_count']}")
```

### Swift (iOS iPad App)

```swift
import Foundation

struct CapacityUpdate: Codable {
    let areaId: String
    let action: String
    let timestamp: String
    
    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case action
        case timestamp
    }
}

class CapacityAPI {
    let baseURL = "https://api.urec-capacity.jmu.edu/api"
    
    func updateCapacity(areaId: String, action: String) async throws {
        let url = URL(string: "\(baseURL)/update")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let update = CapacityUpdate(
            areaId: areaId,
            action: action,
            timestamp: ISO8601DateFormatter().string(from: Date())
        )
        
        request.httpBody = try JSONEncoder().encode(update)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }
        
        // Success
        print("Capacity updated successfully")
    }
}
```

---

## Testing

### Swagger UI

Interactive API documentation is available at:
```
http://localhost:8000/docs
```

### ReDoc

Alternative API documentation:
```
http://localhost:8000/redoc
```

### Example Test Suite

```bash
# Health check
curl http://localhost:8000/api/health

# Get all areas
curl http://localhost:8000/api/capacity

# Get specific area
curl http://localhost:8000/api/capacity/weight-room

# Enter weight room
curl -X POST http://localhost:8000/api/update \
  -H "Content-Type: application/json" \
  -d '{"area_id": "weight-room", "action": "enter"}'

# Exit cardio area (3 people)
curl -X POST http://localhost:8000/api/update \
  -H "Content-Type: application/json" \
  -d '{"area_id": "cardio", "action": "exit", "count": 3}'

# Reset pool capacity
curl -X POST http://localhost:8000/api/reset/pool
```

---

## Webhooks (Future Feature)

*Coming soon: Webhook support for real-time capacity updates*

```json
{
  "event": "capacity_updated",
  "area_id": "weight-room",
  "new_count": 46,
  "timestamp": "2024-02-07T14:30:00.000Z"
}
```

---

## Support

For API issues or questions:
- Email: urec-tech@jmu.edu
- GitHub Issues: [Repository Issues](https://github.com/yourusername/jmu-urec-capacity/issues)
- Documentation: [Full Documentation](https://github.com/yourusername/jmu-urec-capacity)

---

## Changelog

### v1.0.0 (2024-02-07)
- Initial API release
- Basic CRUD operations for capacity
- Health check endpoint
- DynamoDB integration
