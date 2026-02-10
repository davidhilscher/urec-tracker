#!/usr/bin/env python3
"""
Database Initialization Script for UREC Capacity Tracker

This script:
1. Creates the DynamoDB table (if it doesn't exist)
2. Seeds initial area data
3. Verifies the setup

Usage:
    python init_database.py

Environment Variables:
    AWS_REGION - AWS region (default: us-east-1)
    DYNAMODB_TABLE - Table name (default: urec-capacity)
    AWS_ACCESS_KEY_ID - AWS access key
    AWS_SECRET_ACCESS_KEY - AWS secret key
"""

import boto3
import os
import sys
from datetime import datetime
from botocore.exceptions import ClientError

# Configuration
REGION = os.getenv('AWS_REGION', 'us-east-1')
TABLE_NAME = os.getenv('DYNAMODB_TABLE', 'urec-capacity')

# Initial areas to create
INITIAL_AREAS = [
    {
        "area_id": "weight-room",
        "name": "Weight Room",
        "max_capacity": 100
    },
    {
        "area_id": "cardio",
        "name": "Cardio Area",
        "max_capacity": 60
    },
    {
        "area_id": "track",
        "name": "Indoor Track",
        "max_capacity": 50
    },
    {
        "area_id": "pool",
        "name": "Swimming Pool",
        "max_capacity": 40
    },
    {
        "area_id": "basketball",
        "name": "Basketball Courts",
        "max_capacity": 30
    },
    {
        "area_id": "racquetball",
        "name": "Racquetball Courts",
        "max_capacity": 20
    },
    {
        "area_id": "climbing",
        "name": "Climbing Wall",
        "max_capacity": 15
    },
    {
        "area_id": "group-fitness",
        "name": "Group Fitness Studio",
        "max_capacity": 40
    }
]


def create_dynamodb_table(dynamodb):
    """
    Create DynamoDB table if it doesn't exist
    
    Args:
        dynamodb: boto3 DynamoDB resource
    
    Returns:
        Table object
    """
    try:
        print(f"Checking if table '{TABLE_NAME}' exists...")
        
        # Try to get the table
        table = dynamodb.Table(TABLE_NAME)
        table.load()
        
        print(f"✓ Table '{TABLE_NAME}' already exists")
        return table
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"Table '{TABLE_NAME}' does not exist. Creating...")
            
            # Create the table
            table = dynamodb.create_table(
                TableName=TABLE_NAME,
                KeySchema=[
                    {
                        'AttributeName': 'PK',
                        'KeyType': 'HASH'  # Partition key
                    },
                    {
                        'AttributeName': 'SK',
                        'KeyType': 'RANGE'  # Sort key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'PK',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'SK',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'UREC-Capacity-Tracker'
                    },
                    {
                        'Key': 'Environment',
                        'Value': 'Development'
                    }
                ]
            )
            
            # Wait for table to be created
            print("Waiting for table to be created...")
            table.wait_until_exists()
            
            print(f"✓ Table '{TABLE_NAME}' created successfully")
            return table
        else:
            raise


def seed_areas(table):
    """
    Seed initial area data into DynamoDB
    
    Args:
        table: DynamoDB table object
    """
    print("\nSeeding initial area data...")
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    created_count = 0
    updated_count = 0
    
    for area_config in INITIAL_AREAS:
        area_id = area_config['area_id']
        pk = f"AREA#{area_id}"
        sk = "METADATA"
        
        # Check if area already exists
        try:
            response = table.get_item(Key={'PK': pk, 'SK': sk})
            
            if 'Item' in response:
                print(f"  - {area_config['name']}: Already exists (keeping current count)")
                
                # Update max_capacity if it changed
                table.update_item(
                    Key={'PK': pk, 'SK': sk},
                    UpdateExpression="SET max_capacity = :max_cap, #name = :name",
                    ExpressionAttributeNames={'#name': 'name'},
                    ExpressionAttributeValues={
                        ':max_cap': area_config['max_capacity'],
                        ':name': area_config['name']
                    }
                )
                updated_count += 1
                continue
                
        except ClientError:
            pass
        
        # Create new area
        item = {
            'PK': pk,
            'SK': sk,
            'area_id': area_id,
            'name': area_config['name'],
            'current_count': 0,
            'max_capacity': area_config['max_capacity'],
            'is_open': True,
            'last_updated': timestamp,
            'created_at': timestamp
        }
        
        table.put_item(Item=item)
        print(f"  ✓ {area_config['name']}: Created (capacity: {area_config['max_capacity']})")
        created_count += 1
    
    print(f"\n✓ Seeding complete: {created_count} created, {updated_count} updated")


def verify_setup(table):
    """
    Verify the database is set up correctly
    
    Args:
        table: DynamoDB table object
    """
    print("\nVerifying setup...")
    
    # Scan for all areas
    response = table.scan(
        FilterExpression=boto3.dynamodb.conditions.Key('SK').eq('METADATA')
    )
    
    items = response.get('Items', [])
    
    print(f"✓ Found {len(items)} areas in database:")
    for item in items:
        print(f"  - {item['name']}: {item['current_count']}/{item['max_capacity']} "
              f"({'Open' if item.get('is_open', True) else 'Closed'})")
    
    if len(items) >= len(INITIAL_AREAS):
        print("\n✅ Database setup successful!")
        return True
    else:
        print(f"\n⚠️  Warning: Expected {len(INITIAL_AREAS)} areas, found {len(items)}")
        return False


def main():
    """Main function"""
    print("=" * 60)
    print("UREC Capacity Tracker - Database Initialization")
    print("=" * 60)
    print(f"\nRegion: {REGION}")
    print(f"Table: {TABLE_NAME}")
    print()
    
    try:
        # Initialize boto3 client
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        
        # Create table if needed
        table = create_dynamodb_table(dynamodb)
        
        # Seed initial data
        seed_areas(table)
        
        # Verify setup
        success = verify_setup(table)
        
        if success:
            print("\n" + "=" * 60)
            print("✅ Database initialization complete!")
            print("=" * 60)
            print("\nYou can now:")
            print("1. Start the backend: cd backend && uvicorn main:app --reload")
            print("2. Test the API: curl http://localhost:8000/api/capacity")
            print("3. Open the frontend: open frontend/index.html")
            return 0
        else:
            print("\n⚠️  Setup completed with warnings")
            return 1
            
    except ClientError as e:
        print(f"\n❌ AWS Error: {e}")
        print("\nPlease check:")
        print("1. AWS credentials are configured")
        print("2. You have DynamoDB permissions")
        print("3. AWS_REGION is set correctly")
        return 1
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
