# Accessible MCP Client

A comprehensive, web-accessible Model Context Protocol (MCP) client built with Flask. This application provides a user-friendly interface to connect to and interact with various MCP servers while maintaining full WCAG 2.1 AA compliance.

## Features

- **Full MCP Support**: Complete implementation of the Model Context Protocol specification
- **Chat Interface**: Natural language interaction with MCP servers through Claude AI
- **Accessible Interface**: WCAG 2.1 AA compliant HTML frontend with semantic markup
- **Multi-Server Support**: Connect to multiple MCP servers simultaneously
- **Protocol Flexibility**: Supports different MCP transport protocols (stdio, HTTP, WebSocket)
- **Real-time Communication**: Live interaction with MCP servers
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Screen Reader Friendly**: Optimized for assistive technologies

## Architecture

### Backend (Flask)
- **Flask Application**: Main web server and API endpoints
- **MCP Protocol Handler**: Manages MCP server connections and protocol compliance
- **WebSocket Support**: Real-time communication with MCP servers
- **Session Management**: Handles multiple concurrent server connections
- **Error Handling**: Comprehensive error management and logging

### Frontend (HTML/CSS/JavaScript)
- **Semantic HTML5**: Proper document structure and ARIA attributes
- **Progressive Enhancement**: Works without JavaScript, enhanced with it
- **Responsive Design**: Mobile-first approach with flexible layouts
- **High Contrast Support**: Accessible color schemes and focus indicators
- **Keyboard Navigation**: Full keyboard accessibility

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Modern web browser
- Anthropic API key (for chat functionality)

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd AccessibleMCPClient
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   
   **Option A: Using .env file (Recommended for local development)**
   ```bash
   # Copy the example file and edit it
   cp .env.example .env
   # Edit .env file with your actual values
   nano .env
   ```
   
   **Option B: Using environment variables**
   ```bash
   export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
   export SECRET_KEY="your-secret-key-here"
   ```

5. **Run the application**:
   ```bash
   python app.py
   ```

6. **Access the application**:
   Open your browser to `http://localhost:5000`

## MCP Server Configuration

The client supports connecting to MCP servers via different transport methods:

### Stdio Transport
- **Command**: Path to the MCP server executable
- **Arguments**: Command-line arguments for the server
- **Working Directory**: Optional working directory for the server process

### HTTP Transport
- **URL**: HTTP endpoint of the MCP server
- **Headers**: Optional HTTP headers for authentication
- **Timeout**: Request timeout in seconds

### WebSocket Transport
- **URL**: WebSocket endpoint of the MCP server
- **Protocols**: Optional WebSocket sub-protocols
- **Headers**: Optional connection headers

## Usage Guide

### Connecting to an MCP Server

1. **Navigate to the Connections tab**
2. **Fill in server details**:
   - Server Name: A friendly name for identification
   - Transport Type: Choose between stdio, HTTP, or WebSocket
   - Connection Parameters: Fill in the appropriate fields based on transport type
3. **Test Connection**: Use the "Test Connection" button to verify connectivity
4. **Save Connection**: Store the connection for future use

### Interacting with Connected Servers

#### Using the Dashboard
1. **Select Active Server**: Choose from your connected servers
2. **Browse Available Tools**: View tools provided by the server
3. **Execute Tool Calls**: Use the interactive forms to call server tools
4. **View Responses**: See formatted responses with syntax highlighting
5. **Manage Resources**: Access and manage server resources

#### Using the Chat Interface
1. **Navigate to Chat**: Click the Chat tab in the navigation
2. **Create Session**: Start a new chat session with an optional title
3. **Select Servers**: Choose which MCP servers Claude can access
4. **Start Chatting**: Use natural language to interact with your MCP tools
5. **Review Results**: Claude will automatically call appropriate tools and format results

Example chat interactions:
- "Can you list the files in my project directory?"
- "What's the current weather in San Francisco?"
- "Help me analyze this data file"
- "Create a new document with the following content..."

### Accessibility Features

- **Keyboard Navigation**: All functionality accessible via keyboard
- **Screen Reader Support**: Comprehensive ARIA labels and descriptions
- **High Contrast Mode**: Toggle high contrast for better visibility
- **Focus Management**: Clear focus indicators and logical tab order
- **Error Announcements**: Screen reader notifications for errors and status changes

## API Endpoints

### Server Management
- `GET /api/servers` - List all configured servers
- `POST /api/servers` - Add a new server configuration
- `PUT /api/servers/<id>` - Update server configuration
- `DELETE /api/servers/<id>` - Remove server configuration
- `POST /api/servers/<id>/connect` - Connect to a server
- `POST /api/servers/<id>/disconnect` - Disconnect from a server

### MCP Protocol
- `POST /api/mcp/initialize` - Initialize MCP session with server
- `POST /api/mcp/list_tools` - Get available tools from server
- `POST /api/mcp/call_tool` - Execute a tool on the server
- `POST /api/mcp/list_resources` - Get available resources from server
- `GET /api/mcp/read_resource` - Read a specific resource

### Chat Interface
- `GET /api/chat/sessions` - List all chat sessions
- `POST /api/chat/sessions` - Create a new chat session
- `GET /api/chat/sessions/<id>` - Get chat session details
- `DELETE /api/chat/sessions/<id>` - Delete a chat session
- `POST /api/chat/sessions/<id>/messages` - Send a message to a session

### WebSocket Endpoints
- `/ws/mcp/<server_id>` - WebSocket connection for real-time MCP communication

## Configuration

## Configuration

### Environment Variables

You can configure the application using environment variables or a `.env` file. For local development, using a `.env` file is recommended as it keeps your configuration organized and secure.

#### Setting up a .env file (Recommended)

1. **Copy the example file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file** with your actual values:
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Required variables**:
   - `ANTHROPIC_API_KEY`: Your Anthropic API key for chat functionality
   - `SECRET_KEY`: Flask secret key for session management

#### Using Environment Variables Directly

If you prefer not to use a `.env` file, you can set environment variables directly:

```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
export SECRET_KEY="your-secret-key-here"
export FLASK_ENV="development"
```

#### Available Configuration Options
- `FLASK_ENV`: Set to 'development' for development mode
- `SECRET_KEY`: Flask secret key for session management
- `ANTHROPIC_API_KEY`: Anthropic API key for chat functionality
- `MCP_TIMEOUT`: Default timeout for MCP operations (default: 30 seconds)
- `MAX_SERVERS`: Maximum number of concurrent server connections (default: 10)
- `CLAUDE_MODEL`: Claude model to use for chat (default: claude-3-5-sonnet-20241022)
- `CLAUDE_MAX_TOKENS`: Maximum tokens for Claude responses (default: 4000)
- `MAX_MESSAGE_LENGTH`: Maximum length for chat messages (default: 10000)
- `MAX_SESSION_TITLE_LENGTH`: Maximum length for chat session titles (default: 200)

### Configuration File
Create a `config.json` file in the root directory:

```json
{
  "debug": false,
  "host": "0.0.0.0",
  "port": 5000,
  "mcp_timeout": 30,
  "max_servers": 10,
  "log_level": "INFO"
}
```

## CI/CD Pipeline

This repository includes an automated CI/CD pipeline that:

- **Automated Testing**: Runs comprehensive tests on Python 3.8-3.12
- **Code Quality**: Linting with flake8, formatting with black, import sorting with isort
- **Coverage Reports**: Generates and uploads test coverage data
- **Multi-Platform**: Ensures compatibility across different Python versions

The pipeline triggers on pushes to `main`/`develop` branches and pull requests. For setup instructions, see [CI_CD_SETUP.md](CI_CD_SETUP.md).

## Testing

### Automated Testing (CI/CD)

This repository includes a comprehensive CI/CD pipeline that automatically:
- Runs tests on multiple Python versions (3.8-3.12)
- Performs code quality checks (linting, formatting)
- Generates coverage reports

See [CI_CD_SETUP.md](CI_CD_SETUP.md) for detailed setup instructions.

### Running Tests Locally

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# Run accessibility tests
python -m pytest tests/test_accessibility.py
```

### Manual Testing
1. **Accessibility Testing**: Use screen readers (NVDA, JAWS, VoiceOver)
2. **Keyboard Testing**: Navigate using only keyboard
3. **Mobile Testing**: Test on various mobile devices and screen sizes
4. **Browser Testing**: Verify compatibility across browsers

## Deployment

### Local Production Deployment

1. **Set production environment**:
   ```bash
   export FLASK_ENV=production
   ```

2. **Use production WSGI server**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

### Docker Deployment

1. **Build Docker image**:
   ```bash
   docker build -t accessible-mcp-client .
   ```

2. **Run container**:
   ```bash
   docker run -p 5000:5000 accessible-mcp-client
   ```

## GitHub Pages Hosting

**Important Note**: GitHub Pages only supports static content (HTML, CSS, JavaScript) and cannot host Flask applications directly. However, you can deploy the frontend as a static site that connects to a separately hosted Flask backend.

### Static Frontend Deployment to GitHub Pages

1. **Build static version**:
   ```bash
   python build_static.py
   ```

2. **Configure GitHub Pages**:
   - Go to repository Settings → Pages
   - Select source: "Deploy from a branch"
   - Choose branch: `gh-pages`
   - Folder: `/ (root)`

3. **Deploy backend separately**:
   - Use platforms like Heroku, DigitalOcean, AWS, or Railway
   - Update frontend configuration to point to backend URL

### Alternative Hosting Options

For full-stack deployment with Flask backend:

1. **Heroku**:
   ```bash
   # Create Procfile
   echo "web: gunicorn app:app" > Procfile
   
   # Deploy to Heroku
   heroku create your-app-name
   git push heroku main
   ```

2. **Railway**:
   - Connect GitHub repository to Railway
   - Railway will auto-detect Flask application
   - Set environment variables in Railway dashboard

3. **DigitalOcean App Platform**:
   - Connect GitHub repository
   - Configure build and run commands
   - Set environment variables

## Development

### Project Structure
```
AccessibleMCPClient/
├── app.py                 # Main Flask application
├── chat/                  # Chat service implementation
│   ├── __init__.py
│   └── service.py        # Claude AI integration and chat management
├── mcp/                   # MCP protocol implementation
│   ├── __init__.py
│   ├── client.py         # MCP client implementation
│   ├── protocol.py       # Protocol definitions
│   └── transport.py      # Transport layer implementations
├── static/               # Static assets
│   ├── css/
│   │   ├── main.css     # Main stylesheet
│   │   └── accessibility.css # Accessibility enhancements
│   ├── js/
│   │   ├── main.js      # Main JavaScript
│   │   ├── mcp-client.js # MCP client JavaScript
│   │   └── accessibility.js # Accessibility helpers
│   └── images/          # Image assets
├── templates/           # Jinja2 templates
│   ├── base.html       # Base template
│   ├── index.html      # Main interface
│   ├── chat.html       # Chat interface
│   ├── connections.html # Server connections
│   └── help.html       # Help documentation
├── docs/               # Additional documentation
│   └── chat.md         # Chat functionality guide
├── tests/              # Test suite
├── requirements.txt    # Python dependencies
├── requirements-dev.txt # Development dependencies
├── Dockerfile         # Docker configuration
├── Procfile          # Heroku configuration
└── README.md         # This file
```

### Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Follow coding standards**: Use Black for Python formatting
4. **Add tests**: Ensure new features have test coverage
5. **Test accessibility**: Verify WCAG 2.1 AA compliance
6. **Submit pull request**: Include detailed description of changes

### Code Standards

- **Python**: Follow PEP 8, use Black formatter
- **JavaScript**: Use ESLint with accessibility plugin
- **HTML**: Validate with W3C validator, check ARIA usage
- **CSS**: Use semantic class names, follow BEM methodology

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check if MCP server is running and ports are correct
2. **WebSocket Errors**: Verify WebSocket URL and ensure server supports WebSocket
3. **Permission Denied**: Check file permissions for stdio transport servers
4. **Timeout Errors**: Increase timeout values in configuration

### Debug Mode

Enable debug mode for detailed error messages:
```bash
export FLASK_ENV=development
python app.py
```

### Logs

Application logs are available in:
- Console output (development)
- `logs/app.log` (production)

## Security Considerations

- **Input Validation**: All user inputs are validated and sanitized
- **CSRF Protection**: Cross-site request forgery protection enabled
- **Secure Headers**: Security headers configured for production
- **Connection Security**: Support for secure WebSocket (WSS) and HTTPS

## Accessibility Compliance

This application meets WCAG 2.1 AA standards:

- **Perceivable**: High contrast ratios, alternative text, semantic markup
- **Operable**: Keyboard navigation, focus management, no seizure-inducing content
- **Understandable**: Clear language, predictable navigation, error identification
- **Robust**: Valid HTML, ARIA attributes, cross-browser compatibility

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the help documentation in the application

## Changelog

### Version 1.0.0
- Initial release with full MCP protocol support
- WCAG 2.1 AA compliant interface
- Multi-transport support (stdio, HTTP, WebSocket)
- Comprehensive documentation and testing
