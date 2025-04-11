from flask import Flask, request, jsonify
import threading
import time
import uuid
from datetime import datetime
import docker
import os
import logging

app = Flask(__name__)
client = docker.from_env()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API Server")

nodes = {}  # {node_id: {"cpu_cores": int, "available_cores": int, "pods": [], "last_heartbeat": timestamp, "container_id": str}}
pods = {}   # {pod_id: {"cpu_required": int, "node_id": str}}
def health_monitor():
    while True:
        current_time = datetime.now().timestamp()
        for node_id in list(nodes.keys()):
            if current_time - nodes[node_id]["last_heartbeat"] > 10:  # 10s timeout
                failed_pods = nodes[node_id]["pods"]
                container_id = nodes[node_id]["container_id"]
                try:
                    container = client.containers.get(container_id)
                    container.stop()
                    container.remove()
                except:
                    pass  # Container already gone
                del nodes[node_id]
                for pod_id in failed_pods:
                    schedule_pod(pod_id, pods[pod_id]["cpu_required"])
        time.sleep(2)

# First-Fit scheduling algorithm (needed for recovery)
def schedule_pod(pod_id, cpu_required):
    for node_id, node in nodes.items():
        if node["available_cores"] >= cpu_required:
            node["available_cores"] -= cpu_required
            node["pods"].append(pod_id)
            pods[pod_id]["node_id"] = node_id
            return True
    return False

# Routes
@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    node_id = data['node_id']
    if node_id in nodes:
        nodes[node_id]["last_heartbeat"] = datetime.now().timestamp()
        logger.info(f"Heartbeat received from {node_id}")
    else:
        logger.warning(f"Heartbeat from unknown node {node_id}")
    return jsonify({"message": "Heartbeat received"})


def schedule_pod(pod_id, cpu_required):
    for node_id, node in nodes.items():
        if node["available_cores"] >= cpu_required:
            node["available_cores"] -= cpu_required
            node["pods"].append(pod_id)
            pods[pod_id]["node_id"] = node_id
            return True
    return False

# Routes
@app.route('/launch_pod', methods=['POST'])
def launch_pod():
    cpu_required = int(request.form['cpu_required'])
    pod_id = str(uuid.uuid4())
    pods[pod_id] = {"cpu_required": cpu_required, "node_id": None}
    if schedule_pod(pod_id, cpu_required):
        return jsonify({"message": f"Pod {pod_id} launched", "pod_id": pod_id})
    else:
        del pods[pod_id]
        return jsonify({"message": "No available node with sufficient resources"}), 400



if __name__ == '__main__':
    threading.Thread(target=health_monitor, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
