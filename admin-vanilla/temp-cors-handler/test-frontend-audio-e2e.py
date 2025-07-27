#!/usr/bin/env python3
"""
End-to-end test that mimics exact frontend behavior for audio generation
"""
import asyncio
from playwright.async_api import async_playwright
import time
import boto3
import json

# Configuration
FRONTEND_URL = "https://video.deepfoundai.com"
TEST_USER = "admin.test@deepfoundai.com"
TEST_PASSWORD = "AdminTest123!"

async def run_test():
    print("🎬 Running End-to-End Audio Test")
    print("=" * 50)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set headless=True for CI
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))
        
        try:
            # Step 1: Navigate to frontend
            print("\n1️⃣ Navigating to frontend...")
            await page.goto(FRONTEND_URL)
            await page.wait_for_load_state('networkidle')
            
            # Step 2: Login
            print("\n2️⃣ Logging in...")
            await page.fill('input[type="email"]', TEST_USER)
            await page.fill('input[type="password"]', TEST_PASSWORD)
            await page.click('button:has-text("Sign In")')
            
            # Wait for login to complete
            await page.wait_for_selector('#generator-section', timeout=10000)
            print("✅ Logged in successfully")
            
            # Step 3: Fill out video generation form
            print("\n3️⃣ Filling out video generation form...")
            test_prompt = f"Test audio generation {int(time.time())}"
            
            await page.fill('#prompt', test_prompt)
            await page.select_option('#duration', '5')
            await page.select_option('#tier', 'fast')
            
            # Check the audio checkbox
            audio_checkbox = page.locator('#enable-audio')
            is_checked = await audio_checkbox.is_checked()
            print(f"   Audio checkbox initially checked: {is_checked}")
            
            if not is_checked:
                await audio_checkbox.check()
                print("   ✅ Checked audio generation checkbox")
            
            # Verify checkbox is checked
            is_checked = await audio_checkbox.is_checked()
            print(f"   Audio checkbox now checked: {is_checked}")
            
            # Step 4: Submit form and capture network request
            print("\n4️⃣ Submitting form and monitoring API calls...")
            
            # Set up request monitoring
            api_request_data = None
            job_id = None
            
            async def capture_request(request):
                nonlocal api_request_data, job_id
                if '/jobs' in request.url and request.method == 'POST':
                    try:
                        api_request_data = request.post_data_json
                        print(f"\n📤 API Request captured:")
                        print(f"   URL: {request.url}")
                        print(f"   Body: {json.dumps(api_request_data, indent=2)}")
                    except:
                        pass
            
            async def capture_response(response):
                nonlocal job_id
                if '/jobs' in response.url and response.request.method == 'POST':
                    try:
                        data = await response.json()
                        job_id = data.get('jobId')
                        print(f"\n📥 API Response:")
                        print(f"   Status: {response.status}")
                        print(f"   Job ID: {job_id}")
                    except:
                        pass
            
            page.on("request", capture_request)
            page.on("response", capture_response)
            
            # Submit the form
            await page.click('button:has-text("Generate Video")')
            
            # Wait for API call
            await page.wait_for_timeout(3000)
            
            # Step 5: Verify request included audio feature
            print("\n5️⃣ Analyzing submission...")
            if api_request_data:
                has_audio_feature = 'feature' in api_request_data and api_request_data['feature'].get('audio') == True
                print(f"✅ Request data captured")
                print(f"   Has audio feature: {has_audio_feature}")
                
                if has_audio_feature:
                    print(f"   Audio tier: {api_request_data['feature'].get('audioTier', 'Not specified')}")
                else:
                    print("❌ Audio feature NOT included in request!")
            else:
                print("❌ Failed to capture API request")
            
            # Step 6: Check job in DynamoDB
            if job_id:
                print(f"\n6️⃣ Checking job {job_id} in database...")
                dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
                table = dynamodb.Table('Jobs-prod')
                
                # Wait a bit for job to be saved
                await page.wait_for_timeout(2000)
                
                try:
                    response = table.get_item(Key={'jobId': job_id})
                    if 'Item' in response:
                        job = response['Item']
                        print(f"✅ Job found in DynamoDB")
                        print(f"   Status: {job.get('status')}")
                        print(f"   Has feature field: {'feature' in job}")
                        if 'feature' in job:
                            print(f"   Feature: {job['feature']}")
                            print(f"   Audio enabled: {job['feature'].get('audio', False)}")
                    else:
                        print("❌ Job not found in DynamoDB")
                except Exception as e:
                    print(f"❌ Error checking DynamoDB: {e}")
            
            # Step 7: Monitor for audio generation
            print("\n7️⃣ Monitoring page for audio controls...")
            
            # Wait for job to complete (with timeout)
            max_wait = 60  # seconds
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                # Check if sync controls appear
                sync_controls = await page.query_selector('.sync-controls')
                if sync_controls:
                    print("✅ Audio sync controls found on page!")
                    
                    # Check for audio element
                    audio_element = await page.query_selector('audio')
                    if audio_element:
                        audio_src = await audio_element.get_attribute('src')
                        print(f"✅ Audio element found with source: {audio_src[:50]}...")
                    break
                
                # Check for completion
                completed_jobs = await page.query_selector_all('.job-item.completed')
                if completed_jobs:
                    print(f"   Job completed, checking for audio...")
                
                await page.wait_for_timeout(5000)
            
            # Take screenshot
            await page.screenshot(path='audio-test-result.png')
            print("\n📸 Screenshot saved as audio-test-result.png")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            await page.screenshot(path='audio-test-error.png')
            
        finally:
            await browser.close()

# Run the test
if __name__ == "__main__":
    asyncio.run(run_test())