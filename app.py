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
