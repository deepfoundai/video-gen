#!/usr/bin/env python3
"""
Quick CORS test using Python requests to simulate browser behavior
"""

import requests
import json

def test_cors_endpoint(url, name):
    """Test a single endpoint for CORS support"""
    print(f"\n🧪 Testing {name}: {url}")
    
    # Test OPTIONS preflight request
    try:
        options_response = requests.options(
            url,
            headers={
                'Origin': 'https://video.deepfoundai.com',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'authorization,content-type'
            },
            timeout=10
        )
        
        print(f"   OPTIONS Status: {options_response.status_code}")
        print(f"   CORS Headers:")
        
        cors_headers = {}
        for header, value in options_response.headers.items():
            if 'access-control' in header.lower():
                cors_headers[header] = value
                print(f"     {header}: {value}")
        
        if 'Access-Control-Allow-Origin' in cors_headers:
            print(f"   ✅ CORS Origin header present")
        else:
            print(f"   ❌ CORS Origin header missing")
            
    except Exception as e:
        print(f"   ❌ OPTIONS request failed: {str(e)}")
    
    # Test GET request
    try:
        get_response = requests.get(
            url,
            headers={
                'Origin': 'https://video.deepfoundai.com',
                'Authorization': 'Bearer test-token',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        print(f"   GET Status: {get_response.status_code}")
        
        if get_response.status_code == 200:
            print(f"   ✅ GET request successful")
            try:
                data = get_response.json()
                print(f"   📊 Response: {str(data)[:100]}...")
            except:
                print(f"   📊 Response: {get_response.text[:100]}...")
        elif get_response.status_code in [401, 403]:
            print(f"   ✅ GET request handled (auth/permission issue as expected)")
        else:
            print(f"   ⚠️ GET request returned: {get_response.status_code}")
            print(f"   📊 Response: {get_response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ GET request failed: {str(e)}")

def main():
    print("🚀 Quick CORS Test")
    print("==================")
    print("Testing the exact URLs from the console errors...")
    
    # Test the exact URLs from the console errors
    test_cors_endpoint(
        "https://hxk5lx2y17.execute-api.us-east-1.amazonaws.com/v1/credits/balance",
        "Credits Balance API"
    )
    
    test_cors_endpoint(
        "https://6ydbgbao92.execute-api.us-east-1.amazonaws.com/v1/admin/overview", 
        "Jobs Admin Overview API"
    )
    
    print(f"\n🏁 Test Complete")
    print("================")
    print("If CORS headers are present, the frontend should work!")

if __name__ == "__main__":
    main()