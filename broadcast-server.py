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