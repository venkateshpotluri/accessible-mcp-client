"""
Chat service for integrating with Claude and MCP servers
"""
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import anthropic

logger = logging.getLogger(__name__)


class ChatMessage:
    """Represents a single chat message"""
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None, message_id: Optional[str] = None):
        self.id = message_id or str(uuid.uuid4())
        self.role = role  # 'user', 'assistant', 'system'
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.tool_calls = []
        self.tool_results = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        timestamp = datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now()
        message = cls(
            role=data["role"],
            content=data["content"],
            timestamp=timestamp,
            message_id=data["id"]
        )
        message.tool_calls = data.get("tool_calls", [])
        message.tool_results = data.get("tool_results", [])
        return message


class ChatSession:
    """Represents a chat session with conversation history"""
    
    def __init__(self, session_id: Optional[str] = None, title: Optional[str] = None):
        self.id = session_id or str(uuid.uuid4())
        self.title = title or "New Chat"
        self.messages: List[ChatMessage] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.active_server_ids: List[str] = []

    def add_message(self, message: ChatMessage):
        """Add a message to the session"""
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_messages_for_claude(self) -> List[Dict[str, Any]]:
        """Convert messages to Claude API format"""
        claude_messages = []
        
        for message in self.messages:
            if message.role in ['user', 'assistant']:
                claude_message = {
                    "role": message.role,
                    "content": message.content
                }
                claude_messages.append(claude_message)
        
        return claude_messages

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "active_server_ids": self.active_server_ids
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatSession':
        session = cls(
            session_id=data["id"],
            title=data["title"]
        )
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.updated_at = datetime.fromisoformat(data["updated_at"])
        session.active_server_ids = data.get("active_server_ids", [])
        session.messages = [ChatMessage.from_dict(msg_data) for msg_data in data.get("messages", [])]
        return session


class ChatService:
    """Service for handling chat interactions with Claude and MCP integration"""
    
    def __init__(self, anthropic_api_key: Optional[str] = None):
        self.api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("No Anthropic API key provided. Chat functionality will be limited.")
        
        self.sessions: Dict[str, ChatSession] = {}
        self.mcp_clients = {}  # Will be injected by the main app

    def set_mcp_clients(self, mcp_clients: Dict[str, Any]):
        """Set the MCP clients reference from the main app"""
        self.mcp_clients = mcp_clients

    def create_session(self, title: Optional[str] = None) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(title=title)
        self.sessions[session.id] = session
        logger.info(f"Created new chat session: {session.id}")
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all chat sessions"""
        return [
            {
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "message_count": len(session.messages)
            }
            for session in self.sessions.values()
        ]

    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted chat session: {session_id}")
            return True
        return False

    def get_available_tools(self, server_ids: List[str]) -> Dict[str, Any]:
        """Get available MCP tools from specified servers"""
        available_tools = {}
        tool_schemas = []

        for server_id in server_ids:
            if server_id in self.mcp_clients:
                try:
                    client = self.mcp_clients[server_id]
                    tools_response = client.list_tools()
                    server_tools = tools_response.get("tools", [])
                    
                    available_tools[server_id] = server_tools
                    
                    # Convert MCP tool schemas to Claude function calling format
                    for tool in server_tools:
                        claude_tool = self._convert_mcp_tool_to_claude_function(tool, server_id)
                        tool_schemas.append(claude_tool)
                        
                except Exception as e:
                    logger.error(f"Failed to get tools from server {server_id}: {e}")

        return {
            "available_tools": available_tools,
            "claude_tool_schemas": tool_schemas
        }

    def _convert_mcp_tool_to_claude_function(self, mcp_tool: Dict[str, Any], server_id: str) -> Dict[str, Any]:
        """Convert MCP tool schema to Claude function calling format"""
        function_schema = {
            "name": f"{server_id}_{mcp_tool['name']}",
            "description": mcp_tool.get("description", f"Tool {mcp_tool['name']} from server {server_id}"),
            "input_schema": mcp_tool.get("inputSchema", {"type": "object", "properties": {}})
        }
        
        # Add server_id to the schema for tool routing
        if "properties" not in function_schema["input_schema"]:
            function_schema["input_schema"]["properties"] = {}
            
        function_schema["input_schema"]["properties"]["_mcp_server_id"] = {
            "type": "string",
            "const": server_id,
            "description": "Internal: MCP server ID (auto-filled)"
        }
        
        return function_schema

    def send_message(self, session_id: str, user_message: str, server_ids: List[str] = None) -> ChatMessage:
        """Send a message and get Claude's response with MCP tool integration"""
        if not self.client:
            raise ValueError("Anthropic API key not configured")

        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Update active servers for this session
        if server_ids:
            session.active_server_ids = server_ids

        # Add user message to session
        user_msg = ChatMessage("user", user_message)
        session.add_message(user_msg)

        # Get available tools from active servers
        tools_info = self.get_available_tools(session.active_server_ids)
        claude_tools = tools_info["claude_tool_schemas"]

        # Prepare system message with MCP context
        system_message = self._create_system_message(session.active_server_ids, tools_info["available_tools"])

        # Get conversation history for Claude
        messages = session.get_messages_for_claude()

        try:
            # Call Claude API with function calling
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                system=system_message,
                messages=messages,
                tools=claude_tools if claude_tools else None
            )

            # Process Claude's response
            assistant_message = self._process_claude_response(response, session)
            session.add_message(assistant_message)

            return assistant_message

        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            error_message = ChatMessage("assistant", f"I'm sorry, I encountered an error: {str(e)}")
            session.add_message(error_message)
            return error_message

    def _create_system_message(self, server_ids: List[str], available_tools: Dict[str, Any]) -> str:
        """Create system message for Claude with MCP context"""
        system_parts = [
            "You are an AI assistant with access to Model Context Protocol (MCP) servers.",
            "You can help users interact with various tools and resources through natural language.",
            "",
            "Available MCP servers and their tools:"
        ]

        for server_id in server_ids:
            if server_id in available_tools:
                tools = available_tools[server_id]
                system_parts.append(f"\nServer '{server_id}':")
                for tool in tools:
                    system_parts.append(f"  - {tool['name']}: {tool.get('description', 'No description')}")

        system_parts.extend([
            "",
            "When using tools:",
            "- Always explain what you're doing before calling a tool",
            "- Present results in a clear, user-friendly format",
            "- If a tool call fails, explain what went wrong and suggest alternatives",
            "- You can call multiple tools if needed to complete a task",
            "",
            "Be helpful, accurate, and maintain the accessible nature of this interface."
        ])

        return "\n".join(system_parts)

    def _process_claude_response(self, response, session: ChatSession) -> ChatMessage:
        """Process Claude's response and handle tool calls"""
        content_parts = []
        tool_calls = []
        tool_results = []

        for content in response.content:
            if content.type == "text":
                content_parts.append(content.text)
            elif content.type == "tool_use":
                # Handle tool call
                tool_call = {
                    "id": content.id,
                    "name": content.name,
                    "input": content.input
                }
                tool_calls.append(tool_call)

                # Execute the MCP tool
                try:
                    result = self._execute_mcp_tool(content.name, content.input)
                    tool_result = {
                        "tool_call_id": content.id,
                        "result": result,
                        "success": True
                    }
                    tool_results.append(tool_result)
                    
                    # Add tool result to content
                    content_parts.append(f"\n[Tool: {content.name}]\nResult: {json.dumps(result, indent=2)}")
                    
                except Exception as e:
                    error_result = {
                        "tool_call_id": content.id,
                        "error": str(e),
                        "success": False
                    }
                    tool_results.append(error_result)
                    content_parts.append(f"\n[Tool: {content.name}]\nError: {str(e)}")

        # Create assistant message
        assistant_message = ChatMessage("assistant", "\n".join(content_parts))
        assistant_message.tool_calls = tool_calls
        assistant_message.tool_results = tool_results

        return assistant_message

    def _execute_mcp_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Execute an MCP tool call"""
        # Parse server_id and tool_name from the function name
        if "_" not in tool_name:
            raise ValueError(f"Invalid tool name format: {tool_name}")
        
        server_id, actual_tool_name = tool_name.split("_", 1)
        
        if server_id not in self.mcp_clients:
            raise ValueError(f"MCP server {server_id} not connected")

        client = self.mcp_clients[server_id]
        
        # Remove the internal _mcp_server_id parameter
        clean_input = {k: v for k, v in tool_input.items() if k != "_mcp_server_id"}
        
        # Call the MCP tool
        result = client.call_tool(actual_tool_name, clean_input)
        return result

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a chat session"""
        session = self.get_session(session_id)
        if not session:
            return None

        return {
            "id": session.id,
            "title": session.title,
            "message_count": len(session.messages),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "active_servers": session.active_server_ids,
            "last_message": session.messages[-1].content if session.messages else None
        }