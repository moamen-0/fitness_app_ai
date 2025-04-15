#!/bin/bash

# Script to deploy the fitness app to Cloud Run

# Display current gcloud config
echo "Current gcloud configuration:"
gcloud config list

# Ask for project ID
read -p "Enter your Google Cloud Project ID: " PROJECT_ID

# Confirm project ID
echo "You entered: $PROJECT_ID"
read -p "Is this correct? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "Deployment cancelled."
    exit 1
fi

# Set the project
echo "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Build and push the Docker image to Container Registry
echo "Building and pushing Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/fitness-app

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy fitness-app \
    --image gcr.io/$PROJECT_ID/fitness-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --min-instances=1 \
    --memory=2Gi \
    --cpu=1 \
    --set-env-vars="MEDIAPIPE_MODEL_COMPLEXITY=1" \
    --concurrency=80 \
    --session-affinity

# Show details of the deployment
echo "Deployment completed. Your app should be available at:"
gcloud run services describe fitness-app --platform managed --region us-central1 --format="value(status.url)"

echo "To view logs, run:"
echo "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=fitness-app\" --limit=10"
