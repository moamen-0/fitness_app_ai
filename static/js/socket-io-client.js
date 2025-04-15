/**
 * Enhanced Socket.IO client for Google Cloud App Engine
 * Provides reliable connections with automatic fallback
 */
class AppEngineSocketClient {
    constructor() {
        this.socket = null;
        this.eventHandlers = {};
        this.isConnected = false;
        this.connectionMode = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    /**
     * Connect to the server with optimal settings for App Engine
     * @param {string} url - Optional server URL, defaults to current host
     * @param {Object} options - Optional configuration
     * @returns {Object} - The socket instance
     */
    connect(url, options = {}) {
        // Clean up any existing connection
        if (this.socket) {
            this.disconnect();
        }
        
        // Set default URL if not provided
        const serverUrl = url || window.location.origin;
        console.log(`Connecting to: ${serverUrl}`);
        
        // Configure with App Engine optimized settings
        const defaultOptions = {
            transports: ['polling', 'websocket'], // Start with polling for compatibility
            upgrade: true,                        // Try to upgrade to WebSocket
            reconnection: true,
            reconnectionAttempts: this.maxReconnectAttempts,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            timeout: 20000,
            forceNew: true
        };
        
        // Merge with user options
        const connectionOptions = {...defaultOptions, ...options};
        console.log("Connection options:", connectionOptions);
        
        try {
            // Create socket connection
            this.socket = io(serverUrl, connectionOptions);
            
            // Set up core event handlers
            this._setupCoreEventHandlers();
            
            // Re-attach any user event handlers
            this._reattachEventHandlers();
            
            return this.socket;
        } catch (error) {
            console.error("Socket connection error:", error);
            this._triggerEvent('connect_error', error);
            return null;
        }
    }
    
    /**
     * Set up core event handlers for the socket
     * @private
     */
    _setupCoreEventHandlers() {
        if (!this.socket) return;
        
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.connectionMode = this.socket.io.engine.transport.name;
            console.log(`Connected via ${this.connectionMode}`);
            this._triggerEvent('connect', {
                id: this.socket.id,
                transport: this.connectionMode
            });
            
            // Check for transport upgrade
            this.socket.io.engine.on('upgrade', () => {
                this.connectionMode = this.socket.io.engine.transport.name;
                console.log(`Transport upgraded to: ${this.connectionMode}`);
                this._triggerEvent('transport_change', {
                    transport: this.connectionMode
                });
            });
        });
        
        this.socket.on('connect_error', (error) => {
            console.error("Connection error:", error);
            this.reconnectAttempts++;
            this._triggerEvent('connect_error', error);
            
            // If we're maxed out on reconnect attempts and not connected
            if (this.reconnectAttempts >= this.maxReconnectAttempts && !this.isConnected) {
                console.log(`Max reconnect attempts (${this.maxReconnectAttempts}) reached, giving up`);
                this._triggerEvent('max_reconnect_attempts', {
                    attempts: this.reconnectAttempts
                });
            }
        });
        
        this.socket.on('disconnect', (reason) => {
            this.isConnected = false;
            console.log(`Disconnected: ${reason}`);
            this._triggerEvent('disconnect', {reason});
            
            // If the server forcibly closed the connection, we should not reconnect
            if (reason === 'io server disconnect') {
                console.log('Server forcibly disconnected the client');
            }
        });
        
        this.socket.on('error', (error) => {
            console.error("Socket error:", error);
            this._triggerEvent('error', error);
        });
    }
    
    /**
     * Register an event handler
     * @param {string} event - Event name
     * @param {Function} callback - Event handler
     */
    on(event, callback) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        
        this.eventHandlers[event].push(callback);
        
        // If socket exists, attach the handler directly
        if (this.socket) {
            this.socket.on(event, callback);
        }
        
        return this; // Allow chaining
    }
    
    /**
     * Send an event to the server
     * @param {string} event - Event name
     * @param {any} data - Event data
     * @returns {boolean} - True if sent, false otherwise
     */
    emit(event, data) {
        if (!this.socket || !this.isConnected) {
            console.warn(`Cannot emit event '${event}': Not connected`);
            return false;
        }
        
        try {
            this.socket.emit(event, data);
            return true;
        } catch (error) {
            console.error(`Error emitting event '${event}':`, error);
            return false;
        }
    }
    
    /**
     * Disconnect from the server
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        
        this.isConnected = false;
        console.log('Disconnected from server');
    }
    
    /**
     * Get current connection status
     * @returns {Object} - Connection status information
     */
    getStatus() {
        return {
            connected: this.isConnected,
            transport: this.connectionMode,
            socketId: this.socket ? this.socket.id : null,
            reconnectAttempts: this.reconnectAttempts
        };
    }
    
    /**
     * Re-attach stored event handlers to a new socket
     * @private
     */
    _reattachEventHandlers() {
        if (!this.socket) return;
        
        // Attach all stored event handlers
        Object.keys(this.eventHandlers).forEach(event => {
            this.eventHandlers[event].forEach(callback => {
                this.socket.on(event, callback);
            });
        });
    }
    
    /**
     * Trigger registered event handlers
     * @private
     */
    _triggerEvent(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${event} handler:`, error);
                }
            });
        }
    }
}

// Create global instance
window.socketClient = new AppEngineSocketClient();
