import os
import requests
import time
import socket
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Node")

# Get environment variables
NODE_ID = os.getenv("NODE_ID")
CPU_CORES = os.getenv("CPU_CORES")
API_URL = os.getenv("API_URL", "http://localhost:5000")
CONTAINER_ID = socket.gethostname()  # Docker container ID

# Validate environment variables
if not NODE_ID or not CPU_CORES:
    logger.error("NODE_ID or CPU_CORES not set. Exiting.")
    exit(1)

try:
    CPU_CORES = int(CPU_CORES)
except ValueError:
    logger.error(f"Invalid CPU_CORES value: {CPU_CORES}. Must be an integer. Exiting.")
    exit(1)

# Register node with API server
def register_node():
    while True:
        try:
            response = requests.post(
                f"{API_URL}/register_node",
                json={"node_id": NODE_ID, "cpu_cores": CPU_CORES, "container_id": CONTAINER_ID},
                timeout=5
            )
            if response.status_code == 200:
                logger.info(f"Node {NODE_ID} registered successfully")
                return True
            else:
                logger.warning(f"Registration failed with status {response.status_code}: {response.text}")
        except requests.RequestException as e:
            logger.error(f"Failed to register with API server at {API_URL}: {e}")
        time.sleep(2)

# Send heartbeat
def send_heartbeat():
    while True:
        try:
            response = requests.post(
                f"{API_URL}/heartbeat",
                json={"node_id": NODE_ID},
                timeout=5
            )
            logger.info(f"Heartbeat sent from {NODE_ID}: {response.text}")
        except requests.RequestException as e:
            logger.error(f"Failed to send heartbeat to {API_URL}: {e}")
        time.sleep(5)

if __name__ == "__main__":
    logger.info(f"Starting node {NODE_ID} with {CPU_CORES} CPU cores on container {CONTAINER_ID}")
    if register_node():
        send_heartbeat()
    else:
        logger.error("Node failed to register and will exit.")
        exit(1)
