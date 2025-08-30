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