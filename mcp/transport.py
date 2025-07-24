"""
MCP Transport layer implementations
"""
import json
import logging
import queue
import subprocess
import threading
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

import requests
import websocket

logger = logging.getLogger(__name__)


class MCPTransport(ABC):
    """Abstract base class for MCP transports"""

    def __init__(self):
        self.connected = False
        self.message_handler: Optional[Callable[[Dict[str, Any]], None]] = None

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to MCP server"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to MCP server"""
        pass

    @abstractmethod
    def send_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send message to MCP server - returns response for HTTP, None for async transports"""
        pass

    def set_message_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Set callback for incoming messages"""
        self.message_handler = handler


class StdioTransport(MCPTransport):
    """Standard input/output transport for MCP"""

    def __init__(self, command: str, args: list = None, cwd: str = None):
        super().__init__()
        self.command = command
        self.args = args or []
        self.cwd = cwd
        self.process: Optional[subprocess.Popen] = None
        self.reader_thread: Optional[threading.Thread] = None
        self.message_queue = queue.Queue()
        self.running = False

    def connect(self) -> None:
        """Start the MCP server process and establish stdio connection"""
        try:
            # Build command with arguments
            cmd = [self.command] + self.args

            # Start process
            self.process = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.cwd, text=True, bufsize=0
            )

            self.running = True
            self.connected = True

            # Start reader thread
            self.reader_thread = threading.Thread(target=self._read_messages, daemon=True)
            self.reader_thread.start()

            logger.info(f"Connected to MCP server via stdio: {self.command}")

        except Exception as e:
            logger.error(f"Failed to connect via stdio: {e}")
            raise

    def disconnect(self) -> None:
        """Terminate the MCP server process"""
        self.running = False
        self.connected = False

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

            self.process = None

        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1)

        logger.info("Disconnected from MCP server via stdio")

    def send_message(self, message: Dict[str, Any]) -> None:
        """Send message to MCP server via stdin"""
        if not self.connected or not self.process:
            raise RuntimeError("Not connected to MCP server")

        try:
            json_message = json.dumps(message) + "\n"
            self.process.stdin.write(json_message)
            self.process.stdin.flush()

            logger.debug(f"Sent message via stdio: {message}")
            return None  # Async transport - response comes via message handler

        except Exception as e:
            logger.error(f"Failed to send message via stdio: {e}")
            raise

    def _read_messages(self) -> None:
        """Read messages from MCP server stdout in separate thread"""
        while self.running and self.process:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break

                line = line.strip()
                if line:
                    try:
                        message = json.loads(line)
                        if self.message_handler:
                            self.message_handler(message)

                        logger.debug(f"Received message via stdio: {message}")

                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON received via stdio: {line}, error: {e}")

            except Exception as e:
                if self.running:
                    logger.error(f"Error reading from stdio: {e}")
                break


class HTTPTransport(MCPTransport):
    """HTTP transport for MCP"""

    def __init__(self, url: str, headers: Dict[str, str] = None, timeout: int = 30):
        super().__init__()

        # Ensure URL has proper protocol
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        self.url = url
        self.headers = headers or {}
        self.timeout = timeout
        self.session = requests.Session()

        logger.info(f"HTTPTransport initialized with URL: {self.url}")

    def connect(self) -> None:
        """Test connection to HTTP MCP server"""
        try:
            logger.info(f"Attempting to connect to MCP server at: {self.url}")

            # Test connection with an initialize request to verify MCP compatibility
            test_message = {
                "jsonrpc": "2.0",
                "id": "test_connection",
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
            }

            logger.info(f"Sending test request to: {self.url}")
            logger.info(f"Headers: {self.headers}")

            response = self.session.post(
                self.url, json=test_message, headers={**self.headers, "Content-Type": "application/json"}, timeout=self.timeout
            )

            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Response body: {result}")
                if result.get("jsonrpc") == "2.0" and "result" in result:
                    self.connected = True
                    logger.info(f"Connected to MCP server via HTTP: {self.url}")
                    return

            logger.error(f"HTTP server returned status {response.status_code}")
            logger.error(f"Response text: {response.text}")
            raise RuntimeError(f"HTTP server returned status {response.status_code} or invalid MCP response")

        except Exception as e:
            logger.error(f"Failed to connect via HTTP to {self.url}: {e}")
            raise

    def disconnect(self) -> None:
        """Close HTTP session"""
        self.connected = False
        self.session.close()
        logger.info("Disconnected from MCP server via HTTP")

    def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to MCP server via HTTP POST and return response"""
        if not self.connected:
            raise RuntimeError("Not connected to MCP server")

        try:
            response = self.session.post(
                self.url, json=message, headers={**self.headers, "Content-Type": "application/json"}, timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            logger.debug(f"Sent message via HTTP: {message}")
            logger.debug(f"Received response via HTTP: {result}")

            return result  # Sync transport - return response directly

        except Exception as e:
            logger.error(f"Failed to send message via HTTP: {e}")
            raise


class WebSocketTransport(MCPTransport):
    """WebSocket transport for MCP"""

    def __init__(self, url: str, protocols: list = None, headers: Dict[str, str] = None):
        super().__init__()
        self.url = url
        self.protocols = protocols or []
        self.headers = headers or {}
        self.websocket: Optional[websocket.WebSocket] = None
        self.reader_thread: Optional[threading.Thread] = None
        self.running = False

    def connect(self) -> None:
        """Establish WebSocket connection to MCP server"""
        try:
            # Create WebSocket connection
            self.websocket = websocket.create_connection(
                self.url, subprotocols=self.protocols, header=list(self.headers.items()) if self.headers else None, timeout=30
            )

            self.running = True
            self.connected = True

            # Start reader thread
            self.reader_thread = threading.Thread(target=self._read_messages, daemon=True)
            self.reader_thread.start()

            logger.info(f"Connected to MCP server via WebSocket: {self.url}")

        except Exception as e:
            logger.error(f"Failed to connect via WebSocket: {e}")
            raise

    def disconnect(self) -> None:
        """Close WebSocket connection"""
        self.running = False
        self.connected = False

        if self.websocket:
            try:
                self.websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")

            self.websocket = None

        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1)

        logger.info("Disconnected from MCP server via WebSocket")

    def send_message(self, message: Dict[str, Any]) -> None:
        """Send message to MCP server via WebSocket"""
        if not self.connected or not self.websocket:
            raise RuntimeError("Not connected to MCP server")

        try:
            json_message = json.dumps(message)
            self.websocket.send(json_message)

            logger.debug(f"Sent message via WebSocket: {message}")
            return None  # Async transport - response comes via message handler

        except Exception as e:
            logger.error(f"Failed to send message via WebSocket: {e}")
            raise

    def _read_messages(self) -> None:
        """Read messages from WebSocket in separate thread"""
        while self.running and self.websocket:
            try:
                message_str = self.websocket.recv()
                if message_str:
                    try:
                        message = json.loads(message_str)
                        if self.message_handler:
                            self.message_handler(message)

                        logger.debug(f"Received message via WebSocket: {message}")

                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON received via WebSocket: {message_str}, error: {e}")

            except websocket.WebSocketConnectionClosedException:
                logger.info("WebSocket connection closed")
                break
            except Exception as e:
                if self.running:
                    logger.error(f"Error reading from WebSocket: {e}")
                break

        self.connected = False
