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

To use the chat functionality, you need an Anthropic API key:

```bash
# Set environment variable
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"

# Or add to your .env file
echo "ANTHROPIC_API_KEY=your_anthropic_api_key_here" >> .env
```

Get your API key from the [Anthropic Console](https://console.anthropic.com/).

### 2. Connect MCP Servers

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

For more detailed information, see the full documentation in the repository.