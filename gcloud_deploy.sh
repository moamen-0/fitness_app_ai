#!/bin/bash

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

# Deploy the app
echo "Deploying application to App Engine..."
gcloud app deploy app.yaml --quiet

# Show URL after deployment
echo "Deployment completed. Your app should be available at:"
echo "https://$PROJECT_ID.oa.r.appspot.com/"

# Show logs command
echo "To view logs, run:"
echo "gcloud app logs tail -s default"
