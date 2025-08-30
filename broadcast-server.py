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