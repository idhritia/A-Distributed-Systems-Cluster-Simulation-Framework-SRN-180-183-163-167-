# Distributed Cluster Simulator

A lightweight, simulation-based distributed system that mimics core Kubernetes cluster management functionalities, built as part of the `PE22CS351B: Cloud Computing` course project. This project simulates a cluster with nodes (Docker containers) and pods, featuring node management, pod scheduling, and health monitoring, accessible via a web interface.

## Project Overview

- **Course**: PE22CS351B: Cloud Computing (Sem 6, 2025)
- **Objective**: Develop a simplified Kubernetes-like system to demonstrate distributed computing concepts.
- **Features**:
  - Add nodes with specified CPU cores (simulated as Docker containers).
  - Launch pods with CPU requirements, scheduled using a First-Fit algorithm.
  - Monitor node health with heartbeats and handle failures by rescheduling pods.
  - Web interface to interact with the cluster.
- **Tech Stack**:
  - Python (Flask for API server, Docker SDK for container management)
  - Docker (for node simulation)
  - HTML/CSS/JavaScript (web interface)

## Prerequisites

- **Docker**: Install Docker Desktop (Mac/Windows) or Docker Engine (Linux).
  - Verify with: `docker --version`
- **Docker Compose**: Included with Docker Desktop; for Linux, install separately.
  - Verify with: `docker-compose --version`
- **Python 3.9+**: Only needed for local development (optional), as Docker handles runtime.

## Directory Structure

```
distributed-cluster-sim/
├── static/
│   └── style.css           # CSS for web interface
├── templates/
│   └── index.html          # Web interface HTML
├── Dockerfile.app          # Dockerfile for API server
├── Dockerfile.node         # Dockerfile for node containers
├── app.py                  # API server and cluster logic
├── node.py                 # Node simulation script
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd distributed-cluster-sim
   ```

2. **Build the Node Image**
   ```bash
   docker build -f Dockerfile.node -t cluster-node .
   ```
   This creates the `cluster-node` image used for simulating nodes.

## Running the Project

1. **Start the API Server**
   ```bash
   docker-compose up --build
   ```
   - Builds and runs the API server at `http://localhost:5000`.
   - Creates a `cluster_network` for container communication.

2. **Access the Web Interface**
   - Open your browser at: `http://localhost:5000`
   - Interface includes:
     - **Add Node**: Specify CPU cores to add a node (spawns a Docker container).
     - **Launch Pod**: Specify CPU requirements to launch a pod.
     - **Node Status**: Auto-refreshes every 5 seconds to show node details.

3. **Verify Containers**
   ```bash
   docker ps
   ```
   Example output after adding a node:
   ```
   CONTAINER ID   IMAGE         COMMAND            STATUS          PORTS                    NAMES
   <id>           cluster-node  "python node.py"   Up 10 seconds                            <random_name>
   <id>           <app_image>   "python app.py"    Up 1 minute     0.0.0.0:5000->5000/tcp   distributed-cluster-sim-app-1
   ```

4. **Stop the Project**
   ```bash
   docker-compose down
   ```
   Stops and removes containers and the `cluster_network`.

## Usage

- **Add a Node**:
  - Enter CPU cores (e.g., 4) and click "Add Node."
  - A new Docker container starts, visible in `docker ps`.
- **Launch a Pod**:
  - Enter CPU required (e.g., 2) and click "Launch Pod."
  - Pod is scheduled to a node with sufficient resources.
- **Monitor Nodes**:
  - "Node Status" shows node details (ID, CPU, pods, status, container ID).
  - If a node fails (e.g., stopped via `docker stop <container_id>`), pods are rescheduled.
- **Check Logs**:
  - API server: `docker logs distributed-cluster-sim-app-1`
  - Node: `docker logs <node_container_id>`

## Weekly Implementation Breakdown

- **Week 1: Node Manager**
  - Implemented in `app.py` with `/add_node` route and `ensure_network()` function.
- **Week 2: Pod Scheduler & Health Monitor**
  - Pod scheduling via `schedule_pod()` (First-Fit algorithm).
  - Health monitoring in `health_monitor()` thread, rescheduling pods on node failure.
- **Week 3: Node Listing**
  - `/list_nodes` route and auto-refreshing web interface.

## Troubleshooting

- **Nodes Not Appearing in Web Interface**:
  - Check `docker ps` for "Running" node containers.
  - Verify logs:
    ```bash
    docker logs distributed-cluster-sim-app-1
    docker logs <node_container_id>
    ```
  - Ensure `cluster_network` exists:
    ```bash
    docker network ls
    
