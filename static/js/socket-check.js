/**
 * Socket.IO connectivity checker for App Engine deployments
 */
class SocketConnectionChecker {
    constructor() {
        this.socket = null;
        this.results = {
            connectionAttempts: 0,
            successfulConnections: 0,
            failedConnections: 0,
            pollingSucceeded: false,
            websocketSucceeded: false,
            latestError: null,
            latency: []
        };
        this.logContainer = null;
    }

    /**
     * Initialize the diagnostic UI
     */
    initUI() {
        // Create diagnostic container if it doesn't exist
        const existingContainer = document.getElementById('socket-diagnostics');
        if (existingContainer) {
            this.logContainer = existingContainer.querySelector('.socket-log');
            return;
        }

        const container = document.createElement('div');
        container.id = 'socket-diagnostics';
        container.style.cssText = 'position:fixed; bottom:0; right:0; width:400px; background:#f8f9fa; border:1px solid #dee2e6; padding:10px; z-index:9999; font-family:monospace; font-size:12px; box-shadow:0 0 10px rgba(0,0,0,0.2);';
        
        const header = document.createElement('div');
        header.innerHTML = '<h3 style="margin:0 0 10px 0;">Socket.IO Diagnostics</h3><button id="socket-close-btn" style="position:absolute; top:5px; right:5px; cursor:pointer;">✕</button>';
        container.appendChild(header);
        
        const statusBox = document.createElement('div');
        statusBox.id = 'socket-status';
        statusBox.style.cssText = 'background:#e9ecef; padding:5px; margin-bottom:10px; border-radius:3px;';
        statusBox.innerText = 'Initializing...';
        container.appendChild(statusBox);
        
        const logBox = document.createElement('div');
        logBox.classList.add('socket-log');
        logBox.style.cssText = 'height:200px; overflow-y:auto; background:#343a40; color:#f8f9fa; padding:5px; border-radius:3px; margin-bottom:10px;';
        container.appendChild(logBox);
        
        const buttonBox = document.createElement('div');
        buttonBox.style.cssText = 'display:flex; justify-content:space-between;';
        buttonBox.innerHTML = `
            <button id="test-polling-btn" style="padding:5px 10px;">Test Long Polling</button>
            <button id="test-websocket-btn" style="padding:5px 10px;">Test WebSocket</button>
            <button id="test-ping-btn" style="padding:5px 10px;">Send Ping</button>
        `;
        container.appendChild(buttonBox);
        
        document.body.appendChild(container);
        
        // Set up event handlers
        document.getElementById('socket-close-btn').addEventListener('click', () => {
            container.style.display = 'none';
        });
        
        document.getElementById('test-polling-btn').addEventListener('click', () => {
            this.testConnection('polling');
        });
        
        document.getElementById('test-websocket-btn').addEventListener('click', () => {
            this.testConnection('websocket');
        });
        
        document.getElementById('test-ping-btn').addEventListener('click', () => {
            this.sendPing();
        });
        
        this.logContainer = logBox;
    }

    /**
     * Log a message to the diagnostic UI
     * @param {string} message - Message to log
     * @param {string} type - Type of log (info, success, error, warning)
     */
    log(message, type = 'info') {
        if (!this.logContainer) this.initUI();
        
        const colors = {
            info: '#17a2b8',
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107'
        };
        
        const entry = document.createElement('div');
        entry.style.marginBottom = '5px';
        
        const timestamp = new Date().toTimeString().split(' ')[0];
        entry.innerHTML = `<span style="color:#6c757d;">[${timestamp}]</span> <span style="color:${colors[type]};">${message}</span>`;
        
        this.logContainer.appendChild(entry);
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
        
        // Also log to console
        console.log(`[Socket Diag ${type}] ${message}`);
    }

    /**
     * Update the status display
     * @param {string} status - Status message
     * @param {string} type - Type of status (info, success, error, warning)
     */
    updateStatus(status, type = 'info') {
        const statusBox = document.getElementById('socket-status');
        if (!statusBox) return;
        
        const bgColors = {
            info: '#e9ecef',
            success: '#d4edda',
            error: '#f8d7da',
            warning: '#fff3cd'
        };
        
        const textColors = {
            info: '#343a40',
            success: '#155724',
            error: '#721c24',
            warning: '#856404'
        };
        
        statusBox.style.background = bgColors[type];
        statusBox.style.color = textColors[type];
        statusBox.innerText = status;
    }

    /**
     * Test connection using specified transport
     * @param {string} transport - Transport to test (polling, websocket)
     */
    testConnection(transport) {
        this.results.connectionAttempts++;
        
        // Disconnect any existing connection
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        
        this.log(`Testing connection using ${transport} transport...`);
        this.updateStatus(`Connecting via ${transport}...`, 'info');
        
        const startTime = Date.now();
        
        // Create connection with specific transport
        this.socket = io(window.location.origin, {
            transports: [transport],
            upgrade: false,
            reconnection: true,
            reconnectionAttempts: 3,
            timeout: 10000
        });
        
        // Set up event handlers
        this.socket.on('connect', () => {
            const elapsed = Date.now() - startTime;
            this.results.latency.push(elapsed);
            
            this.results.successfulConnections++;
            if (transport === 'polling') this.results.pollingSucceeded = true;
            if (transport === 'websocket') this.results.websocketSucceeded = true;
            
            this.log(`Connected successfully via ${transport} in ${elapsed}ms`, 'success');
            this.updateStatus(`Connected (${transport})`, 'success');
            
            // Send a ping to test bidirectional communication
            this.sendPing();
        });
        
        this.socket.on('connect_error', (error) => {
            this.results.failedConnections++;
            this.results.latestError = error.message;
            
            this.log(`Connection error: ${error.message}`, 'error');
            this.updateStatus(`Connection failed: ${error.message}`, 'error');
        });
        
        this.socket.on('disconnect', (reason) => {
            this.log(`Disconnected: ${reason}`, reason === 'io client disconnect' ? 'info' : 'warning');
            this.updateStatus(`Disconnected: ${reason}`, reason === 'io client disconnect' ? 'info' : 'warning');
        });
        
        this.socket.on('pong', (data) => {
            this.log(`Received pong: ${JSON.stringify(data)}`, 'success');
        });
    }

    /**
     * Send a ping message to test bidirectional communication
     */
    sendPing() {
        if (!this.socket || !this.socket.connected) {
            this.log('Cannot send ping: Not connected', 'error');
            return;
        }
        
        const pingData = {
            timestamp: Date.now(),
            clientInfo: {
                userAgent: navigator.userAgent,
                language: navigator.language
            }
        };
        
        this.log(`Sending ping: ${JSON.stringify(pingData)}`);
        this.socket.emit('ping', pingData);
    }

    /**
     * Get a diagnostic report
     * @returns {Object} - Diagnostic results
     */
    getReport() {
        return {
            ...this.results,
            averageLatency: this.results.latency.length > 0 
                ? this.results.latency.reduce((sum, val) => sum + val, 0) / this.results.latency.length 
                : 0,
            recommendation: this._generateRecommendation()
        };
    }

    /**
     * Generate a recommendation based on test results
     * @private
     * @returns {string} - Recommendation
     */
    _generateRecommendation() {
        if (this.results.websocketSucceeded) {
            return "WebSocket transport is working correctly. This is optimal for real-time applications.";
        } else if (this.results.pollingSucceeded) {
            return "Long-polling is working, but WebSocket failed. Check network configuration, proxies, or firewalls.";
        } else {
            return "Both connection methods failed. Check server logs, network connectivity, and CORS settings.";
        }
    }
}

// Create global instance
window.socketChecker = new SocketConnectionChecker();

// Auto-initialize UI when script loads
document.addEventListener('DOMContentLoaded', () => {
    window.socketChecker.initUI();
});
