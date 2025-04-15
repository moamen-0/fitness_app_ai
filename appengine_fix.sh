#!/bin/bash

echo "App Engine 502 Bad Gateway Troubleshooter"
echo "========================================="

# Check project ID
echo "1. Checking current Google Cloud project:"
PROJECT_ID=$(gcloud config get-value project)
echo "   Current project: $PROJECT_ID"

# Check app status
echo "2. Checking App Engine status:"
gcloud app describe

# Check recent deployments
echo "3. Checking recent deployments:"
gcloud app versions list --sort-by=~version_id --limit=3

# Check logs for recent errors
echo "4. Checking App Engine logs for errors:"
gcloud logging read "resource.type=gae_app AND severity>=ERROR" --limit=10 --format="table(timestamp, severity, textPayload)"

# Get diagnostic info
echo "5. Getting more detailed diagnostic information..."
gcloud app instances list

echo "6. Suggestions:"
echo "   - Check if your app has the correct entrypoint in app.yaml"
echo "   - Ensure main.py properly imports and initializes your app"
echo "   - Look for import errors or startup failures in the logs"
echo "   - Try a simple test app to verify App Engine is working"

echo "7. Fixes to try:"
echo "   a. Redeploy with updated configuration:"
echo "      gcloud app deploy app.yaml --project=$PROJECT_ID"
echo ""
echo "   b. If issues persist, try deploying a minimal app"
echo "      (Create a simple main.py and app.yaml to test)"
echo ""
echo "   c. Check if your service account has proper permissions"
echo "      gcloud projects get-iam-policy $PROJECT_ID"
echo ""
echo "   d. Restart the App Engine service from the Google Cloud Console"
