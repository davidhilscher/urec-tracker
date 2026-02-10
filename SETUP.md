# UREC Capacity Tracker - Setup Guide

Complete setup instructions for deploying the JMU UREC Live Capacity Tracker.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [AWS Infrastructure Setup](#aws-infrastructure-setup)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** (optional, for local frontend serving) - [Download](https://nodejs.org/)
- **AWS CLI** - [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **Git** - [Download](https://git-scm.com/downloads)

### AWS Account

- Active AWS account with appropriate permissions
- IAM user with permissions for:
  - DynamoDB (create/read/write tables)
  - Lambda (create/update functions)
  - API Gateway (create/configure APIs)
  - CloudWatch (logging and monitoring)
  - S3 (for frontend hosting)

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/davidhilscher/urec-tracker.git
cd urec-tracker
```

### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# backend/.env
AWS_REGION=us-east-1
DYNAMODB_TABLE=urec-capacity
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
```

**Important**: Never commit `.env` files to Git. They're already in `.gitignore`.

### 5. Run Backend Locally

```bash
# From backend/ directory
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 6. Serve Frontend Locally

```bash
# From project root
cd frontend

# Option 1: Python HTTP Server (recommended)
python -m http.server 8080

# Option 2: Node.js HTTP Server
npx http-server -p 8080

# Option 3: VS Code Live Server extension
# Just open index.html and click "Go Live"
```

Access the frontend at `http://localhost:8080`

---

## AWS Infrastructure Setup

### 1. Configure AWS CLI

```bash
aws configure

# Enter your credentials:
# AWS Access Key ID: YOUR_KEY
# AWS Secret Access Key: YOUR_SECRET
# Default region: us-east-1
# Default output format: json
```

### 2. Create DynamoDB Table

```bash
# Create table from schema
aws dynamodb create-table \
  --table-name urec-capacity \
  --attribute-definitions \
      AttributeName=PK,AttributeType=S \
      AttributeName=SK,AttributeType=S \
  --key-schema \
      AttributeName=PK,KeyType=HASH \
      AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Project,Value=UREC-Capacity-Tracker
```

Wait for table to be active:

```bash
aws dynamodb wait table-exists --table-name urec-capacity
```

### 3. Populate Initial Data

Create a file `seed_data.json`:

```json
{
  "urec-capacity": [
    {
      "PutRequest": {
        "Item": {
          "PK": {"S": "AREA#weight-room"},
          "SK": {"S": "METADATA"},
          "area_id": {"S": "weight-room"},
          "name": {"S": "Weight Room"},
          "current_count": {"N": "0"},
          "max_capacity": {"N": "100"},
          "is_open": {"BOOL": true},
          "last_updated": {"S": "2024-02-07T00:00:00.000Z"},
          "created_at": {"S": "2024-02-07T00:00:00.000Z"}
        }
      }
    },
    {
      "PutRequest": {
        "Item": {
          "PK": {"S": "AREA#cardio"},
          "SK": {"S": "METADATA"},
          "area_id": {"S": "cardio"},
          "name": {"S": "Cardio Area"},
          "current_count": {"N": "0"},
          "max_capacity": {"N": "60"},
          "is_open": {"BOOL": true},
          "last_updated": {"S": "2024-02-07T00:00:00.000Z"},
          "created_at": {"S": "2024-02-07T00:00:00.000Z"}
        }
      }
    },
    {
      "PutRequest": {
        "Item": {
          "PK": {"S": "AREA#track"},
          "SK": {"S": "METADATA"},
          "area_id": {"S": "track"},
          "name": {"S": "Indoor Track"},
          "current_count": {"N": "0"},
          "max_capacity": {"N": "50"},
          "is_open": {"BOOL": true},
          "last_updated": {"S": "2024-02-07T00:00:00.000Z"},
          "created_at": {"S": "2024-02-07T00:00:00.000Z"}
        }
      }
    },
    {
      "PutRequest": {
        "Item": {
          "PK": {"S": "AREA#pool"},
          "SK": {"S": "METADATA"},
          "area_id": {"S": "pool"},
          "name": {"S": "Swimming Pool"},
          "current_count": {"N": "0"},
          "max_capacity": {"N": "40"},
          "is_open": {"BOOL": true},
          "last_updated": {"S": "2024-02-07T00:00:00.000Z"},
          "created_at": {"S": "2024-02-07T00:00:00.000Z"}
        }
      }
    }
  ]
}
```

Load the data:

```bash
aws dynamodb batch-write-item --request-items file://seed_data.json
```

### 4. Create IAM Role for Lambda

```bash
# Create trust policy file
cat > lambda-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name urec-lambda-execution-role \
  --assume-role-policy-document file://lambda-trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name urec-lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create custom DynamoDB policy
cat > dynamodb-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/urec-capacity"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name urec-lambda-execution-role \
  --policy-name DynamoDBAccess \
  --policy-document file://dynamodb-policy.json
```

### 5. Deploy Lambda Function

```bash
# Navigate to lambda directory
cd lambda

# Create deployment package
mkdir -p package
pip install -r requirements.txt -t package/
cp capacity_updater.py package/

# Create ZIP file
cd package
zip -r ../capacity_updater.zip .
cd ..

# Create Lambda function
aws lambda create-function \
  --function-name urec-capacity-updater \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/urec-lambda-execution-role \
  --handler capacity_updater.lambda_handler \
  --zip-file fileb://capacity_updater.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables={DYNAMODB_TABLE=urec-capacity}
```

Replace `YOUR_ACCOUNT_ID` with your AWS account ID.

### 6. Set Up API Gateway

```bash
# Create REST API
aws apigateway create-rest-api \
  --name urec-capacity-api \
  --description "API for UREC capacity updates"

# Note the API ID from the response, then continue configuration
# This is simplified - consider using AWS SAM or Terraform for full setup
```

---

## Backend Deployment

### Option 1: AWS Lambda + API Gateway (Recommended)

The Lambda function is already set up in the previous section.

### Option 2: AWS ECS/Fargate

```bash
# Build Docker image
cd backend
docker build -t urec-backend .

# Push to ECR and deploy to ECS
# (Full ECS setup requires additional configuration)
```

### Option 3: Traditional Server (EC2/VPS)

```bash
# SSH into server
ssh user@your-server.com

# Clone repository
git clone https://github.com/davidhilscher/urec-tracker.git
cd urec-tracker/backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AWS_REGION=us-east-1
export DYNAMODB_TABLE=urec-capacity

# Run with systemd or supervisor
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Frontend Deployment

### Option 1: AWS S3 + CloudFront (Recommended)

```bash
# Create S3 bucket
aws s3 mb s3://urec-tracker

# Enable static website hosting
aws s3 website s3://urec-tracker \
  --index-document index.html \
  --error-document index.html

# Upload files
cd frontend
aws s3 sync . s3://urec-tracker --acl public-read

# Update API_BASE_URL in js/app.js to point to your backend
```

### Option 2: GitHub Pages

```bash
# Push to GitHub
git add .
git commit -m "Initial commit"
git push origin main

# Enable GitHub Pages in repository settings
# Set source to main branch / root directory
```

### Option 3: Netlify/Vercel

Simply connect your GitHub repository to Netlify or Vercel and deploy the `frontend/` directory.

---

## Testing

### Test Backend API

```bash
# Health check
curl http://localhost:8000/api/health

# Get all capacity
curl http://localhost:8000/api/capacity

# Get specific area
curl http://localhost:8000/api/capacity/weight-room

# Update capacity
curl -X POST http://localhost:8000/api/update \
  -H "Content-Type: application/json" \
  -d '{"area_id": "weight-room", "action": "enter"}'
```

### Test Lambda Function

```bash
aws lambda invoke \
  --function-name urec-capacity-updater \
  --payload '{"body": "{\"area_id\": \"weight-room\", \"action\": \"enter\"}"}' \
  response.json

cat response.json
```

### Test Frontend

1. Open `http://localhost:8080` in browser
2. Open browser console (F12)
3. Click "Refresh" button
4. Verify data loads correctly

---

## Troubleshooting

### Backend won't start

- Check Python version: `python --version` (should be 3.11+)
- Verify dependencies: `pip list`
- Check environment variables: `echo $DYNAMODB_TABLE`

### DynamoDB connection fails

- Verify AWS credentials: `aws sts get-caller-identity`
- Check table exists: `aws dynamodb describe-table --table-name urec-capacity`
- Verify IAM permissions

### Frontend shows no data

- Check browser console for errors
- Verify API_BASE_URL in `js/app.js`
- Check CORS settings in backend
- Test API directly with curl

### Lambda function errors

- Check CloudWatch Logs: `aws logs tail /aws/lambda/urec-tracker-updater`
- Verify IAM role permissions
- Test function in Lambda console

---

## Next Steps

After setup is complete:

1. Configure iPad apps to send events to Lambda/API Gateway
2. Set up CloudWatch dashboards for monitoring
3. Configure automatic backups for DynamoDB
4. Set up SSL certificate for custom domain
5. Implement authentication if needed

For more information, see:
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture details
- [API.md](API.md) - API documentation
- [README.md](../README.md) - Project overview
