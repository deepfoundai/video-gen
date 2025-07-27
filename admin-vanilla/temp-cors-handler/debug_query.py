#!/usr/bin/env python3
"""
Debug script to test DynamoDB query for QUEUED jobs
Run this in Lambda console or locally with proper AWS credentials
"""

import json
import boto3
from boto3.dynamodb.conditions import Attr

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
jobs_table = dynamodb.Table('Jobs-prod')

def test_queries():
    print("=== DynamoDB Query Debug ===")
    
    # Test 1: Direct scan with FilterExpression (same as job processor)
    print("\n1. Testing current job processor query:")
    try:
        response = jobs_table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'QUEUED'},
            Limit=5
        )
        items = response.get('Items', [])
        print(f"   Found {len(items)} items with current query")
        for item in items:
            print(f"   - {item.get('jobId')}: {item.get('status')} (created: {item.get('createdAt')})")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 2: Alternative query with Attr condition
    print("\n2. Testing with boto3 Attr condition:")
    try:
        response = jobs_table.scan(
            FilterExpression=Attr('status').eq('QUEUED'),
            Limit=5
        )
        items = response.get('Items', [])
        print(f"   Found {len(items)} items with Attr query")
        for item in items:
            print(f"   - {item.get('jobId')}: {item.get('status')}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 3: Check all recent jobs regardless of status
    print("\n3. Testing all recent jobs (any status):")
    try:
        response = jobs_table.scan(
            FilterExpression='begins_with(createdAt, :today)',
            ExpressionAttributeValues={':today': '2025-07-25'},
            Limit=10
        )
        items = response.get('Items', [])
        print(f"   Found {len(items)} items from today")
        for item in items:
            print(f"   - {item.get('jobId')}: status='{item.get('status')}' tier='{item.get('tier')}' feature='{item.get('feature')}'")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 4: Check specific job by ID
    print("\n4. Testing specific job lookup:")
    try:
        response = jobs_table.get_item(
            Key={'jobId': '361e0495-00d1-411f-adb7-e3e112854381'}
        )
        if 'Item' in response:
            item = response['Item']
            print(f"   Specific job: {item.get('jobId')}")
            print(f"   Status: '{item.get('status')}' (type: {type(item.get('status'))})")
            print(f"   Tier: '{item.get('tier')}'")
            print(f"   Feature: '{item.get('feature')}'")
            print(f"   Created: {item.get('createdAt')}")
        else:
            print("   Job not found")
    except Exception as e:
        print(f"   ERROR: {e}")

    # Test 5: Check table metadata
    print("\n5. Table information:")
    try:
        table_info = jobs_table.meta.client.describe_table(TableName='Jobs-prod')
        print(f"   Table status: {table_info['Table']['TableStatus']}")
        print(f"   Item count: {table_info['Table']['ItemCount']}")
        
        gsi = table_info['Table'].get('GlobalSecondaryIndexes', [])
        print(f"   GSI count: {len(gsi)}")
        for index in gsi:
            print(f"   - {index['IndexName']}: {index['KeySchema']}")
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    test_queries()