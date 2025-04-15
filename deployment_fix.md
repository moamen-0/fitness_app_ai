# Fixing 502 Bad Gateway in App Engine WebSocket App

This guide provides step-by-step instructions to fix the 502 Bad Gateway error you're encountering with your Socket.IO WebSocket application on App Engine.

## Causes of 502 Bad Gateway

The 502 Bad Gateway error usually indicates:

1. Your app is crashing during startup
2. The WebSocket setup isn't compatible with App Engine
3. Issues with MediaPipe initialization 
4. Entrypoint configuration problems

## Fix #1: Deploy with Simplified Configuration

The most important changes we've made:

1. **Moved MediaPipe initialization to module level** in `main.py`
2. **Added proper Socket.IO middleware** with `app = socketio.middleware(app)`
3. **Simplified the entrypoint** in `app.yaml`

Deploy using:

```bash
gcloud app deploy app.yaml --project=pure-highlander-456910-i7
```

## Fix #2: Check the Logs

If the first fix doesn't work, check the logs:

```bash
gcloud app logs tail --project=pure-highlander-456910-i7
```

Look for specific error messages during app startup.

## Fix #3: Try Simplified Export

If the error persists, modify `main.py` to:

```python
# Google Cloud App Engine uses this as the entry point
from app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
```

And `app.yaml` to:

```yaml
runtime: python39
entrypoint: gunicorn -b :$PORT 'main:app'
instance_class: F2
```

This removes the WebSocket functionality but lets you verify basic app deployment.

## Fix #4: Verify Socket.IO Transport Settings

If basic deployment works, the issue is with Socket.IO. In `app.py`, modify:

```python
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    engineio_logger=True,
    ping_interval=25,
    ping_timeout=60,
    transports=['polling', 'websocket']  # Try with just polling if issues persist
)
```

## Fix #5: Use the diagnostic tools

After deployment, visit:
- `/healthz` - Should return a simple status check
- `/websocket_test` - Tests WebSocket connectivity

The WebSocket test page includes built-in diagnostics to help identify specific issues.

## Still Having Issues?

Try Cloud Run instead, which often works better for WebSocket applications:

```bash
gcloud run deploy --source . --platform managed --region us-central1 --allow-unauthenticated
```

Make sure your `Dockerfile` is properly configured first.
