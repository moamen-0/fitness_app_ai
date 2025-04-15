# Getting WebSockets Working on Google App Engine

WebSocket support on Google App Engine can be tricky. This guide covers how to properly configure and troubleshoot WebSocket connections for your Flask-SocketIO application.

## Key Configuration Points

### 1. App Engine Configuration (app.yaml)

The `app.yaml` configuration is critical:

```yaml
runtime: python39
entrypoint: gunicorn -b :$PORT -w 1 --timeout 300 --worker-class eventlet 'app:app'
instance_class: F4  # Use at least F2 or higher

network:
  session_affinity: true  # CRITICAL for WebSockets
  
manual_scaling:
  instances: 1  # Use manual scaling to prevent instance shutdown
```

Important settings:
- **Worker class**: Must be `eventlet` for WebSocket support
- **Single worker**: `-w 1` prevents issues with multiple workers
- **Session affinity**: Ensures requests from the same client go to the same instance
- **Manual scaling**: Prevents your instance from being shut down between requests

### 2. Flask-SocketIO Configuration

```python
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    engineio_logger=True,
    logger=True,
    ping_interval=25,  # Shorter ping interval helps keep connections alive
    ping_timeout=60,
    transports=['polling', 'websocket']  # Start with polling, upgrade to WebSocket
)
```

### 3. Client-Side Configuration

```javascript
const socket = io(serverUrl, {
    transports: ['polling', 'websocket'],  // Start with polling
    upgrade: true,                         // Try to upgrade to WebSocket
    reconnection: true,
    reconnectionAttempts: 5,
    timeout: 20000
});
```

## Common Issues and Solutions

### 1. "Service Unavailable" Error

If you're getting "Service Unavailable" errors when trying to access your WebSocket endpoint:

- **Check logs**: In Google Cloud Console, go to "Logging" and filter for your service
- **Verify instance**: Make sure your App Engine instance is actually running
- **Increase instance class**: Try using F4 instead of F2/F1

### 2. WebSocket Connection Fails, Falls Back to Polling

If WebSocket connections attempt to establish but then fall back to polling:

- **Check HTTPS**: WebSockets require secure connections in production
- **Verify session affinity**: Make sure `session_affinity: true` is set
- **Check timeouts**: App Engine has a 60-second timeout; make sure your ping interval is shorter

### 3. Connections Drop After Inactivity

If connections drop after periods of inactivity:

- **Reduce ping interval**: Set `ping_interval` to 25 seconds
- **Client reconnection**: Implement automatic reconnection on the client
- **Keep-alive messages**: Send periodic messages to keep the connection active

## Debugging Steps

1. **Check App Engine logs**: Look for connection errors or timeouts
2. **Verify correct endpoint**: Make sure your client is connecting to the right URL
3. **Test with polling only**: Try setting `transports: ['polling']` to see if basic communication works
4. **Check network settings**: Ensure no firewalls or proxies are blocking WebSocket connections

## Final Notes

- App Engine Standard has more limitations for WebSockets than Flexible Environment
- Consider using Cloud Run as an alternative if WebSockets are critical for your application
- Always implement a fallback to polling for clients where WebSockets are not available
