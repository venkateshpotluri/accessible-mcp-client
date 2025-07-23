/**
 * MCP Client WebSocket and API communication
 * Handles real-time communication with MCP servers
 */

(function() {
    'use strict';
    
    const MCPClient = {
        socket: null,
        isConnected: false,
        reconnectAttempts: 0,
        maxReconnectAttempts: 5,
        reconnectDelay: 1000,
        
        init: function() {
            this.setupWebSocket();
            this.setupAPIHelpers();
        },
        
        // Setup WebSocket connection
        setupWebSocket: function() {
            if (typeof io === 'undefined') {
                console.warn('Socket.IO not loaded, real-time features will be disabled');
                return;
            }
            
            try {
                this.socket = io();
                this.setupSocketEventListeners();
            } catch (error) {
                console.error('Failed to initialize WebSocket:', error);
            }
        },
        
        // Setup Socket.IO event listeners
        setupSocketEventListeners: function() {
            if (!this.socket) return;
            
            this.socket.on('connect', () => {
                console.log('Connected to WebSocket server');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.announceConnectionStatus('Connected to server');
            });
            
            this.socket.on('disconnect', (reason) => {
                console.log('Disconnected from WebSocket server:', reason);
                this.isConnected = false;
                this.announceConnectionStatus('Disconnected from server');
                
                if (reason === 'io server disconnect') {
                    // Server initiated disconnect, don't reconnect automatically
                    return;
                }
                
                // Client disconnect, try to reconnect
                this.handleReconnection();
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('WebSocket connection error:', error);
                this.handleReconnection();
            });
            
            // MCP-specific events
            this.socket.on('server_status_changed', (data) => {
                this.handleServerStatusChange(data);
            });
            
            this.socket.on('tool_execution_started', (data) => {
                this.handleToolExecutionStarted(data);
            });
            
            this.socket.on('tool_execution_completed', (data) => {
                this.handleToolExecutionCompleted(data);
            });
            
            this.socket.on('resource_updated', (data) => {
                this.handleResourceUpdated(data);
            });
            
            this.socket.on('error_occurred', (data) => {
                this.handleErrorOccurred(data);
            });
        },
        
        // Handle reconnection attempts
        handleReconnection: function() {
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                console.error('Max reconnection attempts reached');
                this.announceConnectionStatus('Connection failed, please refresh the page', 'assertive');
                return;
            }
            
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
            
            setTimeout(() => {
                console.log(`Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
                this.announceConnectionStatus(`Reconnecting... (attempt ${this.reconnectAttempts})`);
                
                if (this.socket) {
                    this.socket.connect();
                }
            }, delay);
        },
        
        // Join a server room for updates
        joinServerRoom: function(serverId) {
            if (this.socket && this.isConnected) {
                this.socket.emit('join_server', { serverId });
            }
        },
        
        // Leave a server room
        leaveServerRoom: function(serverId) {
            if (this.socket && this.isConnected) {
                this.socket.emit('leave_server', { serverId });
            }
        },
        
        // Handle server status changes
        handleServerStatusChange: function(data) {
            console.log('Server status changed:', data);
            
            // Update UI elements
            const statusElements = document.querySelectorAll(`[data-server-id="${data.serverId}"]`);
            statusElements.forEach(element => {
                this.updateServerStatusUI(element, data.status);
            });
            
            // Announce status change
            const message = `Server ${data.serverName || data.serverId} is now ${data.status}`;
            this.announceConnectionStatus(message);
            
            // Trigger custom event
            document.dispatchEvent(new CustomEvent('serverStatusChanged', {
                detail: data
            }));
        },
        
        // Handle tool execution started
        handleToolExecutionStarted: function(data) {
            console.log('Tool execution started:', data);
            
            // Show loading state
            const executionContainer = document.getElementById('execution-results');
            if (executionContainer) {
                const loadingDiv = document.createElement('div');
                loadingDiv.id = `execution-${data.executionId}`;
                loadingDiv.className = 'execution-result execution-result--loading';
                loadingDiv.innerHTML = `
                    <div class="result-header">
                        <h3 class="result-title">
                            <span class="result-icon loading-spinner" aria-hidden="true"></span>
                            ${data.toolName} - Executing...
                        </h3>
                        <time class="result-timestamp">${new Date().toLocaleString()}</time>
                    </div>
                    <div class="result-content">
                        <p>Tool execution in progress...</p>
                    </div>
                `;
                
                executionContainer.insertAdjacentElement('afterbegin', loadingDiv);
            }
            
            this.announceConnectionStatus(`Tool ${data.toolName} execution started`);
        },
        
        // Handle tool execution completed
        handleToolExecutionCompleted: function(data) {
            console.log('Tool execution completed:', data);
            
            // Update UI
            const executionElement = document.getElementById(`execution-${data.executionId}`);
            if (executionElement) {
                executionElement.className = 'execution-result execution-result--completed';
                
                const icon = executionElement.querySelector('.result-icon');
                const title = executionElement.querySelector('.result-title');
                const content = executionElement.querySelector('.result-content');
                
                if (icon) {
                    icon.className = 'result-icon';
                    icon.textContent = data.success ? '✅' : '❌';
                }
                
                if (title) {
                    title.innerHTML = `
                        <span class="result-icon" aria-hidden="true">${data.success ? '✅' : '❌'}</span>
                        ${data.toolName} - ${data.success ? 'Completed' : 'Failed'}
                    `;
                }
                
                if (content) {
                    if (data.success) {
                        content.innerHTML = `
                            <pre class="result-data"><code>${JSON.stringify(data.result, null, 2)}</code></pre>
                        `;
                    } else {
                        content.innerHTML = `
                            <div class="error-message">
                                <p><strong>Error:</strong> ${data.error}</p>
                            </div>
                        `;
                    }
                }
            }
            
            const message = data.success ? 
                `Tool ${data.toolName} completed successfully` :
                `Tool ${data.toolName} failed: ${data.error}`;
            
            this.announceConnectionStatus(message, data.success ? 'polite' : 'assertive');
        },
        
        // Handle resource updates
        handleResourceUpdated: function(data) {
            console.log('Resource updated:', data);
            
            // Trigger custom event for resource updates
            document.dispatchEvent(new CustomEvent('resourceUpdated', {
                detail: data
            }));
            
            this.announceConnectionStatus(`Resource ${data.resourceName} has been updated`);
        },
        
        // Handle errors
        handleErrorOccurred: function(data) {
            console.error('Server error:', data);
            
            // Show error notification
            this.showErrorNotification(data.message, data.details);
            
            this.announceConnectionStatus(`Error: ${data.message}`, 'assertive');
        },
        
        // Update server status UI
        updateServerStatusUI: function(element, status) {
            // Update status indicator
            const statusIndicator = element.querySelector('.status-indicator');
            if (statusIndicator) {
                statusIndicator.className = `status-indicator status-indicator--${status}`;
            }
            
            // Update status text
            const statusText = element.querySelector('.server-card__status-text');
            if (statusText) {
                statusText.textContent = status;
            }
            
            // Update buttons
            const connectBtn = element.querySelector('[onclick*="connectServer"]');
            const disconnectBtn = element.querySelector('[onclick*="disconnectServer"]');
            
            if (status === 'connected') {
                if (connectBtn) connectBtn.style.display = 'none';
                if (disconnectBtn) disconnectBtn.style.display = 'inline-flex';
            } else {
                if (connectBtn) connectBtn.style.display = 'inline-flex';
                if (disconnectBtn) disconnectBtn.style.display = 'none';
            }
        },
        
        // Show error notification
        showErrorNotification: function(message, details) {
            const notification = document.createElement('div');
            notification.className = 'flash-message flash-message--error';
            notification.setAttribute('role', 'alert');
            notification.innerHTML = `
                <span class="flash-message__icon" aria-hidden="true">❌</span>
                <div class="flash-message__text">
                    <strong>${message}</strong>
                    ${details ? `<br><small>${details}</small>` : ''}
                </div>
                <button type="button" class="flash-message__close" aria-label="Dismiss message">
                    <span aria-hidden="true">×</span>
                </button>
            `;
            
            // Add to page
            const container = document.querySelector('.flash-messages') || 
                             document.querySelector('.container');
            
            if (container) {
                container.insertAdjacentElement('afterbegin', notification);
                
                // Auto-dismiss after 10 seconds
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 10000);
                
                // Handle close button
                const closeBtn = notification.querySelector('.flash-message__close');
                if (closeBtn) {
                    closeBtn.addEventListener('click', () => {
                        notification.remove();
                    });
                }
            }
        },
        
        // API Helper methods
        setupAPIHelpers: function() {
            // Setup default headers and error handling
            this.apiHeaders = {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            };
        },
        
        // Generic API request helper
        async apiRequest(url, options = {}) {
            const defaultOptions = {
                headers: this.apiHeaders,
                credentials: 'same-origin'
            };
            
            const mergedOptions = {
                ...defaultOptions,
                ...options,
                headers: {
                    ...defaultOptions.headers,
                    ...options.headers
                }
            };
            
            try {
                const response = await fetch(url, mergedOptions);
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
                }
                
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return await response.json();
                } else {
                    return await response.text();
                }
                
            } catch (error) {
                console.error('API request failed:', error);
                throw error;
            }
        },
        
        // Server management API calls
        async getServers() {
            return this.apiRequest('/api/servers');
        },
        
        async createServer(config) {
            return this.apiRequest('/api/servers', {
                method: 'POST',
                body: JSON.stringify(config)
            });
        },
        
        async updateServer(serverId, config) {
            return this.apiRequest(`/api/servers/${serverId}`, {
                method: 'PUT',
                body: JSON.stringify(config)
            });
        },
        
        async deleteServer(serverId) {
            return this.apiRequest(`/api/servers/${serverId}`, {
                method: 'DELETE'
            });
        },
        
        async connectServer(serverId) {
            return this.apiRequest(`/api/servers/${serverId}/connect`, {
                method: 'POST'
            });
        },
        
        async disconnectServer(serverId) {
            return this.apiRequest(`/api/servers/${serverId}/disconnect`, {
                method: 'POST'
            });
        },
        
        async testServer(serverId) {
            return this.apiRequest(`/api/servers/${serverId}/test`, {
                method: 'POST'
            });
        },
        
        // MCP API calls
        async getTools(serverId) {
            return this.apiRequest(`/api/mcp/${serverId}/tools`);
        },
        
        async callTool(serverId, toolName, args) {
            return this.apiRequest(`/api/mcp/${serverId}/tools/call`, {
                method: 'POST',
                body: JSON.stringify({
                    name: toolName,
                    arguments: args
                })
            });
        },
        
        async getResources(serverId) {
            return this.apiRequest(`/api/mcp/${serverId}/resources`);
        },
        
        async readResource(serverId, uri) {
            return this.apiRequest(`/api/mcp/${serverId}/resources/read`, {
                method: 'POST',
                body: JSON.stringify({ uri })
            });
        },
        
        async getPrompts(serverId) {
            return this.apiRequest(`/api/mcp/${serverId}/prompts`);
        },
        
        async getPrompt(serverId, name, args = {}) {
            return this.apiRequest(`/api/mcp/${serverId}/prompts/get`, {
                method: 'POST',
                body: JSON.stringify({
                    name,
                    arguments: args
                })
            });
        },
        
        // Utility methods
        announceConnectionStatus: function(message, priority = 'polite') {
            if (window.MCPClientApp) {
                window.MCPClientApp.announceToUser(message, priority);
            }
        },
        
        // Get connection status
        getConnectionStatus: function() {
            return {
                websocket: this.isConnected,
                reconnectAttempts: this.reconnectAttempts
            };
        },
        
        // Cleanup method
        cleanup: function() {
            if (this.socket) {
                this.socket.disconnect();
                this.socket = null;
            }
            this.isConnected = false;
        }
    };
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => MCPClient.init());
    } else {
        MCPClient.init();
    }
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        MCPClient.cleanup();
    });
    
    // Make globally available
    window.MCPClient = MCPClient;
    
})();
