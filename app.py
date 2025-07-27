import json
import logging
import os
import re
import uuid
from datetime import datetime

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

from chat.service import ChatService
from mcp.client import MCPClient
from mcp.transport import HTTPTransport, StdioTransport, WebSocketTransport

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Set MCP module logging to INFO level
logging.getLogger("mcp.transport").setLevel(logging.INFO)
logging.getLogger("mcp.client").setLevel(logging.INFO)

logger.info("=== Flask application starting up ===")

# Constants for validation
MAX_MESSAGE_LENGTH = 10000
MAX_SESSION_TITLE_LENGTH = 200


def validate_chat_message(message: str) -> tuple[bool, str]:
    """Validate chat message input"""
    if not message or not isinstance(message, str):
        return False, "Message must be a non-empty string"

    # Strip whitespace for length check
    stripped_message = message.strip()
    if not stripped_message:
        return False, "Message cannot be empty or contain only whitespace"

    if len(message) > MAX_MESSAGE_LENGTH:
        return False, f"Message too long. Maximum length is {MAX_MESSAGE_LENGTH} characters"

    # Basic HTML/script tag detection for XSS prevention
    if re.search(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", message, re.IGNORECASE | re.DOTALL):
        return False, "Message contains potentially dangerous content"

    return True, ""


def sanitize_html_content(content: str) -> str:
    """Basic HTML sanitization for user content"""
    if not content:
        return content

    # Replace common HTML entities that could be used for XSS
    content = content.replace("&", "&amp;")  # Must be first to avoid double encoding
    content = content.replace("<", "&lt;").replace(">", "&gt;")
    content = content.replace('"', "&quot;").replace("'", "&#x27;")

    return content


class ServerConfigManager:
    """Manages persistent storage of server configurations"""

    def __init__(self, config_file="server_configs.json"):
        self.config_file = config_file

    def load_configs(self):
        """Load server configurations from file"""
        if not os.path.exists(self.config_file):
            logger.info(f"Config file {self.config_file} not found, starting with empty configuration")
            return {}

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            configs = {}
            for server_id, config_data in data.items():
                try:
                    configs[server_id] = ServerConfig.from_dict(config_data)
                except Exception as e:
                    logger.warning(f"Failed to load server config {server_id}: {e}")
                    continue

            logger.info(f"Loaded {len(configs)} server configurations from {self.config_file}")
            return configs

        except Exception as e:
            logger.error(f"Failed to load config file {self.config_file}: {e}")
            return {}

    def save_configs(self, configs):
        """Save server configurations to file"""
        try:
            # Convert ServerConfig objects to dictionaries
            data = {}
            for server_id, config in configs.items():
                # Don't save the status field (runtime state)
                config_dict = config.to_dict()
                config_dict.pop("status", None)  # Remove status from saved data
                data[server_id] = config_dict

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(configs)} server configurations to {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config file {self.config_file}: {e}")
            return False


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize configuration manager
config_manager = ServerConfigManager()

# Initialize chat service
chat_service = ChatService()

# Store active MCP clients
active_clients = {}

# Server configurations will be loaded after class definitions
server_configs = {}


class ServerConfig:
    def __init__(self, name, transport_type, config, server_id=None, auto_connect=False):
        self.id = server_id or str(uuid.uuid4())
        self.name = name
        self.transport_type = transport_type
        self.config = config
        self.auto_connect = auto_connect
        self.created_at = datetime.now()
        self.status = "disconnected"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "transport_type": self.transport_type,
            "config": self.config,
            "auto_connect": self.auto_connect,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data):
        """Create ServerConfig from dictionary data"""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            # Parse ISO format datetime string
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                created_at = datetime.now()

        instance = cls(
            name=data["name"],
            transport_type=data["transport_type"],
            config=data["config"],
            server_id=data["id"],
            auto_connect=data.get("auto_connect", False),
        )

        if created_at:
            instance.created_at = created_at

        return instance


# Load server configurations from persistent storage now that ServerConfig is defined
server_configs.update(config_manager.load_configs())

# Set up chat service with MCP clients reference
chat_service.set_mcp_clients(active_clients)


def auto_connect_servers():
    """Auto-connect to servers that have auto_connect enabled"""
    for server_id, server_config in server_configs.items():
        if server_config.auto_connect:
            try:
                logger.info(f"Auto-connecting to server: {server_config.name} ({server_id})")

                # Create transport based on type
                transport = None
                if server_config.transport_type == "stdio":
                    transport = StdioTransport(
                        command=server_config.config.get("command", ""),
                        args=server_config.config.get("args", []),
                        cwd=server_config.config.get("cwd"),
                    )
                elif server_config.transport_type == "http":
                    transport = HTTPTransport(
                        url=server_config.config.get("url", ""),
                        headers=server_config.config.get("headers", {}),
                        timeout=server_config.config.get("timeout", 30),
                    )
                elif server_config.transport_type == "websocket":
                    transport = WebSocketTransport(
                        url=server_config.config.get("url", ""),
                        protocols=server_config.config.get("protocols", []),
                        headers=server_config.config.get("headers", {}),
                    )
                else:
                    logger.error(f"Invalid transport type for server {server_id}: {server_config.transport_type}")
                    continue

                # Create and connect MCP client
                client = MCPClient(transport)
                client.connect()

                # Initialize MCP session
                client.initialize(
                    {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}, "resources": {}},
                        "clientInfo": {"name": "Accessible MCP Client", "version": "1.0.0"},
                    }
                )

                active_clients[server_id] = client
                server_config.status = "connected"
                logger.info(f"Successfully auto-connected to server: {server_config.name}")

            except Exception as e:
                logger.error(f"Failed to auto-connect to server {server_config.name}: {e}")
                server_config.status = "error"


# Auto-connect to servers on startup
auto_connect_servers()


@app.route("/")
def index():
    """Main application interface"""
    return render_template("index.html")


@app.route("/chat")
def chat():
    """Chat interface page"""
    return render_template("chat.html")


@app.route("/connections")
def connections():
    """Server connections management page"""
    return render_template("connections.html")


@app.route("/help")
def help_page():
    """Help and documentation page"""
    return render_template("help.html")


# API Routes


@app.route("/api/servers", methods=["GET"])
def get_servers():
    """Get all configured servers"""
    return jsonify([config.to_dict() for config in server_configs.values()])


@app.route("/api/servers", methods=["POST"])
def create_server():
    """Create a new server configuration"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["name", "transport_type", "config"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Create server configuration
        server_config = ServerConfig(
            name=data["name"],
            transport_type=data["transport_type"],
            config=data["config"],
            auto_connect=data.get("auto_connect", False),
        )

        server_configs[server_config.id] = server_config

        # Save to persistent storage
        if not config_manager.save_configs(server_configs):
            logger.warning("Failed to save server configuration to file")

        return jsonify(server_config.to_dict()), 201

    except Exception as e:
        logger.error(f"Error creating server: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/servers/<server_id>", methods=["PUT"])
def update_server(server_id):
    """Update server configuration"""
    try:
        if server_id not in server_configs:
            return jsonify({"error": "Server not found"}), 404

        data = request.get_json()
        server_config = server_configs[server_id]

        # Update fields if provided
        if "name" in data:
            server_config.name = data["name"]
        if "transport_type" in data:
            server_config.transport_type = data["transport_type"]
        if "config" in data:
            server_config.config = data["config"]
        if "auto_connect" in data:
            server_config.auto_connect = data["auto_connect"]

        # Save to persistent storage
        if not config_manager.save_configs(server_configs):
            logger.warning("Failed to save server configuration to file")

        return jsonify(server_config.to_dict())

    except Exception as e:
        logger.error(f"Error updating server: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/servers/<server_id>", methods=["DELETE"])
def delete_server(server_id):
    """Delete server configuration"""
    try:
        if server_id not in server_configs:
            return jsonify({"error": "Server not found"}), 404

        # Disconnect if connected
        if server_id in active_clients:
            active_clients[server_id].disconnect()
            del active_clients[server_id]

        del server_configs[server_id]

        # Save to persistent storage
        if not config_manager.save_configs(server_configs):
            logger.warning("Failed to save server configuration to file")

        return jsonify({"message": "Server deleted successfully"})

    except Exception as e:
        logger.error(f"Error deleting server: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/servers/<server_id>/connect", methods=["POST"])
def connect_server(server_id):
    """Connect to an MCP server"""
    try:
        if server_id not in server_configs:
            return jsonify({"error": "Server not found"}), 404

        server_config = server_configs[server_id]

        # Create transport based on type
        transport = None
        if server_config.transport_type == "stdio":
            transport = StdioTransport(
                command=server_config.config.get("command", ""),
                args=server_config.config.get("args", []),
                cwd=server_config.config.get("cwd"),
            )
        elif server_config.transport_type == "http":
            transport = HTTPTransport(
                url=server_config.config.get("url", ""),
                headers=server_config.config.get("headers", {}),
                timeout=server_config.config.get("timeout", 30),
            )
        elif server_config.transport_type == "websocket":
            transport = WebSocketTransport(
                url=server_config.config.get("url", ""),
                protocols=server_config.config.get("protocols", []),
                headers=server_config.config.get("headers", {}),
            )
        else:
            return jsonify({"error": "Invalid transport type"}), 400

        # Create and connect MCP client
        client = MCPClient(transport)
        client.connect()

        # Initialize MCP session
        init_result = client.initialize(
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}},
                "clientInfo": {"name": "Accessible MCP Client", "version": "1.0.0"},
            }
        )

        active_clients[server_id] = client
        server_config.status = "connected"

        return jsonify({"message": "Connected successfully", "server_info": init_result})

    except Exception as e:
        logger.error(f"Error connecting to server: {e}")
        server_configs[server_id].status = "error"
        return jsonify({"error": str(e)}), 500


@app.route("/api/servers/<server_id>/disconnect", methods=["POST"])
def disconnect_server(server_id):
    """Disconnect from an MCP server"""
    try:
        if server_id not in active_clients:
            return jsonify({"error": "Server not connected"}), 400

        active_clients[server_id].disconnect()
        del active_clients[server_id]

        if server_id in server_configs:
            server_configs[server_id].status = "disconnected"

        return jsonify({"message": "Disconnected successfully"})

    except Exception as e:
        logger.error(f"Error disconnecting from server: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/servers/<server_id>/test", methods=["POST"])
def test_connection(server_id):
    """Test connection to an MCP server without saving state"""
    try:
        if server_id not in server_configs:
            return jsonify({"error": "Server not found"}), 404

        server_config = server_configs[server_id]

        # Create temporary transport for testing
        transport = None
        if server_config.transport_type == "stdio":
            transport = StdioTransport(
                command=server_config.config.get("command", ""),
                args=server_config.config.get("args", []),
                cwd=server_config.config.get("cwd"),
            )
        elif server_config.transport_type == "http":
            transport = HTTPTransport(
                url=server_config.config.get("url", ""),
                headers=server_config.config.get("headers", {}),
                timeout=server_config.config.get("timeout", 30),
            )
        elif server_config.transport_type == "websocket":
            transport = WebSocketTransport(
                url=server_config.config.get("url", ""),
                protocols=server_config.config.get("protocols", []),
                headers=server_config.config.get("headers", {}),
            )

        # Test connection
        test_client = MCPClient(transport)
        test_client.connect()

        result = test_client.initialize(
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}},
                "clientInfo": {"name": "Accessible MCP Client (Test)", "version": "1.0.0"},
            }
        )

        test_client.disconnect()

        return jsonify({"status": "success", "message": "Connection test successful", "server_info": result})

    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Chat API Routes


@app.route("/api/chat/sessions", methods=["GET"])
def list_chat_sessions():
    """List all chat sessions"""
    try:
        sessions = chat_service.list_sessions()
        return jsonify(sessions)
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/sessions", methods=["POST"])
def create_chat_session():
    """Create a new chat session"""
    try:
        data = request.get_json() or {}
        title = data.get("title")

        # Validate title if provided
        if title is not None:
            if not isinstance(title, str):
                return jsonify({"error": "Title must be a string"}), 400
            if len(title) > MAX_SESSION_TITLE_LENGTH:
                return jsonify({"error": f"Title too long. Maximum length is {MAX_SESSION_TITLE_LENGTH} characters"}), 400

            # Sanitize title
            title = sanitize_html_content(title.strip()) or None

        session = chat_service.create_session(title=title)
        return jsonify(session.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        return jsonify({"error": "An internal error occurred while creating the session"}), 500


@app.route("/api/chat/sessions/<session_id>", methods=["GET"])
def get_chat_session(session_id):
    """Get a chat session"""
    try:
        session = chat_service.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        return jsonify(session.to_dict())
    except Exception as e:
        logger.error(f"Error getting chat session: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/sessions/<session_id>", methods=["DELETE"])
def delete_chat_session(session_id):
    """Delete a chat session"""
    try:
        success = chat_service.delete_session(session_id)
        if not success:
            return jsonify({"error": "Session not found"}), 404

        return jsonify({"message": "Session deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/sessions/<session_id>/messages", methods=["POST"])
def send_chat_message(session_id):
    """Send a message to a chat session"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be valid JSON"}), 400

        if "message" not in data:
            return jsonify({"error": "Message is required"}), 400

        user_message = data["message"]
        server_ids = data.get("server_ids", [])

        # Validate message content
        is_valid, error_msg = validate_chat_message(user_message)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        # Sanitize the message
        user_message = sanitize_html_content(user_message)

        # Validate server_ids format
        if server_ids and not isinstance(server_ids, list):
            return jsonify({"error": "server_ids must be a list"}), 400

        # Validate server IDs exist and are connected
        if server_ids:
            for server_id in server_ids:
                if not isinstance(server_id, str):
                    return jsonify({"error": "All server IDs must be strings"}), 400
                if server_id not in active_clients:
                    return jsonify({"error": f"Server {server_id} not connected"}), 400

        response_message = chat_service.send_message(session_id, user_message, server_ids)
        return jsonify(response_message.to_dict())

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error sending chat message: {e}")
        return jsonify({"error": "An internal error occurred while processing your message"}), 500


# MCP Protocol API Routes


@app.route("/api/mcp/<server_id>/tools", methods=["GET"])
def list_tools(server_id):
    """List available tools from MCP server"""
    try:
        if server_id not in active_clients:
            return jsonify({"error": "Server not connected"}), 400

        client = active_clients[server_id]
        tools = client.list_tools()

        return jsonify(tools)

    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/mcp/<server_id>/tools/call", methods=["POST"])
def call_tool(server_id):
    """Call a tool on the MCP server"""
    try:
        if server_id not in active_clients:
            return jsonify({"error": "Server not connected"}), 400

        data = request.get_json()
        if "name" not in data:
            return jsonify({"error": "Tool name is required"}), 400

        client = active_clients[server_id]
        result = client.call_tool(name=data["name"], arguments=data.get("arguments", {}))

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error calling tool: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/mcp/<server_id>/resources", methods=["GET"])
def list_resources(server_id):
    """List available resources from MCP server"""
    try:
        if server_id not in active_clients:
            return jsonify({"error": "Server not connected"}), 400

        client = active_clients[server_id]
        resources = client.list_resources()

        return jsonify(resources)

    except Exception as e:
        logger.error(f"Error listing resources: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/mcp/<server_id>/resources/read", methods=["POST"])
def read_resource(server_id):
    """Read a resource from the MCP server"""
    try:
        if server_id not in active_clients:
            return jsonify({"error": "Server not connected"}), 400

        data = request.get_json()
        if "uri" not in data:
            return jsonify({"error": "Resource URI is required"}), 400

        client = active_clients[server_id]
        result = client.read_resource(uri=data["uri"])

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error reading resource: {e}")
        return jsonify({"error": str(e)}), 500


# WebSocket Events


@socketio.on("connect")
def handle_connect():
    """Handle WebSocket connection"""
    logger.info(f"Client connected: {request.sid}")
    emit("status", {"message": "Connected to MCP client"})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info(f"Client disconnected: {request.sid}")


@socketio.on("join_server")
def handle_join_server(data):
    """Join a server room for real-time updates"""
    server_id = data.get("server_id")
    if server_id:
        join_room(f"server_{server_id}")
        emit("status", {"message": f"Joined server {server_id}"})


@socketio.on("leave_server")
def handle_leave_server(data):
    """Leave a server room"""
    server_id = data.get("server_id")
    if server_id:
        leave_room(f"server_{server_id}")
        emit("status", {"message": f"Left server {server_id}"})


# Error Handlers


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return render_template("500.html"), 500


# Health Check


@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_servers": len(active_clients),
            "configured_servers": len(server_configs),
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"

    socketio.run(app, host="0.0.0.0", port=port, debug=debug)
