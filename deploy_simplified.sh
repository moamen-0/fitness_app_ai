#!/bin/bash

# Script to deploy the fitness app to Cloud Run with simplified settings

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

# Grant IAM permissions first
echo "Setting up IAM permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_ID@appspot.gserviceaccount.com" \
    --role="roles/run.admin"

# Build and push the Docker image to Container Registry
echo "Building and pushing Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/fitness-app

# Deploy to Cloud Run with minimal settings
echo "Deploying to Cloud Run with basic settings..."
gcloud run deploy fitness-app \
    --image gcr.io/$PROJECT_ID/fitness-app \
    --platform managed \
    --region us-central1 \
    --memory 1Gi \
    --timeout 300 \
    --port 8080 \
    --min-instances 1 \
    --max-instances 2 \
    --session-affinity

# Make the service public
echo "Setting up public access..."
gcloud run services add-iam-policy-binding fitness-app \
    --region=us-central1 \
    --member=allUsers \
    --role=roles/run.invoker

# Show details of the deployment
echo "Deployment completed. Your app should be available at:"
gcloud run services describe fitness-app --platform managed --region us-central1 --format="value(status.url)"

echo "To view logs, run:"
echo "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=fitness-app\" --limit=20"
