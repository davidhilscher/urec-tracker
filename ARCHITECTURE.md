# System Architecture - UREC Capacity Tracker

## Overview

The UREC Capacity Tracker is a serverless, event-driven system designed to provide real-time occupancy information for different areas within JMU's University Recreation Center.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│                                                                  │
│  ┌────────────┐        ┌────────────┐        ┌────────────┐   │
│  │  Desktop   │        │   Mobile   │        │   Tablet   │   │
│  │  Browser   │        │  Browser   │        │   Browser  │   │
│  └─────┬──────┘        └─────┬──────┘        └─────┬──────┘   │
│        │                     │                      │           │
│        └─────────────────────┴──────────────────────┘           │
│                              │                                  │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                               │ HTTPS
                               │
┌──────────────────────────────┼──────────────────────────────────┐
│                         FRONTEND LAYER                           │
│                              │                                  │
│  ┌───────────────────────────▼─────────────────────────────┐   │
│  │          Static Website (S3 + CloudFront)                │   │
│  │                                                          │   │
│  │  • index.html - Main UI                                 │   │
│  │  • styles.css - JMU Branding                           │   │
│  │  • app.js - Frontend Logic                             │   │
│  │  • Auto-refresh every 30 seconds                       │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                              │                                  │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                               │ REST API Calls
                               │
┌──────────────────────────────┼──────────────────────────────────┐
│                          API LAYER                               │
│                              │                                  │
│  ┌───────────────────────────▼─────────────────────────────┐   │
│  │         FastAPI Backend (ECS/Lambda/EC2)                 │   │
│  │                                                          │   │
│  │  Endpoints:                                             │   │
│  │  • GET  /api/capacity        - All areas               │   │
│  │  • GET  /api/capacity/{id}   - Specific area           │   │
│  │  • POST /api/update          - Update capacity         │   │
│  │  • POST /api/reset/{id}      - Reset count (admin)     │   │
│  │  • GET  /api/health          - Health check            │   │
│  │                                                          │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                              │                                  │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                               │ boto3 SDK
                               │
┌──────────────────────────────┼──────────────────────────────────┐
│                       DATABASE LAYER                             │
│                              │                                  │
│  ┌───────────────────────────▼─────────────────────────────┐   │
│  │              AWS DynamoDB                                │   │
│  │                                                          │   │
│  │  Table: urec-capacity                                   │   │
│  │  PK: AREA#<area_id>                                     │   │
│  │  SK: METADATA                                           │   │
│  │                                                          │   │
│  │  Attributes:                                            │   │
│  │  • area_id (string)                                     │   │
│  │  • name (string)                                        │   │
│  │  • current_count (number) - Atomic counter             │   │
│  │  • max_capacity (number)                                │   │
│  │  • is_open (boolean)                                    │   │
│  │  • last_updated (string - ISO timestamp)               │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      EVENT PROCESSING LAYER                       │
│                                                                  │
│  ┌────────────┐         ┌──────────────┐      ┌──────────────┐ │
│  │   UREC     │  HTTPS  │  API Gateway │      │   Lambda     │ │
│  │   iPads    ├────────►│              ├─────►│   Function   │ │
│  │            │         │              │      │              │ │
│  └────────────┘         └──────────────┘      └──────┬───────┘ │
│                                                       │         │
│                                                       │ boto3   │
│                                                       │         │
│                                              ┌────────▼──────┐  │
│                                              │   DynamoDB    │  │
│                                              │   (Update)    │  │
│                                              └───────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend Layer

**Technology**: Vanilla HTML5, CSS3, JavaScript

**Hosting**: AWS S3 + CloudFront (or GitHub Pages, Netlify)

**Responsibilities**:
- Display current capacity for all UREC areas
- Auto-refresh data every 30 seconds
- Color-coded status indicators (green/yellow/red)
- Responsive design for mobile/tablet/desktop
- No authentication required

**Key Files**:
- `index.html` - Main UI structure
- `css/styles.css` - JMU branding and responsive styles
- `js/app.js` - Frontend logic, API calls, DOM manipulation

**Design Principles**:
- Lightweight (no frameworks) for fast loading
- Accessibility compliant (WCAG 2.1 AA)
- Mobile-first responsive design
- Minimal dependencies

### 2. Backend API Layer

**Technology**: Python 3.11+, FastAPI, Uvicorn

**Hosting Options**:
- **Recommended**: AWS Lambda + API Gateway (serverless)
- **Alternative**: AWS ECS Fargate (containerized)
- **Alternative**: EC2/VPS (traditional hosting)

**Responsibilities**:
- Serve REST API endpoints
- Query DynamoDB for current capacity
- Validate and process update requests
- CORS handling for cross-origin requests
- Health checks and monitoring

**Key Files**:
- `main.py` - FastAPI application and endpoints
- `models.py` - Pydantic data models
- `database.py` - DynamoDB integration

**API Endpoints**:

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| GET | `/api/capacity` | Get all areas | `CapacityResponse` |
| GET | `/api/capacity/{area_id}` | Get specific area | `AreaCapacity` |
| POST | `/api/update` | Update capacity | Status message |
| POST | `/api/reset/{area_id}` | Reset count (admin) | Status message |
| GET | `/api/health` | Health check | `HealthResponse` |

### 3. Database Layer

**Technology**: AWS DynamoDB

**Table Design**: Single-table design pattern

**Primary Key**:
- Partition Key (PK): `AREA#<area_id>`
- Sort Key (SK): `METADATA`

**Attributes**:
```json
{
  "PK": "AREA#weight-room",
  "SK": "METADATA",
  "area_id": "weight-room",
  "name": "Weight Room",
  "current_count": 45,
  "max_capacity": 100,
  "is_open": true,
  "last_updated": "2024-02-07T14:30:00.000Z",
  "created_at": "2024-01-01T00:00:00.000Z"
}
```

**Access Patterns**:
1. Get all areas: Scan with `SK = METADATA`
2. Get single area: GetItem with `PK = AREA#<area_id>`, `SK = METADATA`
3. Update capacity: UpdateItem with atomic counter on `current_count`

**Capacity Planning**:
- On-demand billing mode (scales automatically)
- Expected read/write: ~100 requests per minute during peak
- Point-in-time recovery enabled
- Encryption at rest enabled

### 4. Event Processing Layer

**Technology**: AWS Lambda, Python 3.11

**Trigger**: API Gateway HTTP POST

**Responsibilities**:
- Receive entry/exit events from iPad apps
- Validate event data
- Update DynamoDB with atomic increment/decrement
- Error handling and logging

**Event Flow**:
1. UREC staff member checks student in/out on iPad
2. iPad app sends POST request to API Gateway
3. API Gateway triggers Lambda function
4. Lambda updates DynamoDB capacity count
5. Frontend polls API and gets updated data within 30 seconds

**Lambda Configuration**:
- Runtime: Python 3.11
- Memory: 256 MB
- Timeout: 30 seconds
- Concurrency: 100 (adjustable)
- VPC: Not required (DynamoDB is accessed via public endpoint)

## Data Flow

### Read Flow (User views website)

```
User Browser
    │
    │ 1. Load website
    ▼
S3/CloudFront (Frontend)
    │
    │ 2. Load HTML/CSS/JS
    ▼
User Browser
    │
    │ 3. GET /api/capacity
    ▼
FastAPI Backend
    │
    │ 4. Query all areas
    ▼
DynamoDB
    │
    │ 5. Return area data
    ▼
FastAPI Backend
    │
    │ 6. Format response
    ▼
User Browser
    │
    │ 7. Render capacity cards
    ▼
Display to User
```

### Write Flow (Student enters/exits)

```
UREC Staff iPad
    │
    │ 1. Student scans in/out
    ▼
iPad App
    │
    │ 2. POST /update
    ▼
API Gateway
    │
    │ 3. Trigger Lambda
    ▼
Lambda Function
    │
    │ 4. Validate request
    │ 5. Update capacity
    ▼
DynamoDB
    │
    │ 6. Atomic increment/decrement
    │ 7. Return new count
    ▼
Lambda Function
    │
    │ 8. Return success
    ▼
iPad App
    │
    │ 9. Show confirmation
    ▼
UREC Staff
```

## Security Considerations

### Authentication & Authorization

**Frontend**: No authentication required (public access)

**Backend API**: 
- CORS configured to allow specific origins
- Rate limiting to prevent abuse
- Input validation on all endpoints

**iPad Integration**:
- API Gateway with API keys
- Optional: Cognito user pool for staff authentication
- IP whitelist for UREC network

### Data Security

- **Encryption in Transit**: HTTPS/TLS 1.2+
- **Encryption at Rest**: DynamoDB server-side encryption
- **No PII**: System doesn't store personal information
- **Audit Logging**: CloudWatch logs for all operations

### Network Security

- **VPC**: Not required for serverless architecture
- **Security Groups**: If using EC2, restrict to necessary ports
- **CloudFront**: DDoS protection, SSL/TLS termination

## Scalability

### Current Capacity

- **Peak Users**: 500 concurrent users
- **Peak Updates**: 100 updates/minute
- **Database**: Auto-scaling (on-demand)
- **Frontend**: CloudFront CDN (globally distributed)

### Scaling Strategy

**Horizontal Scaling**:
- Lambda: Auto-scales to 1000 concurrent executions
- DynamoDB: Auto-scales with on-demand mode
- CloudFront: Handles millions of requests

**Vertical Scaling**:
- Lambda memory: Can increase to 10 GB if needed
- Backend instances: Can use larger EC2/ECS instances

### Performance Targets

- **Frontend Load Time**: < 2 seconds
- **API Response Time**: < 200ms (p95)
- **Database Query**: < 50ms (p99)
- **End-to-end Update**: < 30 seconds (due to polling interval)

## Monitoring & Observability

### CloudWatch Metrics

- Lambda execution duration
- Lambda error rate
- DynamoDB read/write capacity
- API Gateway request count
- CloudFront cache hit ratio

### Logging

- Lambda: CloudWatch Logs
- API Gateway: Access logs
- DynamoDB: CloudTrail for data plane operations
- Frontend: Browser console errors (not centralized)

### Alerting

- Lambda error rate > 5%
- API response time > 1 second
- DynamoDB throttling
- Frontend availability < 99.9%

## Cost Estimation

### Monthly Costs (Estimated)

| Service | Usage | Cost |
|---------|-------|------|
| DynamoDB | 1M reads, 100K writes | $0.50 |
| Lambda | 1M invocations, 256MB, 100ms | $0.20 |
| API Gateway | 1M requests | $3.50 |
| S3 + CloudFront | 10GB storage, 100GB transfer | $10.00 |
| **Total** | | **~$14.20/month** |

*Actual costs may vary based on usage patterns*

## Disaster Recovery

### Backup Strategy

- **DynamoDB**: Point-in-time recovery enabled (35 days)
- **Frontend**: Version controlled in Git
- **Backend**: Container images in ECR, code in Git

### Recovery Objectives

- **RTO** (Recovery Time Objective): 1 hour
- **RPO** (Recovery Point Objective): 5 minutes

### Failure Scenarios

1. **DynamoDB failure**: Restore from backup, switch region
2. **Lambda failure**: Automatic retry, CloudWatch alarms
3. **Frontend CDN failure**: CloudFront auto-failover
4. **Backend API failure**: Auto-scaling, health checks

## Future Enhancements

### Planned Features

1. **Real-time Updates**: WebSocket support for instant updates
2. **Historical Data**: Track capacity trends over time
3. **Predictive Analytics**: ML model to predict busy times
4. **Mobile App**: Native iOS/Android applications
5. **Staff Dashboard**: Admin interface for managing areas
6. **Notifications**: SMS/email alerts for capacity thresholds

### Technical Improvements

1. **GraphQL API**: More flexible querying
2. **Multi-region**: Deploy to multiple AWS regions
3. **Caching**: Redis/ElastiCache for faster reads
4. **CI/CD Pipeline**: Automated testing and deployment
5. **Infrastructure as Code**: Terraform/CloudFormation

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [JMU Parking System](https://www.jmu.edu/parking/index.shtml) - Inspiration
