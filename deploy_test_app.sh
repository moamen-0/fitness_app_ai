#!/bin/bash

# Script to deploy a minimal test app to Cloud Run for verification

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

# Create a minimal Dockerfile for test app
cat > Dockerfile.test << EOF
FROM python:3.9-slim

WORKDIR /app

# Install Flask
RUN pip install flask gunicorn

# Copy the test app
COPY test_app.py .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 8080

# Command to run
CMD exec gunicorn --bind :8080 test_app:application
EOF

# Build and push the test Docker image
echo "Building and pushing test Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/test-fitness-app --dockerfile Dockerfile.test

# Deploy test app to Cloud Run
echo "Deploying test app to Cloud Run..."
gcloud run deploy test-fitness-app \
    --image gcr.io/$PROJECT_ID/test-fitness-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated

# Show details of the deployment
echo "Test app deployment completed. Your app should be available at:"
gcloud run services describe test-fitness-app --platform managed --region us-central1 --format="value(status.url)"

echo "To view logs, run:"
echo "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=test-fitness-app\" --limit=10"
