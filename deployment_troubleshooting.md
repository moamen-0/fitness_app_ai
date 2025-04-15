# Troubleshooting App Engine Deployment

If you're seeing a "Service Unavailable" error when accessing your deployed application, here are step-by-step solutions:

## Check Application Logs

First, check your application logs to see what's happening:

```bash
gcloud app logs tail -s default
```

Look for error messages that might indicate what's going wrong.

## Common Issues and Solutions

### 1. Python Dependencies Not Installing Correctly

**Solution:** 
- Verify your `requirements.txt` file is correct
- Try using compatible versions of packages
- For mediapipe, use version 0.10.18 which is known to work on App Engine

### 2. Application Crash During Startup

**Solution:**
- Check logs for specific errors
- Simplify your main.py file to be a simple WSGI entry point
- Make sure app.yaml is using the correct entrypoint

### 3. Server Not Listening on the Right Port

**Solution:**
- App Engine injects a PORT environment variable that your app must use
- Ensure your app listens on the port specified by `os.environ.get('PORT', 8080)`

### 4. Memory or Resource Limits

**Solution:**
- Increase instance class in app.yaml (F2 or higher)
- Optimize your application to use less memory

### 5. App Engine Quota Limits

**Solution:**
- Check your Google Cloud Console > App Engine > Quotas
- If you've exceeded quotas, you may need to enable billing or request quota increases

## Specific Commands to Fix

### Redeploy with Simplified Configuration

```bash
gcloud app deploy app.yaml --project=YOUR_PROJECT_ID
```

### Check Instance Status

```bash
gcloud app instances list
```

### View Application URL

```bash
gcloud app describe --format="value(defaultHostname)"
```

## If All Else Fails

1. Create a new, simple "Hello World" app.yaml and main.py
2. Deploy this minimal app to verify App Engine is working
3. Gradually add back your application components

## Final Checks

- Ensure billing is enabled for your Google Cloud project
- Verify you have the App Engine Admin API enabled
- Check that your service account has sufficient permissions
