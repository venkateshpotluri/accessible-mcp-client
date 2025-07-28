# Chat Functionality

The Accessible MCP Client now includes a comprehensive chat interface that allows users to interact with connected MCP servers using natural language through Claude AI.

## Overview

The chat functionality bridges the gap between human language and MCP protocol commands, enabling users to:
- Ask questions and get help using connected MCP tools
- Interact with multiple MCP servers simultaneously
- Maintain conversation history across sessions
- Access advanced AI capabilities while maintaining full accessibility standards

## Setup

### 1. API Key Configuration

To use the chat functionality, you need an Anthropic API key from the [Anthropic Console](https://console.anthropic.com/).

**For Local Development (Recommended):**

1. **Copy the environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file** and add your API key:
   ```bash
   # Edit the ANTHROPIC_API_KEY line in .env
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

**Alternative Methods:**

```bash
# Set environment variable directly
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"

# Or add to your shell profile (persistent)
echo 'export ANTHROPIC_API_KEY="your_anthropic_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

> **Security Note**: Never commit your `.env` file to version control. The `.env` file is already included in `.gitignore` to prevent accidental commits.

### 2. Optional Configuration

You can customize the chat behavior by adding these variables to your `.env` file or setting them as environment variables:

**In your .env file:**
```bash
# Claude model configuration
CLAUDE_MODEL=claude-3-5-sonnet-20241022  # Default model
CLAUDE_MAX_TOKENS=4000                   # Max response tokens

# Message limits
MAX_MESSAGE_LENGTH=10000                 # Max characters per message
MAX_SESSION_TITLE_LENGTH=200             # Max title length

# Flask configuration
SECRET_KEY=your-secure-secret-key-here
FLASK_ENV=development
```

**As environment variables:**
```bash
export CLAUDE_MODEL="claude-3-5-sonnet-20241022"
export CLAUDE_MAX_TOKENS="4000"
export MAX_MESSAGE_LENGTH="10000"
export MAX_SESSION_TITLE_LENGTH="200"
```

### 3. Connect MCP Servers

Before chatting, connect your MCP servers through the Connections page:
1. Navigate to the Connections tab
2. Add your MCP server configurations
3. Test and connect to your servers

## Using the Chat Interface

### Creating a Chat Session

1. Navigate to the Chat page
2. Click "New Chat" to create a session
3. Optionally provide a session title
4. Select which MCP servers Claude should have access to

### Chatting with Claude

Once you have an active session:

1. **Select MCP Servers**: Check the servers you want Claude to use
2. **Type Your Message**: Use natural language to describe what you need
3. **Send**: Press Enter or click "Send Message"
4. **Review Response**: Claude will automatically call appropriate MCP tools and provide formatted results

### Example Conversations

```
User: Can you help me list the files in my project directory?
Claude: I'll use the file system tools to list your project files.
[Calls MCP file system tool]
Here are the files in your project directory: ...
```

```
User: What's the weather like in San Francisco?
Claude: Let me check the weather for you.
[Calls MCP weather tool]
The current weather in San Francisco is...
```

## Features

### Session Management
- **Create Sessions**: Start new conversations with custom titles
- **Session History**: All conversations are preserved
- **Session Switching**: Easily switch between multiple chat sessions
- **Delete Sessions**: Remove conversations you no longer need

### MCP Integration
- **Automatic Tool Selection**: Claude intelligently chooses which MCP tools to use
- **Multi-Server Support**: Access tools from multiple MCP servers in one conversation
- **Function Calling**: Seamless integration between Claude's function calling and MCP protocol
- **Error Handling**: Graceful handling of tool failures with user-friendly error messages

### Accessibility Features
- **WCAG 2.1 AA Compliance**: Full accessibility standard compliance
- **Keyboard Navigation**: Complete keyboard-only operation support
- **Screen Reader Support**: Comprehensive ARIA labels and live regions
- **High Contrast Mode**: Visual accessibility options
- **Focus Management**: Proper focus handling for modal dialogs and forms

### Security Features
- **Input Validation**: All chat messages are validated for length and content safety
- **HTML Sanitization**: User input is sanitized to prevent XSS attacks
- **API Key Validation**: Anthropic API keys are validated for format and authenticity
- **Rate Limiting Protection**: Built-in handling for API rate limits
- **Error Handling**: Sensitive information is not exposed in error messages

## Troubleshooting

### Common Issues

#### "Anthropic API key not configured"
- Ensure `ANTHROPIC_API_KEY` environment variable is set
- Restart the application after setting the key
- Verify the key is valid in the Anthropic Console

#### "No MCP servers connected"
- Go to the Connections page and connect your MCP servers
- Verify servers are running and accessible
- Check server connection status in the dashboard

#### Chat input is disabled
- Create a new chat session first
- Ensure you have selected at least one MCP server
- Check that your API key is properly configured

#### Tool calls are failing
- Verify the selected MCP servers are still connected
- Check MCP server logs for detailed error information
- Try reconnecting to the affected servers

#### "Message contains potentially dangerous content"
- Review your message for HTML tags or script elements
- Remove any HTML markup from your message
- Contact support if you believe this is a false positive

#### "Message too long" or "Title too long"
- Check the message length limits (default: 10,000 characters for messages, 200 for titles)
- Adjust limits using `MAX_MESSAGE_LENGTH` and `MAX_SESSION_TITLE_LENGTH` environment variables
- Break long messages into smaller parts

#### "API key validation failed"
- Verify your `ANTHROPIC_API_KEY` format (should start with "sk-ant-")
- Ensure the API key is active in the Anthropic Console
- Check for any extra spaces or characters in the key

For more detailed information, see the full documentation in the repository.