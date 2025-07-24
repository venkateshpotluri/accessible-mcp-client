import pytest

from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def app_context():
    """Create an application context for testing."""
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    with app.app_context():
        yield app


class TestFlaskApp:
    """Test cases for the main Flask application."""

    def test_app_creation(self, app_context):
        """Test that the Flask app is created successfully."""
        assert app_context is not None
        assert app_context.config["TESTING"] is True

    def test_index_route(self, client):
        """Test the main index route."""
        response = client.get("/")
        assert response.status_code == 200
        # Check that the response contains HTML content
        assert b"html" in response.data or b"<!DOCTYPE" in response.data

    def test_api_servers_get(self, client):
        """Test the API endpoint for getting servers."""
        response = client.get("/api/servers")
        assert response.status_code == 200
        # Should return JSON
        assert response.content_type == "application/json"
        data = response.get_json()
        assert isinstance(data, list)

    def test_api_servers_post(self, client):
        """Test creating a new server configuration."""
        server_data = {
            "name": "Test Server",
            "transport_type": "http",
            "config": {"url": "http://example.com", "headers": {}, "timeout": 30},
        }
        response = client.post("/api/servers", json=server_data, content_type="application/json")
        assert response.status_code in [200, 201]
        data = response.get_json()
        assert "id" in data
        assert data["name"] == "Test Server"

    def test_invalid_api_endpoint(self, client):
        """Test accessing a non-existent API endpoint."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404


class TestServerConfig:
    """Test cases for ServerConfig class functionality."""

    def test_server_config_import(self):
        """Test that we can import ServerConfig from app."""
        from app import ServerConfig

        assert ServerConfig is not None

    def test_server_config_creation(self):
        """Test creating a ServerConfig object."""
        from app import ServerConfig

        config = ServerConfig(name="Test Server", transport_type="http", config={"url": "http://example.com"})

        assert config.name == "Test Server"
        assert config.transport_type == "http"
        assert config.config == {"url": "http://example.com"}
        assert config.id is not None
        assert config.status == "disconnected"

    def test_server_config_to_dict(self):
        """Test converting ServerConfig to dictionary."""
        from app import ServerConfig

        config = ServerConfig(name="Test Server", transport_type="http", config={"url": "http://example.com"})

        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["name"] == "Test Server"
        assert config_dict["transport_type"] == "http"
        assert "id" in config_dict
        assert "created_at" in config_dict
        assert "status" in config_dict


class TestMCPIntegration:
    """Test cases for MCP-related functionality."""

    def test_mcp_imports(self):
        """Test that MCP modules can be imported."""
        from mcp.client import MCPClient
        from mcp.protocol import MCPError
        from mcp.transport import HTTPTransport, StdioTransport, WebSocketTransport

        assert MCPClient is not None
        assert HTTPTransport is not None
        assert StdioTransport is not None
        assert WebSocketTransport is not None
        assert MCPError is not None

    def test_http_transport_creation(self):
        """Test creating an HTTP transport object."""
        from mcp.transport import HTTPTransport

        transport = HTTPTransport("http://example.com")
        assert transport is not None
        assert hasattr(transport, "connect")
        assert hasattr(transport, "disconnect")

    def test_mcp_client_creation(self):
        """Test creating an MCP client object."""
        from mcp.client import MCPClient
        from mcp.transport import HTTPTransport

        transport = HTTPTransport("http://example.com")
        client = MCPClient(transport)
        assert client is not None
        assert hasattr(client, "initialize")
        assert hasattr(client, "disconnect")


if __name__ == "__main__":
    pytest.main([__file__])
