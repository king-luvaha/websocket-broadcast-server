# WebSocket Broadcast Server

A real-time messaging application built with Python and WebSockets that enables instant communication between multiple connected clients. Perfect for chat applications, live notifications, or collaborative tools.

## Features

- 🚀 **Real-time messaging** - Instant message delivery to all connected clients
- 👥 **Multi-client support** - Handle unlimited concurrent connections
- 🔄 **Automatic reconnection handling** - Graceful connection management
- 📝 **Message logging** - Server-side logging for monitoring and debugging
- 🕐 **Timestamped messages** - All messages include server timestamps
- 💬 **System notifications** - Client join/leave notifications
- 🛡️ **Error resilience** - Robust error handling and connection cleanup
- 🎯 **CLI interface** - Easy-to-use command-line interface
- 🔧 **Configurable** - Customizable host and port settings

## Requirements

- **Python 3.7+** (Required for async/await support)
- **websockets library** (Only external dependency)

## Installation

### Option 1: Clone and Install (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd websocket-broadcast-server

# Install dependencies
pip install websockets

# Or using requirements.txt
pip install -r requirements.txt
```

### Option 2: Direct Download

1. Download `broadcast-server.py`
2. Install the websockets library:
   ```bash
   pip install websockets
   ```

### Option 3: Virtual Environment (Best Practice)

```bash
# Create virtual environment
python -m venv websocket-env

# Activate virtual environment
# On Windows:
websocket-env\Scripts\activate
# On macOS/Linux:
source websocket-env/bin/activate

# Install dependencies
pip install websockets
```

## Quick Start

### 1. Start the Server

Open a terminal and run:

```bash
python broadcast-server.py start
```

You should see:
```
🚀 Broadcast server started on ws://localhost:8765
Waiting for client connections...
Press Ctrl+C to stop the server
```

### 2. Connect Clients

Open **additional terminals** (keep the server running) and connect clients:

```bash
python broadcast-server.py connect
```

When prompted, enter a username and start chatting!

### 3. Start Messaging

Type messages in any client terminal and watch them appear in real-time across all connected clients.

## Detailed Usage

### Server Commands

#### Start Server (Default Settings)
```bash
python broadcast-server.py start
```
- Starts server on `localhost:8765`
- Accepts connections from local machine only

#### Start Server (Custom Settings)
```bash
# Custom port
python broadcast-server.py start --port 9000

# Accept connections from any IP address
python broadcast-server.py start --host 0.0.0.0

# Custom host and port
python broadcast-server.py start --host 192.168.1.100 --port 8080
```

#### Server Output Example
```
2025-08-30 10:30:15,123 - INFO - Starting broadcast server on localhost:8765
🚀 Broadcast server started on ws://localhost:8765
Waiting for client connections...
Press Ctrl+C to stop the server
2025-08-30 10:30:20,456 - INFO - Client connected: 127.0.0.1:52341. Total clients: 1
2025-08-30 10:30:25,789 - INFO - Client connected: 127.0.0.1:52342. Total clients: 2
2025-08-30 10:30:30,012 - INFO - Broadcasting message from Alice: Hello everyone!
```

### Client Commands

#### Connect to Local Server
```bash
python broadcast-server.py connect
```

#### Connect to Remote Server
```bash
# Connect to custom host/port
python broadcast-server.py connect --host 192.168.1.100 --port 8080
```

#### Client Session Example
```bash
$ python broadcast-server.py connect
Enter your username: Alice
Connecting to ws://localhost:8765...
✅ Connected to broadcast server as 'Alice'
Type your messages and press Enter to send them.
Type '/quit' to disconnect.
--------------------------------------------------
[10:30:25] SYSTEM: Welcome! You are now connected to the broadcast server. 1 client(s) online.
[10:30:30] SYSTEM: A new client has joined the chat. 2 client(s) online.
[10:30:35] Bob: Hey Alice, how are you?
Hello Bob! I'm doing great, thanks for asking!
[10:30:40] Alice: Hello Bob! I'm doing great, thanks for asking!
[10:30:45] Bob: That's wonderful to hear!
/quit
Disconnected from server
```

## Configuration Options

### Command Line Arguments

| Argument | Description | Default | Example |
|----------|-------------|---------|---------|
| `command` | Action to perform (`start` or `connect`) | Required | `start` |
| `--host` | Server host address | `localhost` | `--host 0.0.0.0` |
| `--port` | Server port number | `8765` | `--port 9000` |

### Network Configuration

#### Local Development
```bash
# Server accessible only from local machine
python broadcast-server.py start --host localhost
```

#### LAN Access
```bash
# Server accessible from local network
python broadcast-server.py start --host 0.0.0.0
```

#### Custom Port
```bash
# Use different port (useful if 8765 is busy)
python broadcast-server.py start --port 9000
```

## Message Format

The application uses JSON messages with the following structure:

### Client to Server
```json
{
    "type": "message",
    "message": "Hello, world!",
    "sender": "Alice"
}
```

### Server to Client
```json
{
    "type": "message",
    "message": "Hello, world!",
    "sender": "Alice",
    "timestamp": "2025-08-30T10:30:40.123456"
}
```

### System Messages
```json
{
    "type": "system",
    "message": "A new client has joined the chat. 3 client(s) online.",
    "timestamp": "2025-08-30T10:30:40.123456"
}
```

## Troubleshooting

### Common Issues and Solutions

#### "Connection refused" Error
**Problem**: Cannot connect to server
**Solutions**:
1. Ensure server is running: `python broadcast-server.py start`
2. Check if port is available: `netstat -an | grep 8765`
3. Verify host/port settings match between server and client
4. Check firewall settings if connecting remotely

#### "Address already in use" Error
**Problem**: Port is already occupied
**Solutions**:
1. Use a different port: `--port 9000`
2. Kill existing process using the port
3. Wait a few seconds and try again (port cleanup delay)

#### "ModuleNotFoundError: No module named 'websockets'"
**Problem**: Missing dependency
**Solution**: Install websockets library:
```bash
pip install websockets
```

#### Messages Not Appearing
**Problem**: Messages sent but not received
**Solutions**:
1. Check server logs for errors
2. Verify all clients are connected to the same server
3. Ensure JSON message format is correct
4. Check network connectivity

#### Client Freezing
**Problem**: Client stops responding
**Solutions**:
1. Press Ctrl+C to force disconnect
2. Restart the client
3. Check server logs for connection errors

### Debug Mode

Enable debug logging by modifying the logging level:

```python
# In the script, change:
logging.basicConfig(level=logging.DEBUG)
```

This will show detailed connection and message information.

## Network Setup

### Local Testing
- Server: `python broadcast-server.py start`
- Clients: `python broadcast-server.py connect`

### LAN Testing
1. **Server machine**:
   ```bash
   # Find your IP address
   # Windows: ipconfig
   # macOS/Linux: ifconfig or ip addr show
   
   # Start server on all interfaces
   python broadcast-server.py start --host 0.0.0.0
   ```

2. **Client machines**:
   ```bash
   # Connect using server's IP address
   python broadcast-server.py connect --host 192.168.1.100
   ```

### Port Forwarding (Internet Access)
For internet access, configure your router to forward the chosen port to your server machine.

## Performance Notes

- **Memory Usage**: Minimal - only stores active WebSocket connections
- **CPU Usage**: Low - event-driven architecture
- **Network**: Efficient JSON message format
- **Scalability**: Tested with 100+ concurrent connections on standard hardware

## Security Considerations

⚠️ **Important**: This is a basic implementation suitable for development and trusted networks.

For production use, consider adding:
- Authentication/authorization
- Message validation and sanitization
- Rate limiting
- SSL/TLS encryption (WSS)
- Input filtering
- Connection limits

## File Structure

```
websocket-broadcast/
├── broadcast-server.py      # Main application file
├── requirements.txt         # Python dependencies
└── README.md/
```

## API Reference

### BroadcastServer Class

#### Methods
- `__init__(host, port)` - Initialize server
- `register_client(websocket)` - Register new client connection
- `unregister_client(websocket)` - Remove client connection
- `broadcast_to_all(message)` - Send message to all clients
- `broadcast_to_others(message, sender)` - Send message to all except sender
- `handle_client(websocket)` - Handle individual client communication
- `start_server()` - Start the WebSocket server
- `stop_server()` - Gracefully shutdown server

### BroadcastClient Class

#### Methods
- `__init__(host, port)` - Initialize client
- `connect()` - Connect to server and start message handling
- `listen_for_messages()` - Handle incoming messages
- `send_messages()` - Handle outgoing messages

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review server logs for error messages
3. Ensure all requirements are met
4. Create an issue with detailed error information

## Changelog

### v1.0.0
- Initial release
- Basic broadcast functionality
- CLI interface
- Error handling and logging
- Graceful shutdown support

---

**Happy broadcasting!** 🎉