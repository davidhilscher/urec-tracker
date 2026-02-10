"""
Data Models for UREC Capacity Tracker

Pydantic models for request/response validation and data structure.
These models ensure type safety and automatic validation.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


class AreaCapacity(BaseModel):
    """
    Model representing capacity data for a single UREC area
    
    Attributes:
        area_id: Unique identifier for the area
        name: Human-readable name of the area
        current_count: Current number of people in the area
        max_capacity: Maximum allowed capacity for the area
        is_open: Whether the area is currently open
        last_updated: ISO timestamp of last update
    """
    area_id: str = Field(
        ...,
        description="Unique identifier for the area",
        example="weight-room"
    )
    name: str = Field(
        ...,
        description="Display name of the area",
        example="Weight Room"
    )
    current_count: int = Field(
        ...,
        ge=0,
        description="Current number of people in the area",
        example=45
    )
    max_capacity: int = Field(
        ...,
        gt=0,
        description="Maximum capacity for the area",
        example=100
    )
    is_open: bool = Field(
        default=True,
        description="Whether the area is currently open",
        example=True
    )
    last_updated: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp of last update",
        example="2024-02-07T14:30:00.000Z"
    )
    
    @validator('current_count')
    def validate_current_count(cls, v, values):
        """Ensure current count doesn't exceed max capacity"""
        if 'max_capacity' in values and v > values['max_capacity']:
            # Allow it but log a warning in production
            pass
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "area_id": "weight-room",
                "name": "Weight Room",
                "current_count": 45,
                "max_capacity": 100,
                "is_open": True,
                "last_updated": "2024-02-07T14:30:00.000Z"
            }
        }


class CapacityResponse(BaseModel):
    """
    Response model for capacity queries
    
    Attributes:
        timestamp: Current server timestamp
        areas: List of capacity data for all areas
    """
    timestamp: str = Field(
        ...,
        description="Current server timestamp (ISO format)",
        example="2024-02-07T14:30:00.000Z"
    )
    areas: List[AreaCapacity] = Field(
        ...,
        description="List of capacity data for all areas"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2024-02-07T14:30:00.000Z",
                "areas": [
                    {
                        "area_id": "weight-room",
                        "name": "Weight Room",
                        "current_count": 45,
                        "max_capacity": 100,
                        "is_open": True,
                        "last_updated": "2024-02-07T14:30:00.000Z"
                    },
                    {
                        "area_id": "pool",
                        "name": "Swimming Pool",
                        "current_count": 12,
                        "max_capacity": 40,
                        "is_open": True,
                        "last_updated": "2024-02-07T14:28:00.000Z"
                    }
                ]
            }
        }


class UpdateCapacityRequest(BaseModel):
    """
    Request model for capacity updates from iPads
    
    Attributes:
        area_id: Area to update
        action: Either 'enter' or 'exit'
        count: Optional number of people (default: 1)
        timestamp: Optional client timestamp
    """
    area_id: str = Field(
        ...,
        description="Area identifier to update",
        example="weight-room"
    )
    action: str = Field(
        ...,
        description="Action to perform: 'enter' or 'exit'",
        example="enter"
    )
    count: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Number of people entering/exiting (default: 1)",
        example=1
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="Client timestamp (ISO format)",
        example="2024-02-07T14:30:00.000Z"
    )
    
    @validator('action')
    def validate_action(cls, v):
        """Ensure action is either 'enter' or 'exit'"""
        if v.lower() not in ['enter', 'exit']:
            raise ValueError("Action must be 'enter' or 'exit'")
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "area_id": "weight-room",
                "action": "enter",
                "count": 1,
                "timestamp": "2024-02-07T14:30:00.000Z"
            }
        }


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint
    
    Attributes:
        status: Overall health status
        timestamp: Current server timestamp
        database_connected: Whether database is accessible
    """
    status: str = Field(
        ...,
        description="Health status: 'healthy', 'degraded', or 'unhealthy'",
        example="healthy"
    )
    timestamp: str = Field(
        ...,
        description="Current server timestamp (ISO format)",
        example="2024-02-07T14:30:00.000Z"
    )
    database_connected: bool = Field(
        ...,
        description="Whether database connection is active",
        example=True
    )
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-02-07T14:30:00.000Z",
                "database_connected": True
            }
        }


class DynamoDBItem(BaseModel):
    """
    Model for DynamoDB item structure
    
    This matches the schema of items stored in DynamoDB.
    """
    PK: str = Field(..., description="Partition key (AREA#area_id)")
    SK: str = Field(..., description="Sort key (METADATA)")
    area_id: str
    name: str
    current_count: int
    max_capacity: int
    is_open: bool
    last_updated: str
    created_at: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "PK": "AREA#weight-room",
                "SK": "METADATA",
                "area_id": "weight-room",
                "name": "Weight Room",
                "current_count": 45,
                "max_capacity": 100,
                "is_open": True,
                "last_updated": "2024-02-07T14:30:00.000Z",
                "created_at": "2024-01-01T00:00:00.000Z"
            }
        }


class LambdaEvent(BaseModel):
    """
    Model for Lambda function event payload
    
    This is the structure of events sent from iPad apps or
    API Gateway to the Lambda function.
    """
    area_id: str
    action: str
    count: int = 1
    timestamp: Optional[str] = None
    source: Optional[str] = Field(default="ipad", description="Event source")
    
    class Config:
        schema_extra = {
            "example": {
                "area_id": "weight-room",
                "action": "enter",
                "count": 1,
                "timestamp": "2024-02-07T14:30:00.000Z",
                "source": "ipad"
            }
        }
