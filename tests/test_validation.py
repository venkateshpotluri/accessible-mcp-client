"""
Tests for input validation and error handling
"""

from unittest.mock import MagicMock, patch

import pytest

from app import sanitize_html_content, validate_chat_message
from chat.service import ChatService


class TestInputValidation:
    """Test input validation functions"""

    def test_validate_chat_message_valid(self):
        """Test valid chat message"""
        is_valid, error = validate_chat_message("Hello, how are you?")
        assert is_valid is True
        assert error == ""

    def test_validate_chat_message_empty_string(self):
        """Test empty string message"""
        is_valid, error = validate_chat_message("")
        assert is_valid is False
        assert "non-empty string" in error

    def test_validate_chat_message_none(self):
        """Test None message"""
        is_valid, error = validate_chat_message(None)
        assert is_valid is False
        assert "non-empty string" in error

    def test_validate_chat_message_whitespace_only(self):
        """Test whitespace-only message"""
        is_valid, error = validate_chat_message("   \n\t  ")
        assert is_valid is False
        assert "empty or contain only whitespace" in error

    def test_validate_chat_message_too_long(self):
        """Test message that's too long"""
        long_message = "a" * 10001  # Exceeds MAX_MESSAGE_LENGTH
        is_valid, error = validate_chat_message(long_message)
        assert is_valid is False
        assert "too long" in error

    def test_validate_chat_message_with_script_tag(self):
        """Test message containing script tag"""
        malicious_message = "Hello <script>alert('xss')</script>"
        is_valid, error = validate_chat_message(malicious_message)
        assert is_valid is False
        assert "potentially dangerous content" in error

    def test_validate_chat_message_with_complex_script(self):
        """Test message with complex script tag"""
        malicious_message = "Test < script   type='text/javascript' >evil()</  script  >"
        is_valid, error = validate_chat_message(malicious_message)
        assert is_valid is False
        assert "potentially dangerous content" in error

    def test_sanitize_html_content_basic(self):
        """Test basic HTML sanitization"""
        content = "<div>Hello & goodbye</div>"
        sanitized = sanitize_html_content(content)
        assert sanitized == "&lt;div&gt;Hello &amp; goodbye&lt;/div&gt;"

    def test_sanitize_html_content_quotes(self):
        """Test quote sanitization"""
        content = "He said 'Hello' and \"Goodbye\""
        sanitized = sanitize_html_content(content)
        assert sanitized == "He said &#x27;Hello&#x27; and &quot;Goodbye&quot;"

    def test_sanitize_html_content_empty(self):
        """Test sanitizing empty content"""
        assert sanitize_html_content("") == ""
        assert sanitize_html_content(None) is None


class TestApiKeyValidation:
    """Test API key validation"""

    def test_validate_api_key_valid_anthropic(self):
        """Test valid Anthropic API key format"""
        service = ChatService()
        valid_key = "sk-ant-" + "a" * 100  # Valid format and length
        assert service._validate_api_key(valid_key) is True

    def test_validate_api_key_test_keys(self):
        """Test that test keys are allowed"""
        service = ChatService()
        assert service._validate_api_key("test-key") is True
        assert service._validate_api_key("direct-key") is True
        assert service._validate_api_key("mock-key") is True

    def test_validate_api_key_invalid_prefix(self):
        """Test invalid API key prefix"""
        service = ChatService()
        assert service._validate_api_key("invalid-key") is False

    def test_validate_api_key_too_short(self):
        """Test API key that's too short"""
        service = ChatService()
        short_key = "sk-ant-short"
        assert service._validate_api_key(short_key) is False

    def test_validate_api_key_too_long(self):
        """Test API key that's too long"""
        service = ChatService()
        long_key = "sk-ant-" + "a" * 300
        assert service._validate_api_key(long_key) is False

    def test_validate_api_key_invalid_characters(self):
        """Test API key with invalid characters"""
        service = ChatService()
        invalid_key = "sk-ant-" + "a" * 50 + "!@#$%"
        assert service._validate_api_key(invalid_key) is False

    def test_validate_api_key_none_or_empty(self):
        """Test None or empty API key"""
        service = ChatService()
        assert service._validate_api_key(None) is False
        assert service._validate_api_key("") is False
        assert service._validate_api_key(123) is False


class TestErrorHandling:
    """Test error handling in ChatService"""

    @patch("anthropic.Anthropic")
    def test_anthropic_authentication_error(self, mock_anthropic_class):
        """Test handling of authentication errors"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock the messages.create to raise AuthenticationError
        from anthropic import AuthenticationError

        # Create a proper mock response and error
        mock_response = MagicMock()
        mock_response.status_code = 401
        error = AuthenticationError("Invalid API key", response=mock_response, body={})
        mock_client.messages.create.side_effect = error

        with patch.object(ChatService, "_test_api_key"):
            service = ChatService(anthropic_api_key="test-key")
            session = service.create_session()

            # This should handle the error gracefully
            result = service.send_message(session.id, "Hello")

            assert result.role == "assistant"
            assert "authentication issue" in result.content.lower()

    @patch("anthropic.Anthropic")
    def test_anthropic_rate_limit_error(self, mock_anthropic_class):
        """Test handling of rate limit errors"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        from anthropic import RateLimitError

        mock_response = MagicMock()
        mock_response.status_code = 429
        error = RateLimitError("Rate limit exceeded", response=mock_response, body={})
        mock_client.messages.create.side_effect = error

        with patch.object(ChatService, "_test_api_key"):
            service = ChatService(anthropic_api_key="test-key")
            session = service.create_session()

            result = service.send_message(session.id, "Hello")

            assert result.role == "assistant"
            assert "rate limited" in result.content.lower()

    @patch("anthropic.Anthropic")
    def test_anthropic_connection_error(self, mock_anthropic_class):
        """Test handling of connection errors"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        from anthropic import APIConnectionError

        # APIConnectionError doesn't take a message argument, just use Exception
        error = APIConnectionError(request=MagicMock())
        mock_client.messages.create.side_effect = error

        with patch.object(ChatService, "_test_api_key"):
            service = ChatService(anthropic_api_key="test-key")
            session = service.create_session()

            result = service.send_message(session.id, "Hello")

            assert result.role == "assistant"
            assert "trouble connecting" in result.content.lower()

    @patch("anthropic.Anthropic")
    def test_generic_exception_handling(self, mock_anthropic_class):
        """Test handling of generic exceptions"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_client.messages.create.side_effect = Exception("Unexpected error")

        with patch.object(ChatService, "_test_api_key"):
            service = ChatService(anthropic_api_key="test-key")
            session = service.create_session()

            result = service.send_message(session.id, "Hello")

            assert result.role == "assistant"
            assert "unexpected error" in result.content.lower()


class TestToolResultFormatting:
    """Test tool result formatting functionality"""

    def test_format_tool_result_string(self):
        """Test formatting simple string results"""
        service = ChatService()
        result = service._format_tool_result("test_tool", "Hello world")
        assert result == "Result: Hello world"

    def test_format_tool_result_json_string(self):
        """Test formatting JSON string results"""
        service = ChatService()
        json_string = '{"message": "Hello", "status": "success"}'
        result = service._format_tool_result("test_tool", json_string)
        assert "• message: Hello" in result
        assert "• status: success" in result

    def test_format_tool_result_simple_dict(self):
        """Test formatting simple dictionary results"""
        service = ChatService()
        data = {"name": "John", "age": 30, "active": True}
        result = service._format_tool_result("test_tool", data)
        assert "• name: John" in result
        assert "• age: 30" in result
        assert "• active: True" in result

    def test_format_tool_result_complex_dict(self):
        """Test formatting complex dictionary results"""
        service = ChatService()
        data = {"users": [{"name": "John"}, {"name": "Jane"}], "total": 2}
        result = service._format_tool_result("test_tool", data)
        # Should fall back to JSON formatting for complex data
        assert '"users"' in result
        assert '"total": 2' in result

    def test_format_tool_result_simple_list(self):
        """Test formatting simple list results"""
        service = ChatService()
        data = ["apple", "banana", "cherry"]
        result = service._format_tool_result("test_tool", data)
        assert "• apple" in result
        assert "• banana" in result
        assert "• cherry" in result

    def test_format_tool_result_complex_list(self):
        """Test formatting complex list results"""
        service = ChatService()
        data = [{"name": "John"}, {"name": "Jane"}]
        result = service._format_tool_result("test_tool", data)
        # Should fall back to JSON formatting
        assert '"name": "John"' in result
        assert '"name": "Jane"' in result

    def test_format_tool_result_empty_data(self):
        """Test formatting empty data"""
        service = ChatService()
        assert "Empty data" in service._format_tool_result("test_tool", {})
        assert "Empty list" in service._format_tool_result("test_tool", [])

    def test_format_tool_result_none(self):
        """Test formatting None result"""
        service = ChatService()
        result = service._format_tool_result("test_tool", None)
        assert result == "Result: No data returned"
