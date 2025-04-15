#!/bin/bash

# Deploy to Cloud Run with proper WebSocket configuration
gcloud run deploy ai-fitness-trainer \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --session-affinity \
  --min-instances 1 \
  --cpu 1 \
  --memory 512Mi \
  --concurrency 80 \
  --timeout 300s \
  --set-env-vars="PYTHONUNBUFFERED=True" \
  --ingress=all
