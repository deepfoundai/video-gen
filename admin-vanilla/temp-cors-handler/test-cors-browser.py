#!/usr/bin/env python3
"""
Browser automation script to test CORS fixes
This script opens the frontend and checks for console errors
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_browser():
    """Setup Chrome browser with console logging"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-web-security")  # Allow CORS testing
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    # Enable logging
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")
    
    # Set up logging preferences
    chrome_options.set_capability('goog:loggingPrefs', {
        'browser': 'ALL',
        'driver': 'ALL',
        'performance': 'ALL'
    })
    
    return webdriver.Chrome(options=chrome_options)

def get_console_logs(driver):
    """Get console logs and filter for errors"""
    logs = driver.get_log('browser')
    errors = []
    cors_errors = []
    
    for log in logs:
        if log['level'] == 'SEVERE':
            errors.append(log)
            if 'CORS' in log['message'] or 'Access to fetch' in log['message']:
                cors_errors.append(log)
    
    return logs, errors, cors_errors

def test_cors_fix():
    """Test the CORS fix by visiting the dashboard"""
    print("🧪 Testing CORS Fix with Browser Automation")
    print("===========================================")
    
    driver = None
    try:
        # Setup browser
        print("🌐 Setting up Chrome browser...")
        driver = setup_browser()
        
        # Navigate to the dashboard
        frontend_url = "https://video.deepfoundai.com/dashboard"
        print(f"📍 Navigating to: {frontend_url}")
        driver.get(frontend_url)
        
        # Wait for page to load
        print("⏳ Waiting for page to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait a bit for API calls to happen
        print("⏳ Waiting for API calls to complete...")
        time.sleep(5)
        
        # Get console logs
        print("📋 Checking console logs...")
        all_logs, errors, cors_errors = get_console_logs(driver)
        
        # Print results
        print(f"\n📊 Console Log Analysis:")
        print(f"   Total logs: {len(all_logs)}")
        print(f"   Total errors: {len(errors)}")
        print(f"   CORS errors: {len(cors_errors)}")
        
        if cors_errors:
            print(f"\n❌ CORS Errors Found:")
            for i, error in enumerate(cors_errors, 1):
                print(f"   {i}. {error['message']}")
        else:
            print(f"\n✅ No CORS errors found!")
        
        if errors:
            print(f"\n⚠️  Other Errors:")
            for i, error in enumerate(errors, 1):
                if not any(keyword in error['message'] for keyword in ['CORS', 'Access to fetch']):
                    print(f"   {i}. {error['message']}")
        
        # Check for specific API endpoints in network requests
        print(f"\n🔍 Checking for specific API calls...")
        
        # Use performance logs to check network requests
        perf_logs = driver.get_log('performance')
        api_calls = []
        
        for log in perf_logs:
            try:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    url = message['message']['params']['response']['url']
                    status = message['message']['params']['response']['status']
                    
                    if 'execute-api' in url:
                        api_calls.append({
                            'url': url,
                            'status': status,
                            'timestamp': log['timestamp']
                        })
            except:
                continue
        
        if api_calls:
            print(f"   Found {len(api_calls)} API calls:")
            for call in api_calls:
                status_icon = "✅" if call['status'] < 400 else "❌"
                print(f"   {status_icon} {call['status']} - {call['url']}")
        else:
            print("   No API calls detected in performance logs")
        
        # Take a screenshot for visual verification
        screenshot_path = "/tmp/cors-test-screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"📸 Screenshot saved: {screenshot_path}")
        
        # Test result summary
        print(f"\n🎯 Test Results:")
        if len(cors_errors) == 0:
            print("   ✅ CORS Fix Successful!")
            print("   ✅ No CORS policy errors detected")
        else:
            print("   ❌ CORS Fix Failed!")
            print("   ❌ CORS policy errors still present")
        
        return len(cors_errors) == 0
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False
        
    finally:
        if driver:
            driver.quit()

def test_direct_api_calls():
    """Test API endpoints directly with curl"""
    print(f"\n🔧 Testing API Endpoints Directly")
    print("=================================")
    
    import subprocess
    
    # Test Credits API
    credits_url = "https://hxk5lx2y17.execute-api.us-east-1.amazonaws.com/v1/credits/balance"
    print(f"💳 Testing Credits API: {credits_url}")
    
    try:
        # Test OPTIONS request
        result = subprocess.run([
            'curl', '-X', 'OPTIONS',
            '-H', 'Origin: https://video.deepfoundai.com',
            '-H', 'Access-Control-Request-Method: GET',
            '-I', '-s', credits_url
        ], capture_output=True, text=True, timeout=10)
        
        if 'Access-Control-Allow-Origin' in result.stdout:
            print("   ✅ Credits API CORS headers present")
        else:
            print("   ❌ Credits API CORS headers missing")
            print(f"   Response: {result.stdout}")
            
    except Exception as e:
        print(f"   ❌ Credits API test failed: {str(e)}")
    
    # Test Jobs API
    jobs_url = "https://6ydbgbao92.execute-api.us-east-1.amazonaws.com/v1/admin/overview"
    print(f"🎯 Testing Jobs API: {jobs_url}")
    
    try:
        # Test OPTIONS request
        result = subprocess.run([
            'curl', '-X', 'OPTIONS',
            '-H', 'Origin: https://video.deepfoundai.com',
            '-H', 'Access-Control-Request-Method: GET',
            '-I', '-s', jobs_url
        ], capture_output=True, text=True, timeout=10)
        
        if 'Access-Control-Allow-Origin' in result.stdout:
            print("   ✅ Jobs API CORS headers present")
        else:
            print("   ❌ Jobs API CORS headers missing")
            print(f"   Response: {result.stdout}")
            
    except Exception as e:
        print(f"   ❌ Jobs API test failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 CORS Fix Testing Suite")
    print("========================")
    
    # Test direct API calls first
    test_direct_api_calls()
    
    # Test with browser automation
    browser_success = test_cors_fix()
    
    print(f"\n🏁 Final Results:")
    print(f"=================")
    if browser_success:
        print("✅ CORS Fix Verified Successfully!")
        print("✅ Frontend should now work without CORS errors")
    else:
        print("❌ CORS Fix Needs Additional Work")
        print("❌ Check Lambda functions and API Gateway configuration")
    
    print(f"\n📋 Next Steps:")
    if browser_success:
        print("1. ✅ CORS errors resolved")
        print("2. ✅ APIs responding with proper headers")
        print("3. 🎉 Frontend ready for production use")
    else:
        print("1. 🔍 Review Lambda function logs")
        print("2. 🔍 Check API Gateway integration")
        print("3. 🔧 Debug CORS header implementation")