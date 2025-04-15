# Cloud Run Deployment Troubleshooting

If you're encountering issues deploying to Cloud Run, follow this step-by-step troubleshooting guide.

## Common Error: Container Failed to Start

If you see: `The user-provided container failed to start and listen on the port defined provided by the PORT=8080 environment variable`

### Step 1: Verify IAM Permissions

```bash
# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:YOUR_PROJECT_ID@appspot.gserviceaccount.com" \
    --role="roles/run.admin"

# Allow public access
gcloud run services add-iam-policy-binding fitness-app \
    --region=us-central1 \
    --member=allUsers \
    --role=roles/run.invoker
```

### Step 2: Check Logs for Specific Errors

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=fitness-app" --limit=20
```

Common issues to look for:
- Missing dependencies
- Initialization errors
- Port binding issues
- Crashes during startup

### Step 3: Try the Simplified Deployment

Use the `deploy_simplified.sh` script which:
- Uses a basic configuration
- Removes complex settings
- Adds proper IAM permissions
- Uses minimal resource requirements

### Step 4: Verify with Test App

If the main app still fails, deploy the test app to verify Cloud Run is working:

```bash
./deploy_test_app.sh
```

This will deploy a minimal Flask app without any complex dependencies.

### Step 5: Container Debugging

For detailed container debugging:

```bash
# Build locally
docker build -t fitness-app .

# Run locally
docker run -p 8080:8080 fitness-app

# Check container logs
docker logs CONTAINER_ID
```

### Step 6: Common Fixes

1. **Gunicorn Configuration Issues**:
   - Check worker class compatibility
   - Reduce worker count to 1
   - Increase timeout values

2. **MediaPipe Initialization**:
   - Wrap MediaPipe initialization in try/except
   - Defer initialization until needed

3. **Port Binding**:
   - Ensure app listens on the port defined by PORT environment variable
   - Verify the EXPOSE command matches the environment variable

4. **Memory/CPU Limits**:
   - Increase memory allocation (at least 1Gi for MediaPipe)
   - Ensure CPU allocation is sufficient

## Last Resort

If all else fails, consider:
1. Using App Engine Flexible environment instead
2. Simplifying the application to remove complex dependencies
3. Breaking down into microservices with simpler components
