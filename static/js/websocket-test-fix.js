/**
 * WebSocket connection troubleshooter
 * This script provides advanced diagnostics for WebSocket connections on App Engine
 */

// Global variables
let socket = null;
const connectionModes = ['polling', 'websocket'];
let currentMode = 0;

// Initialize connection
function initializeSocketConnection(url) {
    // Clean up previous connection if any
    if (socket) {
        socket.disconnect();
        socket = null;
    }
    
    // Log connection attempt
    console.log(`Attempting connection using mode: ${connectionModes[currentMode]}`);
    
    // Create connection with specific options
    socket = io(url, {
        transports: [connectionModes[currentMode]],
        upgrade: false,
        reconnection: true,
        reconnectionAttempts: 3,
        reconnectionDelay: 1000,
        timeout: 10000
    });
    
    // Set up event handlers
    setupSocketEventHandlers(socket);
    
    return socket;
}

// Set up socket event handlers
function setupSocketEventHandlers(socket) {
    socket.on('connect', () => {
        console.log(`Successfully connected via ${connectionModes[currentMode]}`);
        logEvent('connect', `Connected using ${connectionModes[currentMode]} transport`);
        
        // If we connected with polling, try to upgrade to websocket
        if (currentMode === 0) {
            setTimeout(() => {
                logEvent('info', 'Attempting to upgrade to WebSocket...');
                socket.io.engine.transport.upgrade();
            }, 1000);
        }
    });
    
    socket.on('connect_error', (error) => {
        console.error(`Connection error: ${error.message}`);
        logEvent('error', `Connection error: ${error.message}`);
        
        // If WebSocket failed, fall back to polling
        if (currentMode === 1) {
            currentMode = 0;
            logEvent('info', 'Falling back to long-polling transport');
            setTimeout(() => {
                initializeSocketConnection(socket.io.uri);
            }, 1000);
        }
    });
    
    socket.io.engine.on('upgrade', () => {
        logEvent('upgrade', 'Connection upgraded to WebSocket');
    });
    
    socket.io.engine.on('upgradeError', (err) => {
        logEvent('error', `WebSocket upgrade failed: ${err}`);
    });
    
    socket.on('disconnect', (reason) => {
        logEvent('disconnect', `Disconnected: ${reason}`);
    });
    
    // Ping/pong handlers
    socket.on('pong', (data) => {
        logEvent('pong', `Server responded: ${JSON.stringify(data)}`);
    });
}

// Add an event to the log
function logEvent(type, message) {
    const logContainer = document.getElementById('log-container');
    if (!logContainer) return;
    
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    
    const timestamp = new Date().toISOString().substring(11, 19);
    const typeColor = type === 'error' ? 'red' : 
                     type === 'connect' ? 'green' : 
                     type === 'disconnect' ? 'orange' : 
                     type === 'upgrade' ? 'purple' : 'blue';
    
    entry.innerHTML = `<span style="color: #777;">[${timestamp}]</span> <span style="color: ${typeColor}">${message}</span>`;
    
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
    
    // Update status
    updateConnectionStatus(type);
}

// Update connection status indicator
function updateConnectionStatus(type) {
    const statusElement = document.getElementById('status');
    if (!statusElement) return;
    
    if (type === 'connect') {
        statusElement.className = 'connection-status connected';
        statusElement.textContent = 'Connected ✅';
    } else if (type === 'disconnect' || type === 'error') {
        statusElement.className = 'connection-status disconnected';
        statusElement.textContent = 'Disconnected ❌';
    } else if (type === 'upgrade') {
        statusElement.className = 'connection-status connected';
        statusElement.textContent = 'Connected (WebSocket) ✅✅';
    }
}

// Send a ping message
function sendPing() {
    if (!socket || !socket.connected) {
        logEvent('error', 'Not connected. Cannot send ping.');
        return;
    }
    
    const data = { message: "Ping from client", timestamp: Date.now() };
    socket.emit('ping', data);
    logEvent('info', `Sent ping: ${JSON.stringify(data)}`);
}

// Try to connect with WebSocket first, then fall back to polling if needed
function connectWithFallback(url) {
    currentMode = 1; // Start with WebSocket
    return initializeSocketConnection(url);
}

// Make functions available globally
window.wsTestUtils = {
    connect: function(url) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = url || window.location.host;
        const wsUrl = `${protocol}//${host}`;
        
        logEvent('info', `Connecting to: ${wsUrl}`);
        return connectWithFallback(wsUrl);
    },
    disconnect: function() {
        if (socket) {
            socket.disconnect();
            logEvent('info', 'Manually disconnected');
        } else {
            logEvent('error', 'No active connection to disconnect');
        }
    },
    ping: sendPing,
    getStatus: function() {
        if (!socket) return 'No connection';
        return socket.connected ? 'Connected' : 'Disconnected';
    },
    getCurrentTransport: function() {
        if (!socket || !socket.io || !socket.io.engine) return 'Unknown';
        return socket.io.engine.transport.name;
    }
};
