# Accessible MCP Client

A comprehensive, web-accessible Model Context Protocol (MCP) client built with Flask. This application provides a user-friendly interface to connect to and interact with various MCP servers while maintaining full WCAG 2.1 AA compliance.

## Features

- **Full MCP Support**: Complete implementation of the Model Context Protocol specification
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

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Access the application**:
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

1. **Select Active Server**: Choose from your connected servers
2. **Browse Available Tools**: View tools provided by the server
3. **Execute Tool Calls**: Use the interactive forms to call server tools
4. **View Responses**: See formatted responses with syntax highlighting
5. **Manage Resources**: Access and manage server resources

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

### WebSocket Endpoints
- `/ws/mcp/<server_id>` - WebSocket connection for real-time MCP communication

## Configuration

### Environment Variables
- `FLASK_ENV`: Set to 'development' for development mode
- `SECRET_KEY`: Flask secret key for session management
- `MCP_TIMEOUT`: Default timeout for MCP operations (default: 30 seconds)
- `MAX_SERVERS`: Maximum number of concurrent server connections (default: 10)

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

## Testing

### Running Tests
```bash
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
│   ├── connections.html # Server connections
│   └── help.html       # Help documentation
├── tests/              # Test suite
├── requirements.txt    # Python dependencies
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
