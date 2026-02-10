"""
AWS Lambda Function - UREC Capacity Updater

This Lambda function processes entry/exit events from iPad apps
and updates the capacity counts in DynamoDB.

Event-driven architecture:
1. iPad app sends entry/exit event to API Gateway
2. API Gateway triggers this Lambda function
3. Lambda updates DynamoDB with atomic increment/decrement
4. Frontend polls FastAPI to get updated data

Author: JMU Development Team
"""

import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE', 'urec-capacity')
table = dynamodb.Table(table_name)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function
    
    Args:
        event: Lambda event payload from API Gateway
        context: Lambda context object
    
    Returns:
        dict: Response with statusCode and body
    
    Expected event structure:
    {
        "body": {
            "area_id": "weight-room",
            "action": "enter",  # or "exit"
            "count": 1,
            "timestamp": "2024-02-07T14:30:00.000Z"
        }
    }
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse the event body
        # Event structure depends on how API Gateway is configured
        if isinstance(event.get('body'), str):
            # If body is a JSON string, parse it
            body = json.loads(event['body'])
        else:
            # If body is already a dict, use it directly
            body = event.get('body', event)
        
        # Extract parameters
        area_id = body.get('area_id')
        action = body.get('action', 'enter').lower()
        count = body.get('count', 1)
        client_timestamp = body.get('timestamp')
        
        # Validate required parameters
        if not area_id:
            return create_error_response(400, "Missing required parameter: area_id")
        
        if action not in ['enter', 'exit']:
            return create_error_response(400, "Action must be 'enter' or 'exit'")
        
        # Validate count
        if not isinstance(count, int) or count < 1 or count > 10:
            return create_error_response(400, "Count must be an integer between 1 and 10")
        
        # Update capacity in DynamoDB
        result = update_capacity(area_id, action, count)
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',  # Configure based on your needs
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'area_id': area_id,
                'action': action,
                'count': count,
                'new_count': result['current_count'],
                'timestamp': datetime.utcnow().isoformat(),
                'client_timestamp': client_timestamp
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        return create_error_response(500, f"Internal server error: {str(e)}")


def update_capacity(area_id: str, action: str, count: int = 1) -> Dict[str, Any]:
    """
    Update capacity count in DynamoDB using atomic operations
    
    Args:
        area_id: Area identifier
        action: 'enter' to increment, 'exit' to decrement
        count: Number of people (default: 1)
    
    Returns:
        dict: Updated item attributes
    
    Raises:
        Exception: If DynamoDB update fails
    """
    try:
        # Construct primary key
        pk = f"AREA#{area_id}"
        sk = "METADATA"
        
        # Determine increment value
        increment = count if action == 'enter' else -count
        
        logger.info(f"Updating {area_id}: {action} by {count} (increment: {increment})")
        
        # Update item with atomic counter
        response = table.update_item(
            Key={
                'PK': pk,
                'SK': sk
            },
            UpdateExpression=(
                "SET current_count = if_not_exists(current_count, :zero) + :inc, "
                "last_updated = :timestamp "
                "ADD update_count :one"
            ),
            ExpressionAttributeValues={
                ':inc': increment,
                ':zero': 0,
                ':one': 1,
                ':timestamp': datetime.utcnow().isoformat()
            },
            ReturnValues='ALL_NEW'
        )
        
        updated_item = response['Attributes']
        
        # Ensure count doesn't go below zero
        if updated_item['current_count'] < 0:
            logger.warning(f"Negative count detected for {area_id}, resetting to 0")
            response = table.update_item(
                Key={'PK': pk, 'SK': sk},
                UpdateExpression="SET current_count = :zero",
                ExpressionAttributeValues={':zero': 0},
                ReturnValues='ALL_NEW'
            )
            updated_item = response['Attributes']
        
        logger.info(f"Successfully updated {area_id}: new count = {updated_item['current_count']}")
        return updated_item
        
    except Exception as e:
        logger.error(f"Error updating DynamoDB: {str(e)}", exc_info=True)
        raise


def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Create a standardized error response
    
    Args:
        status_code: HTTP status code
        message: Error message
    
    Returns:
        dict: Lambda response object
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'success': False,
            'error': message,
            'timestamp': datetime.utcnow().isoformat()
        })
    }


def get_current_capacity(area_id: str) -> Dict[str, Any]:
    """
    Get current capacity for an area (utility function)
    
    Args:
        area_id: Area identifier
    
    Returns:
        dict: Current area data
    """
    try:
        pk = f"AREA#{area_id}"
        sk = "METADATA"
        
        response = table.get_item(
            Key={'PK': pk, 'SK': sk}
        )
        
        return response.get('Item', {})
        
    except Exception as e:
        logger.error(f"Error fetching capacity: {str(e)}")
        return {}


# Lambda warmup handler
def warmup_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle CloudWatch warmup events to keep Lambda warm
    
    This prevents cold starts during peak hours.
    """
    logger.info("Lambda warmup event received")
    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'warm'})
    }
