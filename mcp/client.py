"""
MCP Client implementation
"""
import json
import uuid
import threading
import time
from typing import Dict, Any, Optional, List, Callable
import logging

from .protocol import (
    MCPMessage, MCPRequest, MCPResponse, MCPNotification, MCPError,
    MCPCapabilities, MCPTool, MCPResource, MCPPrompt,
    validate_message, validate_capabilities, validate_tool_call
)
from .transport import MCPTransport

logger = logging.getLogger(__name__)

class MCPClient:
    """MCP (Model Context Protocol) client implementation"""
    
    def __init__(self, transport: MCPTransport):
        self.transport = transport
        self.request_id_counter = 0
        self.pending_requests: Dict[str, threading.Event] = {}
        self.request_responses: Dict[str, Dict[str, Any]] = {}
        self.server_capabilities: Optional[Dict[str, Any]] = None
        self.client_capabilities = MCPCapabilities()
        self.initialized = False
        self.lock = threading.Lock()
        
        # Set up message handling
        self.transport.set_message_handler(self._handle_message)
    
    def connect(self) -> None:
        """Connect to MCP server"""
        self.transport.connect()
    
    def disconnect(self) -> None:
        """Disconnect from MCP server"""
        self.transport.disconnect()
        self.initialized = False
    
    def initialize(self, client_info: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize MCP session with server"""
        try:
            # Send initialize request
            params = {
                'protocolVersion': '2024-11-05',
                'capabilities': self.client_capabilities.to_dict(),
                'clientInfo': client_info
            }
            
            response = self._send_request('initialize', params)
            
            if 'error' in response:
                raise MCPError(
                    response['error']['code'],
                    response['error']['message'],
                    response['error'].get('data')
                )
            
            result = response.get('result', {})
            
            # Store server capabilities
            self.server_capabilities = result.get('capabilities', {})
            
            # Send initialized notification
            self._send_notification('initialized', {})
            
            self.initialized = True
            
            logger.info("MCP session initialized successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP session: {e}")
            raise
    
    def list_tools(self) -> Dict[str, Any]:
        """List available tools from MCP server"""
        if not self.initialized:
            raise RuntimeError("MCP client not initialized")
        
        try:
            response = self._send_request('tools/list', {})
            
            if 'error' in response:
                raise MCPError(
                    response['error']['code'],
                    response['error']['message'],
                    response['error'].get('data')
                )
            
            return response.get('result', {})
            
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            raise
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        if not self.initialized:
            raise RuntimeError("MCP client not initialized")
        
        try:
            # Validate parameters
            validate_tool_call(name, arguments)
            
            params = {
                'name': name,
                'arguments': arguments
            }
            
            response = self._send_request('tools/call', params)
            
            if 'error' in response:
                raise MCPError(
                    response['error']['code'],
                    response['error']['message'],
                    response['error'].get('data')
                )
            
            return response.get('result', {})
            
        except Exception as e:
            logger.error(f"Failed to call tool {name}: {e}")
            raise
    
    def list_resources(self) -> Dict[str, Any]:
        """List available resources from MCP server"""
        if not self.initialized:
            raise RuntimeError("MCP client not initialized")
        
        try:
            response = self._send_request('resources/list', {})
            
            if 'error' in response:
                raise MCPError(
                    response['error']['code'],
                    response['error']['message'],
                    response['error'].get('data')
                )
            
            return response.get('result', {})
            
        except Exception as e:
            logger.error(f"Failed to list resources: {e}")
            raise
    
    def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource from the MCP server"""
        if not self.initialized:
            raise RuntimeError("MCP client not initialized")
        
        try:
            params = {'uri': uri}
            response = self._send_request('resources/read', params)
            
            if 'error' in response:
                raise MCPError(
                    response['error']['code'],
                    response['error']['message'],
                    response['error'].get('data')
                )
            
            return response.get('result', {})
            
        except Exception as e:
            logger.error(f"Failed to read resource {uri}: {e}")
            raise
    
    def list_prompts(self) -> Dict[str, Any]:
        """List available prompts from MCP server"""
        if not self.initialized:
            raise RuntimeError("MCP client not initialized")
        
        try:
            response = self._send_request('prompts/list', {})
            
            if 'error' in response:
                raise MCPError(
                    response['error']['code'],
                    response['error']['message'],
                    response['error'].get('data')
                )
            
            return response.get('result', {})
            
        except Exception as e:
            logger.error(f"Failed to list prompts: {e}")
            raise
    
    def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get a prompt from the MCP server"""
        if not self.initialized:
            raise RuntimeError("MCP client not initialized")
        
        try:
            params = {'name': name}
            if arguments:
                params['arguments'] = arguments
            
            response = self._send_request('prompts/get', params)
            
            if 'error' in response:
                raise MCPError(
                    response['error']['code'],
                    response['error']['message'],
                    response['error'].get('data')
                )
            
            return response.get('result', {})
            
        except Exception as e:
            logger.error(f"Failed to get prompt {name}: {e}")
            raise
    
    def _send_request(self, method: str, params: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """Send a request and wait for response"""
        request_id = self._generate_request_id()
        
        # Create request message
        request = MCPRequest(method, params, request_id)
        
        try:
            # Send request - check if transport returns response directly (HTTP) or async (WebSocket/stdio)
            result = self.transport.send_message(request.to_dict())
            
            # If transport returned a response directly (HTTP transport), return it
            if result is not None and isinstance(result, dict):
                return result
            
            # Otherwise, use async pattern for WebSocket/stdio transports
            # Set up response waiting
            with self.lock:
                event = threading.Event()
                self.pending_requests[request_id] = event
            
            try:
                # Wait for response
                if event.wait(timeout):
                    with self.lock:
                        response = self.request_responses.pop(request_id, {})
                        return response
                else:
                    raise TimeoutError(f"Request {request_id} timed out after {timeout} seconds")
                    
            finally:
                # Clean up
                with self.lock:
                    self.pending_requests.pop(request_id, None)
                    self.request_responses.pop(request_id, None)
                    
        except Exception as e:
            logger.error(f"Error sending request {request_id}: {e}")
            raise
    
    def _send_notification(self, method: str, params: Dict[str, Any]) -> None:
        """Send a notification (no response expected)"""
        notification = MCPNotification(method, params)
        
        # For HTTP transport, check if we should skip certain notifications
        # since HTTP is stateless and doesn't maintain persistent connections
        if hasattr(self.transport, 'session') and method == 'initialized':
            # Skip 'initialized' notification for HTTP transport as it's not needed
            # for stateless HTTP connections
            logger.debug(f"Skipping '{method}' notification for HTTP transport")
            return
            
        result = self.transport.send_message(notification.to_dict())
        
        # HTTP transport might return a response even for notifications
        if result is not None:
            logger.debug(f"Notification '{method}' received response: {result}")
        else:
            logger.debug(f"Sent notification '{method}' (no response expected)")
    
    def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming message from server"""
        try:
            # Validate message format
            validate_message(message)
            
            # Handle response messages
            if 'id' in message and ('result' in message or 'error' in message):
                self._handle_response(message)
            
            # Handle notification messages
            elif 'method' in message and 'id' not in message:
                self._handle_notification(message)
            
            # Handle request messages (if server sends any)
            elif 'method' in message and 'id' in message:
                self._handle_request(message)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def _handle_response(self, message: Dict[str, Any]) -> None:
        """Handle response message"""
        request_id = message.get('id')
        
        with self.lock:
            if request_id in self.pending_requests:
                # Store response
                self.request_responses[request_id] = message
                
                # Signal waiting thread
                event = self.pending_requests[request_id]
                event.set()
    
    def _handle_notification(self, message: Dict[str, Any]) -> None:
        """Handle notification message"""
        method = message.get('method')
        params = message.get('params', {})
        
        logger.info(f"Received notification: {method}")
        
        # Handle specific notifications
        if method == 'progress':
            self._handle_progress_notification(params)
        elif method == 'logging':
            self._handle_logging_notification(params)
        else:
            logger.debug(f"Unhandled notification: {method}")
    
    def _handle_request(self, message: Dict[str, Any]) -> None:
        """Handle request message from server"""
        method = message.get('method')
        params = message.get('params', {})
        request_id = message.get('id')
        
        logger.info(f"Received request: {method}")
        
        # For now, respond with method not found
        # This can be extended to support server-to-client requests
        error_response = MCPResponse(
            request_id,
            error=MCPError(MCPError.METHOD_NOT_FOUND, f"Method {method} not supported")
        )
        
        self.transport.send_message(error_response.to_dict())
    
    def _handle_progress_notification(self, params: Dict[str, Any]) -> None:
        """Handle progress notification"""
        logger.info(f"Progress: {params}")
    
    def _handle_logging_notification(self, params: Dict[str, Any]) -> None:
        """Handle logging notification"""
        level = params.get('level', 'info')
        message = params.get('message', '')
        
        if level == 'error':
            logger.error(f"Server: {message}")
        elif level == 'warning':
            logger.warning(f"Server: {message}")
        else:
            logger.info(f"Server: {message}")
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        with self.lock:
            self.request_id_counter += 1
            return f"req_{self.request_id_counter}_{uuid.uuid4().hex[:8]}"
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and capabilities"""
        return {
            'capabilities': self.server_capabilities,
            'initialized': self.initialized,
            'connected': self.transport.connected
        }
