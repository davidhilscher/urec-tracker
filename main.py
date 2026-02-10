"""
JMU UREC Capacity Tracker - FastAPI Backend

This backend provides REST API endpoints for:
- Retrieving current capacity data from DynamoDB
- Updating capacity data (for iPad integration)
- Health checks

Author: JMU Development Team
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
import logging

from models import (
    AreaCapacity,
    CapacityResponse,
    UpdateCapacityRequest,
    HealthResponse
)
from database import DynamoDBManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="UREC Capacity API",
    description="Real-time capacity tracking for JMU UREC facilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://www.jmu.edu",
        # Add production frontend URL here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database manager
db_manager = DynamoDBManager()


# Dependency to get database manager
def get_db_manager():
    """Dependency injection for database manager"""
    return db_manager


@app.on_event("startup")
async def startup_event():
    """Initialize resources on application startup"""
    logger.info("Starting UREC Capacity API...")
    logger.info("Connecting to DynamoDB...")
    
    # Verify DynamoDB connection
    try:
        await db_manager.verify_connection()
        logger.info("DynamoDB connection verified")
    except Exception as e:
        logger.error(f"Failed to connect to DynamoDB: {e}")
        # In production, you might want to fail fast here


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown"""
    logger.info("Shutting down UREC Capacity API...")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "JMU UREC Capacity Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: DynamoDBManager = Depends(get_db_manager)):
    """
    Health check endpoint
    
    Returns:
        HealthResponse: API and database health status
    """
    try:
        # Check database connection
        db_healthy = await db.verify_connection()
        
        return HealthResponse(
            status="healthy" if db_healthy else "degraded",
            timestamp=datetime.utcnow().isoformat(),
            database_connected=db_healthy
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            database_connected=False
        )


@app.get("/api/capacity", response_model=CapacityResponse, tags=["Capacity"])
async def get_all_capacity(db: DynamoDBManager = Depends(get_db_manager)):
    """
    Get current capacity for all UREC areas
    
    This endpoint returns real-time capacity data for all tracked areas
    in the UREC facility. Data is fetched from DynamoDB.
    
    Returns:
        CapacityResponse: Current capacity for all areas
        
    Raises:
        HTTPException: If database query fails
    """
    try:
        logger.info("Fetching capacity for all areas")
        
        # Fetch all areas from DynamoDB
        areas = await db.get_all_areas()
        
        # If no data in database, return mock data for demo
        if not areas:
            logger.warning("No capacity data found in database, using mock data")
            areas = get_mock_capacity_data()
        
        return CapacityResponse(
            timestamp=datetime.utcnow().isoformat(),
            areas=areas
        )
        
    except Exception as e:
        logger.error(f"Error fetching capacity data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch capacity data: {str(e)}"
        )


@app.get("/api/capacity/{area_id}", response_model=AreaCapacity, tags=["Capacity"])
async def get_area_capacity(
    area_id: str,
    db: DynamoDBManager = Depends(get_db_manager)
):
    """
    Get current capacity for a specific UREC area
    
    Args:
        area_id: Unique identifier for the area (e.g., 'weight-room', 'pool')
    
    Returns:
        AreaCapacity: Current capacity for the specified area
        
    Raises:
        HTTPException: If area not found or database query fails
    """
    try:
        logger.info(f"Fetching capacity for area: {area_id}")
        
        # Fetch specific area from DynamoDB
        area = await db.get_area(area_id)
        
        if not area:
            raise HTTPException(
                status_code=404,
                detail=f"Area '{area_id}' not found"
            )
        
        return area
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching area capacity: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch area capacity: {str(e)}"
        )


@app.post("/api/update", tags=["Capacity"])
async def update_capacity(
    request: UpdateCapacityRequest,
    db: DynamoDBManager = Depends(get_db_manager)
):
    """
    Update capacity for a specific area
    
    This endpoint is called by iPad apps or Lambda functions when
    students enter or exit an area. It updates the current count
    in DynamoDB.
    
    Args:
        request: Update request containing area_id and action (enter/exit)
    
    Returns:
        dict: Updated capacity information
        
    Raises:
        HTTPException: If update fails
    """
    try:
        logger.info(f"Updating capacity for {request.area_id}: {request.action}")
        
        # Validate action
        if request.action not in ["enter", "exit"]:
            raise HTTPException(
                status_code=400,
                detail="Action must be 'enter' or 'exit'"
            )
        
        # Update the capacity in DynamoDB
        updated_area = await db.update_capacity(
            area_id=request.area_id,
            action=request.action
        )
        
        if not updated_area:
            raise HTTPException(
                status_code=404,
                detail=f"Area '{request.area_id}' not found"
            )
        
        return {
            "success": True,
            "area_id": request.area_id,
            "action": request.action,
            "new_count": updated_area.current_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating capacity: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update capacity: {str(e)}"
        )


@app.post("/api/reset/{area_id}", tags=["Admin"])
async def reset_area_capacity(
    area_id: str,
    count: int = 0,
    db: DynamoDBManager = Depends(get_db_manager)
):
    """
    Reset capacity count for a specific area (admin function)
    
    Args:
        area_id: Area identifier
        count: New count value (default: 0)
    
    Returns:
        dict: Success message with new count
    """
    try:
        logger.info(f"Resetting capacity for {area_id} to {count}")
        
        # Update the count directly
        updated_area = await db.set_capacity(area_id, count)
        
        if not updated_area:
            raise HTTPException(
                status_code=404,
                detail=f"Area '{area_id}' not found"
            )
        
        return {
            "success": True,
            "area_id": area_id,
            "new_count": count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting capacity: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset capacity: {str(e)}"
        )


def get_mock_capacity_data() -> List[AreaCapacity]:
    """
    Generate mock capacity data for demonstration
    
    This is used when the database is not available or empty.
    In production, this would be replaced with actual data.
    
    Returns:
        List[AreaCapacity]: Mock capacity data
    """
    return [
        AreaCapacity(
            area_id="weight-room",
            name="Weight Room",
            current_count=45,
            max_capacity=100,
            is_open=True,
            last_updated=datetime.utcnow().isoformat()
        ),
        AreaCapacity(
            area_id="cardio",
            name="Cardio Area",
            current_count=32,
            max_capacity=60,
            is_open=True,
            last_updated=datetime.utcnow().isoformat()
        ),
        AreaCapacity(
            area_id="track",
            name="Indoor Track",
            current_count=18,
            max_capacity=50,
            is_open=True,
            last_updated=datetime.utcnow().isoformat()
        ),
        AreaCapacity(
            area_id="pool",
            name="Swimming Pool",
            current_count=12,
            max_capacity=40,
            is_open=True,
            last_updated=datetime.utcnow().isoformat()
        ),
        AreaCapacity(
            area_id="basketball",
            name="Basketball Courts",
            current_count=24,
            max_capacity=30,
            is_open=True,
            last_updated=datetime.utcnow().isoformat()
        ),
        AreaCapacity(
            area_id="climbing",
            name="Climbing Wall",
            current_count=8,
            max_capacity=15,
            is_open=True,
            last_updated=datetime.utcnow().isoformat()
        )
    ]


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 error handler"""
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 error handler"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
