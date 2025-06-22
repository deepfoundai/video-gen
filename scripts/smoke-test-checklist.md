# 🧪 Frontend Production Smoke Test Checklist

**URL:** https://video.deepfoundai.com  
**Date:** June 22, 2025  
**Tester:** ________________  

## Pre-Test Setup
- [ ] Open **incognito/private** browser window
- [ ] Open **Developer Tools** (F12)
- [ ] Go to **Network** tab in DevTools
- [ ] Have screenshot tool ready (for evidence)

---

## Test Sequence

### 1. 🌐 Site Load Test
- [ ] Navigate to: https://video.deepfoundai.com
- [ ] ✅ Page loads without errors
- [ ] ✅ No 404 or 500 errors in console
- [ ] ✅ SSL certificate shows valid (🔒 in address bar)
- [ ] ✅ Custom domain resolves correctly

**Screenshot:** Site loaded ________________

### 2. 🔐 Authentication Test
- [ ] Click "Sign In" or auth button
- [ ] ✅ Cognito login form appears
- [ ] Enter credentials (use test account)
- [ ] ✅ Successfully authenticated
- [ ] ✅ Redirected back to main app
- [ ] ✅ User session established

**Screenshot:** Authenticated state ________________

### 3. 📹 Job Submission Test
- [ ] Navigate to job creation/submission form
- [ ] Set parameters:
  - Duration: **8 seconds**
  - Resolution: **720p**
  - Provider: **auto**
- [ ] ✅ Form accepts all inputs
- [ ] Click "Submit" or "Create Job"
- [ ] ✅ Job created successfully
- [ ] ✅ Job ID displayed/assigned
- [ ] ✅ No error messages in console

**Job ID created:** ________________

### 4. ⏱️ Status Monitoring Test
- [ ] Navigate to job status/monitoring page
- [ ] ✅ Job appears in list/queue
- [ ] ✅ Status shows "Processing" or similar
- [ ] Wait for completion (may take 1-3 minutes)
- [ ] ✅ Status changes to "Completed"
- [ ] ✅ No timeout or error states

**Final Status:** ________________  
**Time to Complete:** ________________

### 5. 🎬 Gallery/Playback Test
- [ ] Navigate to Gallery or completed jobs
- [ ] ✅ Processed video appears in gallery
- [ ] Click on video/thumbnail
- [ ] ✅ Video player loads
- [ ] ✅ Video plays without errors
- [ ] ✅ Audio/video sync correct
- [ ] ✅ Video quality matches expectations

**Video Quality:** ________________

### 6. 📊 Admin Dashboard Test
- [ ] Navigate to Admin Dashboard
- [ ] ✅ Dashboard loads
- [ ] Check metrics/counters:
  - [ ] ✅ Job counter incremented (+1)
  - [ ] ✅ Credit counter decremented
  - [ ] ✅ Recent activity shows new job
- [ ] ✅ All tiles/widgets functional

**Job Counter Before:** _____ **After:** _____  
**Credit Counter Before:** _____ **After:** _____

---

## 🚨 Error Reporting

### If ANY step fails:
1. **Immediately** take screenshot of error
2. **Copy** full error message from console
3. **Capture** Network tab showing failed requests
4. **Note** exact time of failure
5. **Create** issue: `FRONT-BUG-smoketest-2025-06-22-{step}`

### Console Log Check
At the end of testing, check Developer Console for:
- [ ] ✅ No red error messages
- [ ] ✅ No 404 network requests
- [ ] ✅ No CORS errors
- [ ] ✅ No authentication errors

**Console Status:** ________________

---

## 📝 Test Results Summary

| Test Step | Status | Notes |
|-----------|--------|--------|
| Site Load | ⭕ PASS / ❌ FAIL | |
| Authentication | ⭕ PASS / ❌ FAIL | |
| Job Submission | ⭕ PASS / ❌ FAIL | |
| Status Monitoring | ⭕ PASS / ❌ FAIL | |
| Gallery Playback | ⭕ PASS / ❌ FAIL | |
| Admin Dashboard | ⭕ PASS / ❌ FAIL | |

**Overall Result:** ⭕ PASS / ❌ FAIL  
**Ready for Production:** ⭕ YES / ❌ NO  

**Tester Signature:** ________________  
**Completed Time:** ________________  

---

## 📋 Next Steps After Testing

### If ALL PASS ✅:
1. Upload screenshots to PR
2. Record Loom/GIF of successful flow
3. Notify Frontend team: "Smoke test PASSED ✅"
4. Frontend can proceed with PR creation

### If ANY FAIL ❌:
1. Create detailed bug report
2. Include all screenshots and console logs
3. Notify Frontend team: "Smoke test FAILED ❌"
4. **HALT** release process until fixed 