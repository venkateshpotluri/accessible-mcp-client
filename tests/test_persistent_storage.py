import json
import os
import tempfile
import pytest
from unittest.mock import patch

from app import ServerConfig, ServerConfigManager


class TestServerConfig:
    """Test cases for ServerConfig enhancements"""

    def test_server_config_with_auto_connect(self):
        """Test creating ServerConfig with auto_connect option"""
        config = ServerConfig(
            name="Test Server", transport_type="http", config={"url": "http://example.com"}, auto_connect=True
        )

        assert config.auto_connect is True
        assert config.name == "Test Server"
        assert config.status == "disconnected"

    def test_server_config_default_auto_connect(self):
        """Test that auto_connect defaults to False"""
        config = ServerConfig(name="Test Server", transport_type="http", config={"url": "http://example.com"})

        assert config.auto_connect is False

    def test_server_config_to_dict_includes_auto_connect(self):
        """Test that to_dict includes auto_connect field"""
        config = ServerConfig(
            name="Test Server", transport_type="http", config={"url": "http://example.com"}, auto_connect=True
        )

        config_dict = config.to_dict()
        assert "auto_connect" in config_dict
        assert config_dict["auto_connect"] is True

    def test_server_config_from_dict(self):
        """Test creating ServerConfig from dictionary"""
        data = {
            "id": "test-id-123",
            "name": "Test Server",
            "transport_type": "http",
            "config": {"url": "http://example.com"},
            "auto_connect": True,
            "created_at": "2024-01-01T12:00:00",
        }

        config = ServerConfig.from_dict(data)
        assert config.id == "test-id-123"
        assert config.name == "Test Server"
        assert config.transport_type == "http"
        assert config.auto_connect is True
        assert isinstance(config.created_at, type(config.created_at))

    def test_server_config_from_dict_defaults(self):
        """Test creating ServerConfig from dictionary with missing optional fields"""
        data = {"id": "test-id-123", "name": "Test Server", "transport_type": "http", "config": {"url": "http://example.com"}}

        config = ServerConfig.from_dict(data)
        assert config.auto_connect is False  # Default value


class TestServerConfigManager:
    """Test cases for ServerConfigManager"""

    def test_config_manager_creation(self):
        """Test creating a ServerConfigManager"""
        manager = ServerConfigManager("test_config.json")
        assert manager.config_file == "test_config.json"

    def test_load_configs_nonexistent_file(self):
        """Test loading configs when file doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "nonexistent.json")
            manager = ServerConfigManager(config_file)

            configs = manager.load_configs()
            assert configs == {}

    def test_save_and_load_configs(self):
        """Test saving and loading server configurations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "test_config.json")
            manager = ServerConfigManager(config_file)

            # Create test server configs
            config1 = ServerConfig(
                name="Server 1",
                transport_type="http",
                config={"url": "http://example1.com"},
                auto_connect=True,
                server_id="server-1",
            )
            config2 = ServerConfig(
                name="Server 2",
                transport_type="stdio",
                config={"command": "test-cmd"},
                auto_connect=False,
                server_id="server-2",
            )

            test_configs = {"server-1": config1, "server-2": config2}

            # Save configs
            result = manager.save_configs(test_configs)
            assert result is True
            assert os.path.exists(config_file)

            # Load configs
            loaded_configs = manager.load_configs()
            assert len(loaded_configs) == 2
            assert "server-1" in loaded_configs
            assert "server-2" in loaded_configs

            # Verify loaded config 1
            loaded_config1 = loaded_configs["server-1"]
            assert loaded_config1.name == "Server 1"
            assert loaded_config1.transport_type == "http"
            assert loaded_config1.auto_connect is True
            assert loaded_config1.id == "server-1"

            # Verify loaded config 2
            loaded_config2 = loaded_configs["server-2"]
            assert loaded_config2.name == "Server 2"
            assert loaded_config2.transport_type == "stdio"
            assert loaded_config2.auto_connect is False
            assert loaded_config2.id == "server-2"

    def test_save_configs_invalid_file(self):
        """Test saving configs to invalid file path"""
        manager = ServerConfigManager("/invalid/path/config.json")

        config = ServerConfig(name="Test Server", transport_type="http", config={"url": "http://example.com"})

        result = manager.save_configs({"test": config})
        assert result is False

    def test_load_configs_corrupted_file(self):
        """Test loading from corrupted JSON file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "corrupted.json")

            # Create corrupted JSON file
            with open(config_file, "w") as f:
                f.write("{ invalid json")

            manager = ServerConfigManager(config_file)
            configs = manager.load_configs()
            assert configs == {}

    def test_load_configs_with_invalid_server_data(self):
        """Test loading configs with some invalid server data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "mixed_config.json")

            # Create file with mixed valid/invalid data
            data = {
                "valid-server": {
                    "id": "valid-server",
                    "name": "Valid Server",
                    "transport_type": "http",
                    "config": {"url": "http://example.com"},
                    "auto_connect": True,
                },
                "invalid-server": {
                    "id": "invalid-server",
                    "name": "Invalid Server"
                    # Missing required fields
                },
            }

            with open(config_file, "w") as f:
                json.dump(data, f)

            manager = ServerConfigManager(config_file)
            configs = manager.load_configs()

            # Should only load the valid server
            assert len(configs) == 1
            assert "valid-server" in configs
            assert "invalid-server" not in configs

    def test_status_not_saved_to_file(self):
        """Test that runtime status is not saved to persistent storage"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "status_test.json")
            manager = ServerConfigManager(config_file)

            # Create config with status
            config = ServerConfig(
                name="Test Server", transport_type="http", config={"url": "http://example.com"}, server_id="test-server"
            )
            config.status = "connected"  # Set runtime status

            # Save and reload
            manager.save_configs({"test-server": config})

            # Check file content directly
            with open(config_file, "r") as f:
                saved_data = json.load(f)

            assert "status" not in saved_data["test-server"]

            # Load and verify status is reset to default
            loaded_configs = manager.load_configs()
            assert loaded_configs["test-server"].status == "disconnected"


class TestPersistentStorageAPI:
    """Test API endpoints with persistent storage"""

    @pytest.fixture
    def client(self):
        """Create a test client with temporary config file"""
        from app import app, config_manager

        # Use a temporary file for testing
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_config_file = f.name

        # Patch the config manager to use temp file
        with patch.object(config_manager, "config_file", temp_config_file):
            app.config["TESTING"] = True
            app.config["SECRET_KEY"] = "test-secret-key"

            with app.test_client() as client:
                with app.app_context():
                    yield client

        # Cleanup
        try:
            os.unlink(temp_config_file)
        except FileNotFoundError:
            pass

    def test_create_server_with_auto_connect(self, client):
        """Test creating server with auto_connect option"""
        server_data = {
            "name": "Auto Connect Server",
            "transport_type": "http",
            "config": {"url": "http://example.com"},
            "auto_connect": True,
        }

        response = client.post("/api/servers", json=server_data, content_type="application/json")
        assert response.status_code == 201

        data = response.get_json()
        assert data["auto_connect"] is True
        assert data["name"] == "Auto Connect Server"

    def test_update_server_auto_connect(self, client):
        """Test updating server auto_connect setting"""
        # First create a server
        server_data = {
            "name": "Test Server",
            "transport_type": "http",
            "config": {"url": "http://example.com"},
            "auto_connect": False,
        }

        create_response = client.post("/api/servers", json=server_data, content_type="application/json")
        server_id = create_response.get_json()["id"]

        # Update auto_connect setting
        update_data = {"auto_connect": True}
        response = client.put(f"/api/servers/{server_id}", json=update_data, content_type="application/json")

        assert response.status_code == 200
        data = response.get_json()
        assert data["auto_connect"] is True
