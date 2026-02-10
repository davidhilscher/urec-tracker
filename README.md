# JMU UREC Live Capacity Tracker

A real-time capacity tracking system for James Madison University's University Recreation Center (UREC), modeled after the JMU Parking availability website.

## Project Overview

**Currently in MVP stage**

This system displays live occupancy data for different areas within UREC (weight room, track, pool, etc.) to help students plan their visits and avoid overcrowding. The website is designed to be simple, accessible, and require no login or app download.

## Architecture

- **Frontend**: Vanilla HTML/CSS/JavaScript (lightweight, fast loading)
- **Backend**: Python FastAPI (REST API endpoints)
- **Database**: AWS DynamoDB (serverless, scalable)
- **Event Processing**: AWS Lambda (event-driven updates)
- **Hosting**: Can be deployed to AWS (S3 + CloudFront) or any static host

## Project Structure

```
jmu-urec-capacity/
├── frontend/               # Static website files
│   ├── index.html         # Main UI (JMU parking style)
│   ├── css/
│   │   └── styles.css     # Styling
│   └── js/
│       └── app.js         # Frontend logic
├── backend/               # FastAPI application
│   ├── main.py           # FastAPI server
│   ├── models.py         # Data models
│   ├── database.py       # DynamoDB integration
│   └── requirements.txt  # Python dependencies
├── lambda/               # AWS Lambda functions
│   ├── capacity_updater.py    # Processes iPad entry/exit events
│   └── requirements.txt       # Lambda dependencies
├── infrastructure/       # AWS configuration
│   ├── dynamodb_schema.json   # DynamoDB table schema
│   └── lambda_config.json     # Lambda configuration
├── docs/                # Documentation
│   ├── SETUP.md         # Setup instructions
│   ├── ARCHITECTURE.md  # System architecture
│   └── API.md          # API documentation
├── tests/              # Unit tests
│   └── test_api.py
├── .gitignore
└── README.md
```

## Features

- **Real-time Updates**: Live capacity data refreshed every 30 seconds
- **Multiple Areas**: Track weight room, cardio area, track, pool, courts, climbing wall
- **Color-coded Status**: Green (available), Yellow (moderate), Red (at capacity)
- **No Authentication**: Public access, no login required
- **Mobile Responsive**: Works on all devices
- **Lightweight**: Fast loading times

## Technology Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python 3.11+, FastAPI, Uvicorn
- **Database**: AWS DynamoDB
- **Serverless**: AWS Lambda, API Gateway
- **CI/CD Ready**: GitHub Actions compatible

## Data Flow

1. UREC staff uses iPads to check people in/out of areas
2. iPad app sends events to AWS Lambda via API Gateway
3. Lambda updates DynamoDB with current capacity
4. Frontend polls FastAPI backend every 30 seconds
5. Backend queries DynamoDB and returns current capacity
6. UI updates to show real-time status

## Quick Start

See [SETUP.md](docs/SETUP.md) for detailed setup instructions.

### Local Development

```bash
# 1. Install Python dependencies
cd backend
pip install -r requirements.txt

# 2. Set environment variables
export AWS_REGION=us-east-1
export DYNAMODB_TABLE=urec-capacity
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# 3. Run the backend
uvicorn main:app --reload --port 8000

# 4. Open frontend
# Open frontend/index.html in browser or serve with:
python -m http.server 8080 --directory frontend
```

## Deployment

### Frontend
- Deploy to AWS S3 + CloudFront
- Or use GitHub Pages, Netlify, Vercel

### Backend
- Deploy to AWS Lambda + API Gateway
- Or use AWS ECS/Fargate
- Or traditional EC2/VPS

## API Endpoints

- `GET /api/capacity` - Get current capacity for all areas
- `GET /api/capacity/{area}` - Get capacity for specific area
- `POST /api/update` - Update capacity (iPad integration)
- `GET /api/health` - Health check

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

MIT License - feel free to use for educational purposes

## 👥 Contact

Project Link: [https://github.com/davidhilscher/urec-tracker](https://github.com/davidhilscher/urec-tracker)

## Acknowledgments

- Inspired by [JMU Parking Availability](https://www.jmu.edu/parking/index.shtml)
- Built for JMU students
