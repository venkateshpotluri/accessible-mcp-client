"""
Tests for chat functionality
"""
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from chat.service import ChatMessage, ChatService, ChatSession


class TestChatMessage:
    """Test ChatMessage functionality"""

    def test_chat_message_creation(self):
        """Test creating a chat message"""
        message = ChatMessage("user", "Hello, world!")

        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.id is not None
        assert isinstance(message.timestamp, datetime)
        assert message.tool_calls == []
        assert message.tool_results == []

    def test_chat_message_with_id_and_timestamp(self):
        """Test creating a chat message with custom ID and timestamp"""
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        message = ChatMessage("assistant", "Hello!", timestamp=custom_time, message_id="test-id")

        assert message.id == "test-id"
        assert message.timestamp == custom_time

    def test_chat_message_to_dict(self):
        """Test converting chat message to dictionary"""
        message = ChatMessage("user", "Test message")
        message_dict = message.to_dict()

        assert message_dict["role"] == "user"
        assert message_dict["content"] == "Test message"
        assert message_dict["id"] == message.id
        assert "timestamp" in message_dict
        assert message_dict["tool_calls"] == []
        assert message_dict["tool_results"] == []

    def test_chat_message_from_dict(self):
        """Test creating chat message from dictionary"""
        data = {
            "id": "test-id",
            "role": "assistant",
            "content": "Test response",
            "timestamp": "2023-01-01T12:00:00",
            "tool_calls": [],
            "tool_results": [],
        }

        message = ChatMessage.from_dict(data)

        assert message.id == "test-id"
        assert message.role == "assistant"
        assert message.content == "Test response"
        assert message.timestamp.year == 2023


class TestChatSession:
    """Test ChatSession functionality"""

    def test_chat_session_creation(self):
        """Test creating a chat session"""
        session = ChatSession()

        assert session.id is not None
        assert session.title == "New Chat"
        assert session.messages == []
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)
        assert session.active_server_ids == []

    def test_chat_session_with_custom_title(self):
        """Test creating a chat session with custom title"""
        session = ChatSession(title="Custom Chat")

        assert session.title == "Custom Chat"

    def test_add_message_to_session(self):
        """Test adding a message to a session"""
        session = ChatSession()
        message = ChatMessage("user", "Hello!")

        original_updated_at = session.updated_at
        session.add_message(message)

        assert len(session.messages) == 1
        assert session.messages[0] == message
        assert session.updated_at > original_updated_at

    def test_get_messages_for_claude(self):
        """Test getting messages in Claude API format"""
        session = ChatSession()
        session.add_message(ChatMessage("user", "Hello"))
        session.add_message(ChatMessage("assistant", "Hi there!"))
        session.add_message(ChatMessage("system", "System message"))  # Should be filtered out

        claude_messages = session.get_messages_for_claude()

        assert len(claude_messages) == 2
        assert claude_messages[0]["role"] == "user"
        assert claude_messages[0]["content"] == "Hello"
        assert claude_messages[1]["role"] == "assistant"
        assert claude_messages[1]["content"] == "Hi there!"

    def test_session_to_dict(self):
        """Test converting session to dictionary"""
        session = ChatSession()
        session.add_message(ChatMessage("user", "Test"))

        session_dict = session.to_dict()

        assert session_dict["id"] == session.id
        assert session_dict["title"] == session.title
        assert len(session_dict["messages"]) == 1
        assert "created_at" in session_dict
        assert "updated_at" in session_dict

    def test_session_from_dict(self):
        """Test creating session from dictionary"""
        data = {
            "id": "test-session",
            "title": "Test Chat",
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T13:00:00",
            "active_server_ids": ["server1"],
            "messages": [
                {
                    "id": "msg1",
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2023-01-01T12:30:00",
                    "tool_calls": [],
                    "tool_results": [],
                }
            ],
        }

        session = ChatSession.from_dict(data)

        assert session.id == "test-session"
        assert session.title == "Test Chat"
        assert len(session.messages) == 1
        assert session.active_server_ids == ["server1"]


class TestChatService:
    """Test ChatService functionality"""

    def test_chat_service_creation_without_api_key(self):
        """Test creating chat service without API key"""
        service = ChatService()

        assert service.client is None
        assert service.sessions == {}
        assert service.mcp_clients == {}

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_chat_service_creation_with_api_key(self):
        """Test creating chat service with API key from environment"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            service = ChatService()

            assert service.api_key == "test-key"
            mock_anthropic.assert_called_once_with(api_key="test-key")

    def test_chat_service_creation_with_direct_api_key(self):
        """Test creating chat service with direct API key"""
        with patch("anthropic.Anthropic") as mock_anthropic:
            service = ChatService(anthropic_api_key="direct-key")

            assert service.api_key == "direct-key"
            mock_anthropic.assert_called_once_with(api_key="direct-key")

    def test_set_mcp_clients(self):
        """Test setting MCP clients reference"""
        service = ChatService()
        mock_clients = {"server1": MagicMock(), "server2": MagicMock()}

        service.set_mcp_clients(mock_clients)

        assert service.mcp_clients == mock_clients

    def test_create_session(self):
        """Test creating a new chat session"""
        service = ChatService()

        session = service.create_session("Test Chat")

        assert session.title == "Test Chat"
        assert session.id in service.sessions
        assert service.sessions[session.id] == session

    def test_get_session(self):
        """Test getting a chat session"""
        service = ChatService()
        session = service.create_session("Test Chat")

        retrieved_session = service.get_session(session.id)

        assert retrieved_session == session

    def test_get_nonexistent_session(self):
        """Test getting a non-existent session"""
        service = ChatService()

        result = service.get_session("nonexistent")

        assert result is None

    def test_list_sessions(self):
        """Test listing chat sessions"""
        service = ChatService()
        session1 = service.create_session("Chat 1")
        session2 = service.create_session("Chat 2")

        sessions_list = service.list_sessions()

        assert len(sessions_list) == 2
        session_ids = [s["id"] for s in sessions_list]
        assert session1.id in session_ids
        assert session2.id in session_ids

    def test_delete_session(self):
        """Test deleting a chat session"""
        service = ChatService()
        session = service.create_session("Test Chat")

        success = service.delete_session(session.id)

        assert success is True
        assert session.id not in service.sessions

    def test_delete_nonexistent_session(self):
        """Test deleting a non-existent session"""
        service = ChatService()

        success = service.delete_session("nonexistent")

        assert success is False

    def test_get_available_tools_no_servers(self):
        """Test getting available tools with no servers"""
        service = ChatService()

        tools_info = service.get_available_tools([])

        assert tools_info["available_tools"] == {}
        assert tools_info["claude_tool_schemas"] == []

    def test_get_available_tools_with_servers(self):
        """Test getting available tools with connected servers"""
        service = ChatService()

        # Mock MCP client
        mock_client = MagicMock()
        mock_client.list_tools.return_value = {
            "tools": [
                {
                    "name": "test_tool",
                    "description": "A test tool",
                    "inputSchema": {"type": "object", "properties": {"param": {"type": "string"}}},
                }
            ]
        }

        service.set_mcp_clients({"server1": mock_client})

        tools_info = service.get_available_tools(["server1"])

        assert "server1" in tools_info["available_tools"]
        assert len(tools_info["claude_tool_schemas"]) == 1

        claude_tool = tools_info["claude_tool_schemas"][0]
        assert claude_tool["name"] == "server1_test_tool"
        assert claude_tool["description"] == "A test tool"

    def test_convert_mcp_tool_to_claude_function(self):
        """Test converting MCP tool to Claude function format"""
        service = ChatService()

        mcp_tool = {
            "name": "test_tool",
            "description": "A test tool",
            "inputSchema": {"type": "object", "properties": {"param": {"type": "string"}}},
        }

        claude_function = service._convert_mcp_tool_to_claude_function(mcp_tool, "server1")

        assert claude_function["name"] == "server1_test_tool"
        assert claude_function["description"] == "A test tool"
        assert "_mcp_server_id" in claude_function["input_schema"]["properties"]
        assert claude_function["input_schema"]["properties"]["_mcp_server_id"]["const"] == "server1"

    def test_send_message_without_api_key(self):
        """Test sending message without API key configured"""
        service = ChatService()
        session = service.create_session("Test")

        with pytest.raises(ValueError, match="Anthropic API key not configured"):
            service.send_message(session.id, "Hello")

    def test_send_message_session_not_found(self):
        """Test sending message to non-existent session"""
        service = ChatService(anthropic_api_key="test-key")

        with pytest.raises(ValueError, match="Session .* not found"):
            service.send_message("nonexistent", "Hello")

    def test_get_session_summary(self):
        """Test getting session summary"""
        service = ChatService()
        session = service.create_session("Test Chat")
        session.add_message(ChatMessage("user", "Hello"))
        session.active_server_ids = ["server1"]

        summary = service.get_session_summary(session.id)

        assert summary is not None
        assert summary["id"] == session.id
        assert summary["title"] == "Test Chat"
        assert summary["message_count"] == 1
        assert summary["active_servers"] == ["server1"]
        assert summary["last_message"] == "Hello"

    def test_get_session_summary_nonexistent(self):
        """Test getting summary for non-existent session"""
        service = ChatService()

        summary = service.get_session_summary("nonexistent")

        assert summary is None

    def test_execute_mcp_tool(self):
        """Test executing an MCP tool"""
        service = ChatService()

        # Mock MCP client
        mock_client = MagicMock()
        mock_client.call_tool.return_value = {"result": "success"}

        service.set_mcp_clients({"server1": mock_client})

        result = service._execute_mcp_tool("server1_test_tool", {"param": "value", "_mcp_server_id": "server1"})

        mock_client.call_tool.assert_called_once_with("test_tool", {"param": "value"})
        assert result == {"result": "success"}

    def test_execute_mcp_tool_invalid_format(self):
        """Test executing MCP tool with invalid name format"""
        service = ChatService()

        with pytest.raises(ValueError, match="Invalid tool name format"):
            service._execute_mcp_tool("invalidtoolname", {})

    def test_execute_mcp_tool_server_not_connected(self):
        """Test executing MCP tool with server not connected"""
        service = ChatService()

        with pytest.raises(ValueError, match="MCP server .* not connected"):
            service._execute_mcp_tool("server1_test_tool", {})
