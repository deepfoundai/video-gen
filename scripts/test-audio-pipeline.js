const { chromium } = require('playwright');
const AWS = require('aws-sdk');

async function testAudioPipeline() {
    console.log('🎬 Testing Complete Audio Pipeline\n');
    console.log('=' .repeat(50));
    
    const cognito = new AWS.CognitoIdentityServiceProvider({ region: 'us-east-1' });
    const dynamodb = new AWS.DynamoDB.DocumentClient({ region: 'us-east-1' });
    
    // Test results tracking
    const results = {
        backend: { passed: 0, failed: 0 },
        frontend: { passed: 0, failed: 0 }
    };
    
    // Test user credentials
    const testUser = {
        email: 'todd@theintersecto.com',
        password: 'TempPassword123!'
    };
    
    // Known job with audio
    const KNOWN_AUDIO_JOB_ID = '923db587-8724-4ee4-b792-82fc83da6793';
    
    try {
        // =========================
        // PART 1: Backend Testing
        // =========================
        console.log('\n📊 PART 1: Backend API Testing');
        console.log('-' .repeat(40));
        
        // 1.1 Authenticate
        console.log('\n1.1 Authenticating...');
        const authResult = await cognito.initiateAuth({
            AuthFlow: 'USER_PASSWORD_AUTH',
            ClientId: '7paapnr8fbkanimk5bgpriagmg',
            AuthParameters: {
                USERNAME: testUser.email,
                PASSWORD: testUser.password
            }
        }).promise();
        
        const idToken = authResult.AuthenticationResult.IdToken;
        console.log('✅ Authentication successful');
        results.backend.passed++;
        
        // 1.2 Check DynamoDB directly
        console.log('\n1.2 Checking DynamoDB for audio data...');
        const dbResult = await dynamodb.get({
            TableName: 'Jobs-prod',
            Key: { jobId: KNOWN_AUDIO_JOB_ID }
        }).promise();
        
        const dbAudioUrl = dbResult.Item?.audioUrl;
        const dbVideoUrl = dbResult.Item?.outputUrl;
        console.log(`   Video URL in DB: ${dbVideoUrl ? '✅' : '❌'}`);
        console.log(`   Audio URL in DB: ${dbAudioUrl ? '✅' : '❌'}`);
        
        if (dbAudioUrl) {
            console.log(`   Audio URL: ${dbAudioUrl}`);
            results.backend.passed++;
        } else {
            results.backend.failed++;
        }
        
        // 1.3 Test API GetJob endpoint
        console.log('\n1.3 Testing GetJob API endpoint...');
        const getJobResponse = await fetch(`https://jobsapi.deepfoundai.com/jobs/${KNOWN_AUDIO_JOB_ID}`, {
            headers: {
                'Authorization': `Bearer ${idToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const jobData = await getJobResponse.json();
        console.log(`   API Response status: ${getJobResponse.status}`);
        console.log(`   audioUrl in API response: ${jobData.audioUrl ? '✅' : '❌'}`);
        
        if (jobData.audioUrl) {
            console.log(`   ✅ API returns audioUrl: ${jobData.audioUrl}`);
            results.backend.passed++;
        } else {
            console.log(`   ❌ API missing audioUrl field`);
            console.log(`   Full API response: ${JSON.stringify(jobData, null, 2)}`);
            results.backend.failed++;
        }
        
        // 1.4 Test ListJobs endpoint
        console.log('\n1.4 Testing ListJobs API endpoint...');
        const listJobsResponse = await fetch('https://jobsapi.deepfoundai.com/jobs', {
            headers: {
                'Authorization': `Bearer ${idToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const listData = await listJobsResponse.json();
        const jobInList = listData.jobs?.find(j => j.jobId === KNOWN_AUDIO_JOB_ID);
        
        if (jobInList?.audioUrl) {
            console.log('   ✅ ListJobs includes audioUrl field');
            results.backend.passed++;
        } else {
            console.log('   ❌ ListJobs missing audioUrl field');
            results.backend.failed++;
        }
        
        // 1.5 Submit new job with audio
        console.log('\n1.5 Submitting new job with audio...');
        const newJobResponse = await fetch('https://jobsapi.deepfoundai.com/jobs/submit', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${idToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: `Audio test ${new Date().toISOString()} - ocean waves`,
                duration_seconds: 5,
                resolution: '720p',
                tier: 'fast',
                feature: {
                    audio: true,
                    audioTier: 'fast'
                }
            })
        });
        
        if (newJobResponse.ok) {
            const newJob = await newJobResponse.json();
            console.log(`   ✅ New job submitted: ${newJob.jobId}`);
            results.backend.passed++;
            
            // Wait and check if audio is generated
            console.log('   Waiting 30 seconds for processing...');
            await new Promise(resolve => setTimeout(resolve, 30000));
            
            const checkResponse = await fetch(`https://jobsapi.deepfoundai.com/jobs/${newJob.jobId}`, {
                headers: { 'Authorization': `Bearer ${idToken}` }
            });
            
            const checkData = await checkResponse.json();
            if (checkData.audioUrl) {
                console.log('   ✅ New job has audio URL!');
                results.backend.passed++;
            } else {
                console.log('   ❌ New job missing audio URL');
                results.backend.failed++;
            }
        } else {
            console.log(`   ❌ Failed to submit job: ${newJobResponse.status}`);
            results.backend.failed++;
        }
        
        // =========================
        // PART 2: Frontend Testing
        // =========================
        console.log('\n\n📊 PART 2: Frontend Browser Testing');
        console.log('-' .repeat(40));
        
        const browser = await chromium.launch({ 
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        const context = await browser.newContext();
        const page = await context.newPage();
        
        // Capture console for debugging
        page.on('console', msg => {
            if (msg.type() === 'error') {
                console.log(`[BROWSER ERROR] ${msg.text()}`);
            }
        });
        
        // 2.1 Navigate to frontend
        console.log('\n2.1 Navigating to frontend...');
        await page.goto('https://video.deepfoundai.com');
        await page.waitForLoadState('networkidle');
        console.log('   ✅ Page loaded');
        results.frontend.passed++;
        
        // 2.2 Login
        console.log('\n2.2 Logging in...');
        await page.fill('#login-email', testUser.email);
        await page.fill('#login-password', testUser.password);
        await page.click('button[type="submit"]');
        
        // Wait for main section
        await page.waitForSelector('#main-section', { timeout: 10000 });
        console.log('   ✅ Login successful');
        results.frontend.passed++;
        
        // 2.3 Check for jobs with audio
        console.log('\n2.3 Checking for audio controls...');
        await page.waitForTimeout(3000); // Wait for jobs to load
        
        // Look for audio controls
        const audioControls = await page.$$('.sync-controls');
        console.log(`   Found ${audioControls.length} jobs with audio controls`);
        
        if (audioControls.length > 0) {
            console.log('   ✅ Audio controls are displayed');
            results.frontend.passed++;
            
            // Check specific elements
            const playButton = await page.$('button:has-text("Play Video with Audio")');
            const pauseButton = await page.$('button:has-text("Pause")');
            const restartButton = await page.$('button:has-text("Restart")');
            
            if (playButton && pauseButton && restartButton) {
                console.log('   ✅ All audio control buttons present');
                results.frontend.passed++;
            } else {
                console.log('   ❌ Some audio control buttons missing');
                results.frontend.failed++;
            }
        } else {
            console.log('   ❌ No audio controls found');
            results.frontend.failed++;
            
            // Debug: Check what's in the job data
            const jobDataInDOM = await page.evaluate(() => {
                const jobElements = document.querySelectorAll('.job-item');
                return Array.from(jobElements).map(el => {
                    const promptEl = el.querySelector('.prompt-text');
                    return {
                        prompt: promptEl?.textContent || 'No prompt',
                        html: el.innerHTML.substring(0, 200)
                    };
                });
            });
            
            console.log('\n   Debug - Jobs in DOM:');
            jobDataInDOM.forEach((job, i) => {
                console.log(`   Job ${i + 1}: ${job.prompt}`);
                if (job.html.includes('audioUrl')) {
                    console.log('     - Contains audioUrl in HTML');
                }
            });
        }
        
        // 2.4 Submit new job with audio checkbox
        console.log('\n2.4 Testing audio job submission from frontend...');
        await page.fill('#prompt', `Frontend audio test ${Date.now()}`);
        
        // Check if audio checkbox exists
        const audioCheckbox = await page.$('#enableAudio');
        if (audioCheckbox) {
            await page.check('#enableAudio');
            console.log('   ✅ Audio checkbox found and checked');
            results.frontend.passed++;
        } else {
            console.log('   ❌ Audio checkbox not found');
            results.frontend.failed++;
        }
        
        // Take screenshot for debugging
        await page.screenshot({ path: '/tmp/audio-test-frontend.png' });
        console.log('\n   Screenshot saved to /tmp/audio-test-frontend.png');
        
        await browser.close();
        
    } catch (error) {
        console.error('\n❌ Test error:', error.message);
        results.backend.failed++;
    }
    
    // =========================
    // Test Summary
    // =========================
    console.log('\n\n' + '=' .repeat(50));
    console.log('📊 TEST SUMMARY');
    console.log('=' .repeat(50));
    
    console.log('\nBackend Tests:');
    console.log(`  ✅ Passed: ${results.backend.passed}`);
    console.log(`  ❌ Failed: ${results.backend.failed}`);
    
    console.log('\nFrontend Tests:');
    console.log(`  ✅ Passed: ${results.frontend.passed}`);
    console.log(`  ❌ Failed: ${results.frontend.failed}`);
    
    const totalPassed = results.backend.passed + results.frontend.passed;
    const totalFailed = results.backend.failed + results.frontend.failed;
    
    console.log('\nTotal:');
    console.log(`  ✅ Passed: ${totalPassed}`);
    console.log(`  ❌ Failed: ${totalFailed}`);
    
    if (totalFailed === 0) {
        console.log('\n✅ All tests passed! Audio pipeline is working correctly.');
    } else {
        console.log('\n❌ Some tests failed. Check the details above.');
        
        console.log('\nCommon issues:');
        console.log('1. API not returning audioUrl - Lambda functions need update');
        console.log('2. Frontend not showing controls - Check if audioUrl is in API response');
        console.log('3. Audio not generated - Check audio-handler Lambda logs');
    }
}

// Run the test
testAudioPipeline().catch(console.error);