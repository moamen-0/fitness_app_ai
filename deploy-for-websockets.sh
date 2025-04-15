gcloud run deploy ai-fitness-trainer \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --session-affinity \
  --use-http2 \
  --min-instances 1 \
  --timeout 300s