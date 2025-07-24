"""
MCP Protocol definitions and message handling
"""
import json
from enum import Enum
from typing import Any, Dict, List, Optional


class MCPVersion:
    """MCP Protocol version constants"""

    CURRENT = "2024-11-05"
    SUPPORTED = ["2024-11-05"]


class MessageType(Enum):
    """MCP message types"""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


class MCPError(Exception):
    """MCP protocol error"""

    # Error codes from MCP specification
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP Error {code}: {message}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format"""
        error_dict = {"code": self.code, "message": self.message}
        if self.data is not None:
            error_dict["data"] = self.data
        return error_dict


class MCPMessage:
    """Base MCP message class"""

    def __init__(self, message_type: MessageType, data: Dict[str, Any]):
        self.type = message_type
        self.data = data
        self.jsonrpc = "2.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format"""
        return {"jsonrpc": self.jsonrpc, **self.data}

    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPMessage":
        """Create message from dictionary"""
        if "method" in data:
            if "id" in data:
                msg_type = MessageType.REQUEST
            else:
                msg_type = MessageType.NOTIFICATION
        else:
            msg_type = MessageType.RESPONSE

        return cls(msg_type, data)

    @classmethod
    def from_json(cls, json_str: str) -> "MCPMessage":
        """Create message from JSON string"""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise MCPError(MCPError.PARSE_ERROR, f"Invalid JSON: {e}")


class MCPRequest(MCPMessage):
    """MCP request message"""

    def __init__(self, method: str, params: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None):
        self.method = method
        self.params = params or {}
        self.id = request_id

        data = {"method": method, "id": request_id}
        if params:
            data["params"] = params

        super().__init__(MessageType.REQUEST, data)


class MCPResponse(MCPMessage):
    """MCP response message"""

    def __init__(self, request_id: str, result: Optional[Any] = None, error: Optional[MCPError] = None):
        self.id = request_id
        self.result = result
        self.error = error

        data = {"id": request_id}
        if error:
            data["error"] = error.to_dict()
        else:
            data["result"] = result

        super().__init__(MessageType.RESPONSE, data)


class MCPNotification(MCPMessage):
    """MCP notification message"""

    def __init__(self, method: str, params: Optional[Dict[str, Any]] = None):
        self.method = method
        self.params = params or {}

        data = {"method": method}
        if params:
            data["params"] = params

        super().__init__(MessageType.NOTIFICATION, data)


class MCPCapabilities:
    """MCP capabilities definition"""

    def __init__(self):
        self.tools = {}
        self.resources = {}
        self.prompts = {}
        self.logging = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert capabilities to dictionary"""
        return {"tools": self.tools, "resources": self.resources, "prompts": self.prompts, "logging": self.logging}


class MCPTool:
    """MCP tool definition"""

    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.input_schema = input_schema

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary"""
        return {"name": self.name, "description": self.description, "inputSchema": self.input_schema}


class MCPResource:
    """MCP resource definition"""

    def __init__(self, uri: str, name: str, description: Optional[str] = None, mime_type: Optional[str] = None):
        self.uri = uri
        self.name = name
        self.description = description
        self.mime_type = mime_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary"""
        result = {"uri": self.uri, "name": self.name}
        if self.description:
            result["description"] = self.description
        if self.mime_type:
            result["mimeType"] = self.mime_type
        return result


class MCPPrompt:
    """MCP prompt definition"""

    def __init__(self, name: str, description: str, arguments: Optional[List[Dict[str, Any]]] = None):
        self.name = name
        self.description = description
        self.arguments = arguments or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert prompt to dictionary"""
        result = {"name": self.name, "description": self.description}
        if self.arguments:
            result["arguments"] = self.arguments
        return result


# Protocol validation functions


def validate_message(data: Dict[str, Any]) -> None:
    """Validate MCP message format"""
    if not isinstance(data, dict):
        raise MCPError(MCPError.INVALID_REQUEST, "Message must be a JSON object")

    if data.get("jsonrpc") != "2.0":
        raise MCPError(MCPError.INVALID_REQUEST, "Invalid jsonrpc version")

    # Validate based on message type
    if "method" in data:
        # Request or notification
        if not isinstance(data["method"], str):
            raise MCPError(MCPError.INVALID_REQUEST, "Method must be a string")

        if "params" in data and not isinstance(data["params"], dict):
            raise MCPError(MCPError.INVALID_PARAMS, "Params must be an object")

    elif "result" in data or "error" in data:
        # Response
        if "id" not in data:
            raise MCPError(MCPError.INVALID_REQUEST, "Response must have an id")

        if "result" in data and "error" in data:
            raise MCPError(MCPError.INVALID_REQUEST, "Response cannot have both result and error")

    else:
        raise MCPError(MCPError.INVALID_REQUEST, "Invalid message format")


def validate_capabilities(capabilities: Dict[str, Any]) -> None:
    """Validate MCP capabilities format"""
    if not isinstance(capabilities, dict):
        raise MCPError(MCPError.INVALID_PARAMS, "Capabilities must be an object")

    # Validate tool capabilities
    if "tools" in capabilities:
        tools = capabilities["tools"]
        if not isinstance(tools, dict):
            raise MCPError(MCPError.INVALID_PARAMS, "Tools capability must be an object")

    # Validate resource capabilities
    if "resources" in capabilities:
        resources = capabilities["resources"]
        if not isinstance(resources, dict):
            raise MCPError(MCPError.INVALID_PARAMS, "Resources capability must be an object")


def validate_tool_call(name: str, arguments: Dict[str, Any]) -> None:
    """Validate tool call parameters"""
    if not isinstance(name, str) or not name:
        raise MCPError(MCPError.INVALID_PARAMS, "Tool name must be a non-empty string")

    if not isinstance(arguments, dict):
        raise MCPError(MCPError.INVALID_PARAMS, "Tool arguments must be an object")
