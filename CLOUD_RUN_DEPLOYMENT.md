# Deploying to Cloud Run for WebSocket Support

This guide explains how to deploy the Fitness App to Google Cloud Run for better WebSocket support.

## Why Cloud Run?

Cloud Run offers several advantages for WebSocket applications:

- Better WebSocket support compared to App Engine Standard
- Auto-scaling with the ability to scale to zero when not in use
- Simpler deployment through containers
- Cost-effective pricing model (pay per use)
- Higher limits for concurrent connections

## Prerequisites

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
2. Docker installed on your local machine
3. A Google Cloud project with billing enabled
4. Required APIs enabled (Cloud Run, Container Registry, Cloud Build)

## Deployment Steps

### 1. Build and Deploy using the Script

The simplest way to deploy is using the provided script:

```bash
chmod +x deploy_cloud_run.sh
./deploy_cloud_run.sh
```

Follow the prompts to enter your Google Cloud Project ID.

### 2. Manual Deployment Steps

If you prefer to deploy manually, follow these steps:

1. Build the Docker image locally and tag it:
   ```bash
   docker build -t gcr.io/YOUR_PROJECT_ID/fitness-app .
   ```

2. Configure Docker to use Google Cloud credentials:
   ```bash
   gcloud auth configure-docker
   ```

3. Push the Docker image to Google Container Registry:
   ```bash
   docker push gcr.io/YOUR_PROJECT_ID/fitness-app
   ```

4. Deploy to Cloud Run:
   ```bash
   gcloud run deploy fitness-app \
     --image gcr.io/YOUR_PROJECT_ID/fitness-app \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --session-affinity
   ```

## Testing Your Deployment

1. Once deployed, Cloud Run will provide a URL for your application.
2. Open the URL in your browser to access your Fitness App.
3. Navigate to the `/websocket_test` route to verify WebSocket connectivity.

## Troubleshooting

### WebSocket Connection Issues

If you experience WebSocket connectivity issues:

1. Verify that your client code is using secure WebSockets (`wss://`).
2. Check the Cloud Run logs for errors:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=fitness-app" --limit=20
   ```
3. Ensure `--session-affinity` was enabled during deployment.
4. Try using the WebSocket diagnostic page at `/websocket_test`.

### Application Errors

If your application fails to start:

1. Check if the container is failing to start by looking at Cloud Run logs
2. Verify your Dockerfile is correctly configured
3. Test the Docker image locally:
   ```bash
   docker run -p 8080:8080 gcr.io/YOUR_PROJECT_ID/fitness-app
   ```

## Cost Management

Cloud Run charges based on usage. To minimize costs:

1. Set appropriate minimum instances (0 for dev/test environments)
2. Configure memory and CPU appropriately
3. Set budget alerts in Google Cloud Console

## Updating Your Deployment

To update your application after making changes:

1. Rebuild and redeploy using the script:
   ```bash
   ./deploy_cloud_run.sh
   ```

2. Or manually update:
   ```bash
   docker build -t gcr.io/YOUR_PROJECT_ID/fitness-app .
   docker push gcr.io/YOUR_PROJECT_ID/fitness-app
   gcloud run deploy fitness-app --image gcr.io/YOUR_PROJECT_ID/fitness-app
   ```
