"""
DynamoDB Database Manager for UREC Capacity Tracker

Handles all interactions with AWS DynamoDB including:
- Reading current capacity data
- Updating capacity counts
- Managing area metadata

Uses boto3 for AWS SDK integration.
"""

import os
import boto3
from boto3.dynamodb.conditions import Key
from typing import List, Optional
from datetime import datetime
import logging

from models import AreaCapacity, DynamoDBItem

logger = logging.getLogger(__name__)


class DynamoDBManager:
    """
    Manager class for DynamoDB operations
    
    Handles all database interactions for the UREC capacity system.
    Uses single-table design with composite primary key (PK, SK).
    """
    
    def __init__(self):
        """
        Initialize DynamoDB manager
        
        Environment variables:
            AWS_REGION: AWS region (default: us-east-1)
            DYNAMODB_TABLE: Table name (default: urec-capacity)
            AWS_ACCESS_KEY_ID: AWS access key (optional if using IAM role)
            AWS_SECRET_ACCESS_KEY: AWS secret key (optional if using IAM role)
        """
        # Get configuration from environment
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.table_name = os.getenv('DYNAMODB_TABLE', 'urec-capacity')
        
        # Initialize boto3 client
        # In production, use IAM roles instead of access keys
        session_kwargs = {'region_name': self.region}
        
        # Only add credentials if explicitly provided (for local development)
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if access_key and secret_key:
            session_kwargs['aws_access_key_id'] = access_key
            session_kwargs['aws_secret_access_key'] = secret_key
            logger.info("Using explicit AWS credentials")
        else:
            logger.info("Using default AWS credentials (IAM role or environment)")
        
        # Create DynamoDB resource
        try:
            self.dynamodb = boto3.resource('dynamodb', **session_kwargs)
            self.table = self.dynamodb.Table(self.table_name)
            logger.info(f"Connected to DynamoDB table: {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to connect to DynamoDB: {e}")
            # Set to None so we can handle gracefully
            self.table = None
    
    async def verify_connection(self) -> bool:
        """
        Verify DynamoDB connection is working
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            if not self.table:
                return False
            
            # Try to describe the table (minimal operation)
            _ = self.table.table_status
            return True
        except Exception as e:
            logger.error(f"DynamoDB connection verification failed: {e}")
            return False
    
    async def get_all_areas(self) -> List[AreaCapacity]:
        """
        Get capacity data for all areas
        
        Returns:
            List[AreaCapacity]: List of all area capacity data
            
        Raises:
            Exception: If DynamoDB query fails
        """
        try:
            if not self.table:
                logger.warning("DynamoDB table not initialized")
                return []
            
            # Scan the table for all area items
            # In production, you might want to use a GSI for better performance
            response = self.table.scan(
                FilterExpression=Key('SK').eq('METADATA')
            )
            
            items = response.get('Items', [])
            
            # Convert DynamoDB items to AreaCapacity models
            areas = []
            for item in items:
                try:
                    area = AreaCapacity(
                        area_id=item['area_id'],
                        name=item['name'],
                        current_count=int(item['current_count']),
                        max_capacity=int(item['max_capacity']),
                        is_open=bool(item.get('is_open', True)),
                        last_updated=item.get('last_updated', datetime.utcnow().isoformat())
                    )
                    areas.append(area)
                except Exception as e:
                    logger.error(f"Error parsing DynamoDB item: {e}")
                    continue
            
            logger.info(f"Retrieved {len(areas)} areas from DynamoDB")
            return areas
            
        except Exception as e:
            logger.error(f"Error fetching areas from DynamoDB: {e}")
            raise
    
    async def get_area(self, area_id: str) -> Optional[AreaCapacity]:
        """
        Get capacity data for a specific area
        
        Args:
            area_id: Unique identifier for the area
        
        Returns:
            AreaCapacity: Area capacity data, or None if not found
            
        Raises:
            Exception: If DynamoDB query fails
        """
        try:
            if not self.table:
                logger.warning("DynamoDB table not initialized")
                return None
            
            # Construct primary key
            pk = f"AREA#{area_id}"
            sk = "METADATA"
            
            # Get item from DynamoDB
            response = self.table.get_item(
                Key={'PK': pk, 'SK': sk}
            )
            
            item = response.get('Item')
            
            if not item:
                logger.warning(f"Area not found: {area_id}")
                return None
            
            # Convert to AreaCapacity model
            area = AreaCapacity(
                area_id=item['area_id'],
                name=item['name'],
                current_count=int(item['current_count']),
                max_capacity=int(item['max_capacity']),
                is_open=bool(item.get('is_open', True)),
                last_updated=item.get('last_updated', datetime.utcnow().isoformat())
            )
            
            logger.info(f"Retrieved area: {area_id}")
            return area
            
        except Exception as e:
            logger.error(f"Error fetching area {area_id} from DynamoDB: {e}")
            raise
    
    async def update_capacity(
        self,
        area_id: str,
        action: str
    ) -> Optional[AreaCapacity]:
        """
        Update capacity count for an area (increment or decrement)
        
        Args:
            area_id: Area to update
            action: 'enter' to increment, 'exit' to decrement
        
        Returns:
            AreaCapacity: Updated area data, or None if area not found
            
        Raises:
            Exception: If DynamoDB update fails
        """
        try:
            if not self.table:
                logger.warning("DynamoDB table not initialized")
                return None
            
            # Construct primary key
            pk = f"AREA#{area_id}"
            sk = "METADATA"
            
            # Determine the update value
            increment = 1 if action == 'enter' else -1
            
            # Update item in DynamoDB with atomic counter
            response = self.table.update_item(
                Key={'PK': pk, 'SK': sk},
                UpdateExpression=(
                    "SET current_count = if_not_exists(current_count, :zero) + :inc, "
                    "last_updated = :timestamp"
                ),
                ExpressionAttributeValues={
                    ':inc': increment,
                    ':zero': 0,
                    ':timestamp': datetime.utcnow().isoformat()
                },
                ReturnValues='ALL_NEW'
            )
            
            item = response.get('Attributes')
            
            if not item:
                logger.warning(f"Area not found after update: {area_id}")
                return None
            
            # Ensure count doesn't go below zero
            if item['current_count'] < 0:
                # Reset to zero if negative
                await self.set_capacity(area_id, 0)
                item['current_count'] = 0
            
            # Convert to AreaCapacity model
            area = AreaCapacity(
                area_id=item['area_id'],
                name=item['name'],
                current_count=int(item['current_count']),
                max_capacity=int(item['max_capacity']),
                is_open=bool(item.get('is_open', True)),
                last_updated=item.get('last_updated', datetime.utcnow().isoformat())
            )
            
            logger.info(f"Updated capacity for {area_id}: {action} -> {area.current_count}")
            return area
            
        except Exception as e:
            logger.error(f"Error updating capacity for {area_id}: {e}")
            raise
    
    async def set_capacity(self, area_id: str, count: int) -> Optional[AreaCapacity]:
        """
        Set capacity count to a specific value (admin function)
        
        Args:
            area_id: Area to update
            count: New count value
        
        Returns:
            AreaCapacity: Updated area data, or None if area not found
            
        Raises:
            Exception: If DynamoDB update fails
        """
        try:
            if not self.table:
                logger.warning("DynamoDB table not initialized")
                return None
            
            # Construct primary key
            pk = f"AREA#{area_id}"
            sk = "METADATA"
            
            # Update item in DynamoDB
            response = self.table.update_item(
                Key={'PK': pk, 'SK': sk},
                UpdateExpression="SET current_count = :count, last_updated = :timestamp",
                ExpressionAttributeValues={
                    ':count': max(0, count),  # Ensure non-negative
                    ':timestamp': datetime.utcnow().isoformat()
                },
                ReturnValues='ALL_NEW'
            )
            
            item = response.get('Attributes')
            
            if not item:
                logger.warning(f"Area not found: {area_id}")
                return None
            
            # Convert to AreaCapacity model
            area = AreaCapacity(
                area_id=item['area_id'],
                name=item['name'],
                current_count=int(item['current_count']),
                max_capacity=int(item['max_capacity']),
                is_open=bool(item.get('is_open', True)),
                last_updated=item.get('last_updated', datetime.utcnow().isoformat())
            )
            
            logger.info(f"Set capacity for {area_id} to {count}")
            return area
            
        except Exception as e:
            logger.error(f"Error setting capacity for {area_id}: {e}")
            raise
    
    async def create_area(
        self,
        area_id: str,
        name: str,
        max_capacity: int,
        is_open: bool = True
    ) -> AreaCapacity:
        """
        Create a new area in the database
        
        Args:
            area_id: Unique identifier for the area
            name: Display name
            max_capacity: Maximum capacity
            is_open: Whether the area is open (default: True)
        
        Returns:
            AreaCapacity: Created area data
            
        Raises:
            Exception: If DynamoDB put fails
        """
        try:
            if not self.table:
                raise Exception("DynamoDB table not initialized")
            
            # Construct primary key
            pk = f"AREA#{area_id}"
            sk = "METADATA"
            
            timestamp = datetime.utcnow().isoformat()
            
            # Create item
            item = {
                'PK': pk,
                'SK': sk,
                'area_id': area_id,
                'name': name,
                'current_count': 0,
                'max_capacity': max_capacity,
                'is_open': is_open,
                'last_updated': timestamp,
                'created_at': timestamp
            }
            
            # Put item in DynamoDB
            self.table.put_item(Item=item)
            
            area = AreaCapacity(
                area_id=area_id,
                name=name,
                current_count=0,
                max_capacity=max_capacity,
                is_open=is_open,
                last_updated=timestamp
            )
            
            logger.info(f"Created area: {area_id}")
            return area
            
        except Exception as e:
            logger.error(f"Error creating area {area_id}: {e}")
            raise
