from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import uuid
import logging
import os
from datetime import datetime
from mcp.client import MCPClient
from mcp.transport import StdioTransport, HTTPTransport, WebSocketTransport
from mcp.protocol import MCPError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set MCP module logging to INFO level
logging.getLogger('mcp.transport').setLevel(logging.INFO)
logging.getLogger('mcp.client').setLevel(logging.INFO)

logger.info("=== Flask application starting up ===")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active MCP clients
active_clients = {}
server_configs = {}

class ServerConfig:
    def __init__(self, name, transport_type, config, server_id=None):
        self.id = server_id or str(uuid.uuid4())
        self.name = name
        self.transport_type = transport_type
        self.config = config
        self.created_at = datetime.now()
        self.status = 'disconnected'
        
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'transport_type': self.transport_type,
            'config': self.config,
            'created_at': self.created_at.isoformat(),
            'status': self.status
        }

@app.route('/')
def index():
    """Main application interface"""
    return render_template('index.html')

@app.route('/connections')
def connections():
    """Server connections management page"""
    return render_template('connections.html')

@app.route('/help')
def help_page():
    """Help and documentation page"""
    return render_template('help.html')

# API Routes

@app.route('/api/servers', methods=['GET'])
def get_servers():
    """Get all configured servers"""
    return jsonify([config.to_dict() for config in server_configs.values()])

@app.route('/api/servers', methods=['POST'])
def create_server():
    """Create a new server configuration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'transport_type', 'config']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create server configuration
        server_config = ServerConfig(
            name=data['name'],
            transport_type=data['transport_type'],
            config=data['config']
        )
        
        server_configs[server_config.id] = server_config
        
        return jsonify(server_config.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating server: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<server_id>', methods=['PUT'])
def update_server(server_id):
    """Update server configuration"""
    try:
        if server_id not in server_configs:
            return jsonify({'error': 'Server not found'}), 404
        
        data = request.get_json()
        server_config = server_configs[server_id]
        
        # Update fields if provided
        if 'name' in data:
            server_config.name = data['name']
        if 'transport_type' in data:
            server_config.transport_type = data['transport_type']
        if 'config' in data:
            server_config.config = data['config']
        
        return jsonify(server_config.to_dict())
        
    except Exception as e:
        logger.error(f"Error updating server: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<server_id>', methods=['DELETE'])
def delete_server(server_id):
    """Delete server configuration"""
    try:
        if server_id not in server_configs:
            return jsonify({'error': 'Server not found'}), 404
        
        # Disconnect if connected
        if server_id in active_clients:
            active_clients[server_id].disconnect()
            del active_clients[server_id]
        
        del server_configs[server_id]
        
        return jsonify({'message': 'Server deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting server: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<server_id>/connect', methods=['POST'])
def connect_server(server_id):
    """Connect to an MCP server"""
    try:
        if server_id not in server_configs:
            return jsonify({'error': 'Server not found'}), 404
        
        server_config = server_configs[server_id]
        
        # Create transport based on type
        transport = None
        if server_config.transport_type == 'stdio':
            transport = StdioTransport(
                command=server_config.config.get('command', ''),
                args=server_config.config.get('args', []),
                cwd=server_config.config.get('cwd')
            )
        elif server_config.transport_type == 'http':
            transport = HTTPTransport(
                url=server_config.config.get('url', ''),
                headers=server_config.config.get('headers', {}),
                timeout=server_config.config.get('timeout', 30)
            )
        elif server_config.transport_type == 'websocket':
            transport = WebSocketTransport(
                url=server_config.config.get('url', ''),
                protocols=server_config.config.get('protocols', []),
                headers=server_config.config.get('headers', {})
            )
        else:
            return jsonify({'error': 'Invalid transport type'}), 400
        
        # Create and connect MCP client
        client = MCPClient(transport)
        client.connect()
        
        # Initialize MCP session
        init_result = client.initialize({
            'protocolVersion': '2024-11-05',
            'capabilities': {
                'tools': {},
                'resources': {}
            },
            'clientInfo': {
                'name': 'Accessible MCP Client',
                'version': '1.0.0'
            }
        })
        
        active_clients[server_id] = client
        server_config.status = 'connected'
        
        return jsonify({
            'message': 'Connected successfully',
            'server_info': init_result
        })
        
    except Exception as e:
        logger.error(f"Error connecting to server: {e}")
        server_configs[server_id].status = 'error'
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<server_id>/disconnect', methods=['POST'])
def disconnect_server(server_id):
    """Disconnect from an MCP server"""
    try:
        if server_id not in active_clients:
            return jsonify({'error': 'Server not connected'}), 400
        
        active_clients[server_id].disconnect()
        del active_clients[server_id]
        
        if server_id in server_configs:
            server_configs[server_id].status = 'disconnected'
        
        return jsonify({'message': 'Disconnected successfully'})
        
    except Exception as e:
        logger.error(f"Error disconnecting from server: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<server_id>/test', methods=['POST'])
def test_connection(server_id):
    """Test connection to an MCP server without saving state"""
    try:
        if server_id not in server_configs:
            return jsonify({'error': 'Server not found'}), 404
        
        server_config = server_configs[server_id]
        
        # Create temporary transport for testing
        transport = None
        if server_config.transport_type == 'stdio':
            transport = StdioTransport(
                command=server_config.config.get('command', ''),
                args=server_config.config.get('args', []),
                cwd=server_config.config.get('cwd')
            )
        elif server_config.transport_type == 'http':
            transport = HTTPTransport(
                url=server_config.config.get('url', ''),
                headers=server_config.config.get('headers', {}),
                timeout=server_config.config.get('timeout', 30)
            )
        elif server_config.transport_type == 'websocket':
            transport = WebSocketTransport(
                url=server_config.config.get('url', ''),
                protocols=server_config.config.get('protocols', []),
                headers=server_config.config.get('headers', {})
            )
        
        # Test connection
        test_client = MCPClient(transport)
        test_client.connect()
        
        result = test_client.initialize({
            'protocolVersion': '2024-11-05',
            'capabilities': {
                'tools': {},
                'resources': {}
            },
            'clientInfo': {
                'name': 'Accessible MCP Client (Test)',
                'version': '1.0.0'
            }
        })
        
        test_client.disconnect()
        
        return jsonify({
            'status': 'success',
            'message': 'Connection test successful',
            'server_info': result
        })
        
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# MCP Protocol API Routes

@app.route('/api/mcp/<server_id>/tools', methods=['GET'])
def list_tools(server_id):
    """List available tools from MCP server"""
    try:
        if server_id not in active_clients:
            return jsonify({'error': 'Server not connected'}), 400
        
        client = active_clients[server_id]
        tools = client.list_tools()
        
        return jsonify(tools)
        
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/<server_id>/tools/call', methods=['POST'])
def call_tool(server_id):
    """Call a tool on the MCP server"""
    try:
        if server_id not in active_clients:
            return jsonify({'error': 'Server not connected'}), 400
        
        data = request.get_json()
        if 'name' not in data:
            return jsonify({'error': 'Tool name is required'}), 400
        
        client = active_clients[server_id]
        result = client.call_tool(
            name=data['name'],
            arguments=data.get('arguments', {})
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error calling tool: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/<server_id>/resources', methods=['GET'])
def list_resources(server_id):
    """List available resources from MCP server"""
    try:
        if server_id not in active_clients:
            return jsonify({'error': 'Server not connected'}), 400
        
        client = active_clients[server_id]
        resources = client.list_resources()
        
        return jsonify(resources)
        
    except Exception as e:
        logger.error(f"Error listing resources: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/<server_id>/resources/read', methods=['POST'])
def read_resource(server_id):
    """Read a resource from the MCP server"""
    try:
        if server_id not in active_clients:
            return jsonify({'error': 'Server not connected'}), 400
        
        data = request.get_json()
        if 'uri' not in data:
            return jsonify({'error': 'Resource URI is required'}), 400
        
        client = active_clients[server_id]
        result = client.read_resource(uri=data['uri'])
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error reading resource: {e}")
        return jsonify({'error': str(e)}), 500

# WebSocket Events

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('status', {'message': 'Connected to MCP client'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_server')
def handle_join_server(data):
    """Join a server room for real-time updates"""
    server_id = data.get('server_id')
    if server_id:
        join_room(f"server_{server_id}")
        emit('status', {'message': f'Joined server {server_id}'})

@socketio.on('leave_server')
def handle_leave_server(data):
    """Leave a server room"""
    server_id = data.get('server_id')
    if server_id:
        leave_room(f"server_{server_id}")
        emit('status', {'message': f'Left server {server_id}'})

# Error Handlers

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return render_template('500.html'), 500

# Health Check

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_servers': len(active_clients),
        'configured_servers': len(server_configs)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug
    )
