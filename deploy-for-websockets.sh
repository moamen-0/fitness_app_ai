#!/bin/bash

# Deploy to Cloud Run with WebSocket support
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
  --execution-environment gen2 \
  --port 8080 \
  --set-env-vars="PYTHONUNBUFFERED=True,DEBUG=False" \
  --ingress=all \
  --vpc-egress=private-ranges-only
