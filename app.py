from flask import Flask, request, jsonify, render_template
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

# In-memory storage for nodes and pods
nodes = {}  # {node_id: {"cpu_cores": int, "available_cores": int, "pods": [], "last_heartbeat": timestamp, "container_id": str}}
pods = {}   # {pod_id: {"cpu_required": int, "node_id": str}}

# Health monitoring thread
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

# First-Fit scheduling algorithm
def schedule_pod(pod_id, cpu_required):
    for node_id, node in nodes.items():
        if node["available_cores"] >= cpu_required:
            node["available_cores"] -= cpu_required
            node["pods"].append(pod_id)
            pods[pod_id]["node_id"] = node_id
            return True
    return False

# Ensure the network exists
def ensure_network():
    try:
        client.networks.get("cluster_network")
        logger.info("Network 'cluster_network' already exists")
    except docker.errors.NotFound:
        client.networks.create("cluster_network", driver="bridge")
        logger.info("Created network 'cluster_network'")
    except docker.errors.APIError as e:
        logger.error(f"Failed to create/check network: {e}")
        raise

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_node', methods=['POST'])
def add_node():
    cpu_cores = int(request.form['cpu_cores'])
    node_id = str(uuid.uuid4())
    
    try:
        ensure_network()  # Ensure network exists before launching container
        container = client.containers.run(
            "cluster-node",
            environment={"NODE_ID": node_id, "CPU_CORES": cpu_cores, "API_URL": "http://app:5000"},
            network="cluster_network",
            detach=True
        )
        logger.info(f"Started container {container.id} for node {node_id}")
    except docker.errors.APIError as e:
        logger.error(f"Failed to start container for node {node_id}: {e}")
        return jsonify({"message": f"Failed to add node: {e}"}), 500
    
    nodes[node_id] = {
        "cpu_cores": cpu_cores,
        "available_cores": cpu_cores,
        "pods": [],
        "last_heartbeat": datetime.now().timestamp(),
        "container_id": container.id
    }
    logger.info(f"Node {node_id} added to in-memory store")
    return jsonify({"message": f"Node {node_id} added with {cpu_cores} CPU cores", "node_id": node_id})

@app.route('/register_node', methods=['POST'])
def register_node():
    data = request.json
    logger.info(f"Received registration request: {data}")
    node_id = data['node_id']
    cpu_cores = int(data['cpu_cores'])
    if node_id not in nodes:
        try:
            container_id = client.containers.get(data['container_id']).id
            nodes[node_id] = {
                "cpu_cores": cpu_cores,
                "available_cores": cpu_cores,
                "pods": [],
                "last_heartbeat": datetime.now().timestamp(),
                "container_id": container_id
            }
            logger.info(f"Node {node_id} registered successfully")
        except docker.errors.NotFound:
            logger.error(f"Container {data['container_id']} not found for node {node_id}")
    return jsonify({"message": f"Node {node_id} registered"})

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

@app.route('/list_nodes', methods=['GET'])
def list_nodes():
    current_time = datetime.now().timestamp()
    node_status = []
    for node_id, node in nodes.items():
        status = "Healthy" if (current_time - node["last_heartbeat"] <= 10) else "Failed"
        node_status.append({
            "node_id": node_id,
            "cpu_cores": node["cpu_cores"],
            "available_cores": node["available_cores"],
            "pods": node["pods"],
            "status": status,
            "container_id": node["container_id"]
        })
    return jsonify(node_status)

if __name__ == '__main__':
    threading.Thread(target=health_monitor, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
