# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
- **Run all tests**: `python -m pytest tests/`
- **Run with coverage**: `python -m pytest tests/ --cov=. --cov-report=html`
- **Run specific test**: `python -m pytest tests/test_app.py::TestFlaskApp::test_app_creation`
- **Run integration tests**: `python -m pytest tests/ -m integration`
- **Run unit tests only**: `python -m pytest tests/ -m unit`

### Code Quality
- **Lint with flake8**: `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics`
- **Format with black**: `black .` (line length: 127)
- **Check formatting**: `black --check --diff .`
- **Sort imports**: `isort .`
- **Check import sorting**: `isort --check-only --diff .`

### Development
- **Run Flask app**: `python app.py`
- **Run with debug**: `FLASK_ENV=development python app.py`
- **Install dependencies**: `pip install -r requirements.txt`
- **Install dev dependencies**: `pip install -r requirements-dev.txt`

## Architecture

### Core Components

**Flask Application (app.py)**
- Main web server with SocketIO for real-time communication
- `ServerConfigManager` class handles persistent storage of MCP server configurations
- `ServerConfig` dataclass defines server connection parameters
- WebSocket endpoints at `/ws/mcp/<server_id>` for real-time MCP communication

**MCP Implementation (mcp/ directory)**
- `MCPClient`: Core MCP protocol client with request/response handling
- `MCPTransport`: Abstract transport layer with concrete implementations for HTTP, WebSocket, and stdio
- `protocol.py`: MCP protocol definitions, message validation, and error handling
- Protocol version: "2024-11-05"

**Frontend Architecture**
- WCAG 2.1 AA compliant HTML templates in `templates/`
- Progressive enhancement with semantic HTML5 and ARIA attributes
- JavaScript modules: `main.js`, `mcp-client.js`, `accessibility.js`
- CSS: `main.css` (responsive), `accessibility.css` (a11y enhancements)

### Key Patterns

**Configuration Management**
- Server configs stored in `server_configs.json` with auto-connect functionality
- `ServerConfig.from_dict()` and `to_dict()` methods for serialization
- Thread-safe configuration loading and saving

**MCP Protocol Handling**
- Request-response pattern with unique IDs and threading events
- Message validation using `validate_message()` and `validate_tool_call()`
- Transport abstraction allows multiple connection types (stdio, HTTP, WebSocket)

**Error Handling**
- Custom `MCPError` class with standard JSON-RPC error codes
- Comprehensive logging throughout MCP operations
- HTTP error responses with proper status codes

## Testing Strategy

- **25 test cases** across `test_app.py` and `test_persistent_storage.py`
- pytest configuration in `pytest.ini` with markers for integration, unit, and slow tests
- Coverage reporting configured for CI/CD pipeline
- Test markers: `@pytest.mark.integration`, `@pytest.mark.unit`, `@pytest.mark.slow`

## Accessibility Requirements

This is an accessibility-focused application that must maintain WCAG 2.1 AA compliance:
- All new UI elements require proper ARIA attributes
- Semantic HTML5 structure is mandatory
- Keyboard navigation must be fully functional
- Color contrast ratios must meet AA standards
- Screen reader compatibility is essential

## CI/CD Pipeline

GitHub Actions workflow runs on Python 3.8-3.12:
- Automated testing with pytest
- Code quality checks (flake8, black, isort)
- Coverage reporting to Codecov
- Pipeline triggers on pushes to main/develop branches and PRs

## your responsibilities

- you will review code written for this project in pull requests.
- Code is written by a beginner engineer.
- you will assign pull requests back to the author of the code (Copilot) in most cases once you review.
- you will try to finalize code within 2 iterations for each pull request.
- you will give clear, concise, actionable feedback in your reviews.
