import asyncio
import websockets
import json
import argparse
import sys
import signal
from datetime import datetime
from typing import Set, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BroadcastServer:
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set = set()          # Track connected clients
        self.server = None

    async def register_client(self, websocket):
        """Register a new client connection."""
        self.clients.add(websocket)
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"Client connected: {client_info}. Total clients: {len(self.clients)}")
        
        # Send welcome message to the new client
        welcome_msg = {
            "type": "system",
            "message": f"Welcome! You are now connected to the broadcast server. {len(self.clients)} client(s) online.",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(welcome_msg))
        
        # Notify other clients about new connection
        notification = {
            "type": "system",
            "message": f"A new client has joined the chat. {len(self.clients)} client(s) online.",
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_others(json.dumps(notification), websocket)

    async def unregister_client(self, websocket):
        """Unregister a client connection."""
        if websocket in self.clients:
            self.clients.remove(websocket)
            client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
            logger.info(f"Client disconnected: {client_info}. Total clients: {len(self.clients)}")
            
            # Notify remaining clients about disconnection
            if self.clients:  # Only send if there are still clients connected
                notification = {
                    "type": "system",
                    "message": f"A client has left the chat. {len(self.clients)} client(s) online.",
                    "timestamp": datetime.now().isoformat()
                }
                await self.broadcast_to_all(json.dumps(notification))

    async def broadcast_to_all(self, message: str):
        """Broadcast message to all connected clients."""
        if self.clients:
            # Create a copy of clients set to avoid modification during iteration
            clients_copy = self.clients.copy()
            disconnected_clients = []
            
            for client in clients_copy:
                try:
                    await client.send(message)
                except (websockets.exceptions.ConnectionClosed, ConnectionResetError):
                    disconnected_clients.append(client)
                except Exception as e:
                    logger.error(f"Error sending message to client: {e}")
                    disconnected_clients.append(client)
            
            # Remove disconnected clients
            for client in disconnected_clients:
                await self.unregister_client(client)

    async def broadcast_to_others(self, message: str, sender):
        """Broadcast message to all clients except the sender."""
        if self.clients:
            clients_copy = self.clients.copy()
            disconnected_clients = []
            
            for client in clients_copy:
                if client != sender:
                    try:
                        await client.send(message)
                    except (websockets.exceptions.ConnectionClosed, ConnectionResetError):
                        disconnected_clients.append(client)
                    except Exception as e:
                        logger.error(f"Error sending message to client: {e}")
                        disconnected_clients.append(client)
            
            # Remove disconnected clients
            for client in disconnected_clients:
                await self.unregister_client(client)

    async def handle_client(self, websocket):
        """Handle individual client connections and messages."""
        await self.register_client(websocket)
        
        try:
            async for raw_message in websocket:
                try:
                    # Parse the incoming message
                    data = json.loads(raw_message)
                    
                    if data.get("type") == "message":
                        # Create broadcast message with timestamp
                        broadcast_msg = {
                            "type": "message",
                            "message": data.get("message", ""),
                            "sender": data.get("sender", "Anonymous"),
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        # Log the message
                        logger.info(f"Broadcasting message from {broadcast_msg['sender']}: {broadcast_msg['message']}")
                        
                        # Broadcast to all clients
                        await self.broadcast_to_all(json.dumps(broadcast_msg))
                        
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid JSON from client {websocket.remote_address}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except (websockets.exceptions.ConnectionClosed, ConnectionResetError):
            pass
        except Exception as e:
            logger.error(f"Error in client handler: {e}")
        finally:
            await self.unregister_client(websocket)

    async def start_server(self):
        """Start the WebSocket server."""
        logger.info(f"Starting broadcast server on {self.host}:{self.port}")
        
        async def connection_handler(websocket):
            await self.handle_client(websocket)
        
        self.server = await websockets.serve(
            connection_handler,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        print(f"🚀 Broadcast server started on ws://{self.host}:{self.port}")
        print("Waiting for client connections...")
        print("Press Ctrl+C to stop the server")
        
        # Keep the server running
        await self.server.wait_closed()

    async def stop_server(self):
        """Stop the WebSocket server gracefully."""
        if self.server:
            logger.info("Shutting down server...")
            
            # Notify all clients about server shutdown
            shutdown_msg = {
                "type": "system",
                "message": "Server is shutting down. You will be disconnected shortly.",
                "timestamp": datetime.now().isoformat()
            }
            await self.broadcast_to_all(json.dumps(shutdown_msg))
            
            # Close all client connections
            if self.clients:
                await asyncio.gather(
                    *[client.close() for client in self.clients.copy()],
                    return_exceptions=True
                )
            
            # Close the server
            self.server.close()
            await self.server.wait_closed()
            logger.info("Server stopped")

class BroadcastClient:
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.websocket = None
        self.username = None
        self.running = False

    async def connect(self):
        """Connect to the broadcast server."""
        uri = f"ws://{self.host}:{self.port}"
        
        # Get username
        self.username = input("Enter your username: ").strip()
        if not self.username:
            self.username = "Anonymous"
        
        try:
            print(f"Connecting to {uri}...")
            self.websocket = await websockets.connect(uri)
            self.running = True
            
            print(f"✅ Connected to broadcast server as '{self.username}'")
            print("Type your messages and press Enter to send them.")
            print("Type '/quit' to disconnect.")
            print("-" * 50)
            
            # Start listening for messages and sending messages concurrently
            await asyncio.gather(
                self.listen_for_messages(),
                self.send_messages()
            )
            
        except (ConnectionRefusedError, OSError, TimeoutError) as e:
            print(f"❌ Could not connect to server at {uri}")
            print("Make sure the server is running with 'broadcast-server start'")
            print(f"Error details: {e}")
        except Exception as e:
            print(f"❌ Connection error: {e}")

    async def listen_for_messages(self):
        """Listen for incoming messages from the server."""
        try:
            async for raw_message in self.websocket:
                try:
                    message = json.loads(raw_message)
                    
                    if message.get("type") == "message":
                        timestamp = datetime.fromisoformat(message["timestamp"]).strftime("%H:%M:%S")
                        sender = message.get("sender", "Unknown")
                        content = message.get("message", "")
                        print(f"[{timestamp}] {sender}: {content}")
                        
                    elif message.get("type") == "system":
                        timestamp = datetime.fromisoformat(message["timestamp"]).strftime("%H:%M:%S")
                        content = message.get("message", "")
                        print(f"[{timestamp}] SYSTEM: {content}")
                        
                except json.JSONDecodeError:
                    print("Received invalid message from server")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except (websockets.exceptions.ConnectionClosed, ConnectionResetError):
            print("\n💔 Connection to server lost")
            self.running = False
        except Exception as e:
            print(f"\n❌ Error receiving messages: {e}")
            self.running = False

    async def send_messages(self):
        """Handle sending messages to the server."""
        try:
            while self.running:
                # Use asyncio to handle input without blocking
                message = await asyncio.get_event_loop().run_in_executor(
                    None, input, ""
                )
                
                if not self.running:
                    break
                    
                message = message.strip()
                
                if message.lower() == '/quit':
                    break
                    
                if message:
                    # Send message to server
                    msg_data = {
                        "type": "message",
                        "message": message,
                        "sender": self.username
                    }
                    
                    try:
                        await self.websocket.send(json.dumps(msg_data))
                    except (websockets.exceptions.ConnectionClosed, ConnectionResetError):
                        print("Connection closed while sending message")
                        break
                    except Exception as e:
                        print(f"Error sending message: {e}")
                        break
                        
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(f"Error in send_messages: {e}")
        finally:
            self.running = False
            if self.websocket:
                await self.websocket.close()

async def handle_server_shutdown(server: BroadcastServer):
    """Handle graceful server shutdown on SIGINT."""
    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(server.stop_server())
    
    # Set up signal handler for graceful shutdown
    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        await server.stop_server()

def main():
    parser = argparse.ArgumentParser(description="WebSocket Broadcast Server")
    parser.add_argument(
        "command", 
        choices=["start", "connect"], 
        help="Command to execute: 'start' to run server, 'connect' to connect as client"
    )
    parser.add_argument(
        "--host", 
        default="localhost", 
        help="Host address (default: localhost)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8765, 
        help="Port number (default: 8765)"
    )
    
    args = parser.parse_args()
    
    if args.command == "start":
        server = BroadcastServer(args.host, args.port)
        try:
            asyncio.run(handle_server_shutdown(server))
        except KeyboardInterrupt:
            print("\nServer stopped")
    
    elif args.command == "connect":
        client = BroadcastClient(args.host, args.port)
        try:
            asyncio.run(client.connect())
        except KeyboardInterrupt:
            print("\nDisconnected from server")

if __name__ == "__main__":
    main()