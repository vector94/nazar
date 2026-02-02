import os
import socket
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("NAZAR_API_URL", "http://localhost:8000")
HOSTNAME = os.getenv("NAZAR_HOSTNAME", socket.gethostname())
INTERVAL = int(os.getenv("NAZAR_INTERVAL", "10"))