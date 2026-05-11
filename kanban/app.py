from flask import Flask, render_template, request, jsonify
import json, os, uuid
from datetime import datetime

app = Flask(__name__)
DATA_FILE = "data.json"

DEFAULT_DATA = {
    "columns": ["Backlog", "In Progress", "Review", "Done"],
    "tasks": [
        {"id": "t1", "title": "Set up project repository", "desc": "Init git repo, add README and .gitignore", "column": "Done", "priority": "low", "created": "2025-05-01"},
        {"id": "t2", "title": "Design database schema", "desc": "Plan tables for users, tasks, and comments", "column": "Done", "priority": "high", "created": "2025-05-02"},
        {"id": "t3", "title": "Build REST API endpoints", "desc": "CRUD operations for tasks and columns", "column": "Review", "priority": "high", "created": "2025-05-05"},
        {"id": "t4", "title": "Write unit tests", "desc": "Cover all API routes with pytest", "column": "In Progress", "priority": "medium", "created": "2025-05-06"},
        {"id": "t5", "title": "Implement drag-and-drop UI", "desc": "Allow cards to move between columns", "column": "In Progress", "priority": "high", "created": "2025-05-07"},
        {"id": "t6", "title": "Add user authentication", "desc": "Login, signup, JWT tokens", "column": "Backlog", "priority": "high", "created": "2025-05-08"},
        {"id": "t7", "title": "Deploy to production", "desc": "Set up CI/CD pipeline and cloud hosting", "column": "Backlog", "priority": "medium", "created": "2025-05-09"},
        {"id": "t8", "title": "Write API documentation", "desc": "Document all endpoints with examples", "column": "Backlog", "priority": "low", "created": "2025-05-10"},
    ]
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return DEFAULT_DATA.copy()

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/board", methods=["GET"])
def get_board():
    return jsonify(load_data())

@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = load_data()
    body = request.json
    task = {
        "id": str(uuid.uuid4())[:8],
        "title": body.get("title", "Untitled"),
        "desc": body.get("desc", ""),
        "column": body.get("column", data["columns"][0]),
        "priority": body.get("priority", "medium"),
        "created": datetime.today().strftime("%Y-%m-%d")
    }
    data["tasks"].append(task)
    save_data(data)
    return jsonify(task), 201

@app.route("/api/tasks/<task_id>", methods=["PUT"])
def update_task(task_id):
    data = load_data()
    for task in data["tasks"]:
        if task["id"] == task_id:
            task.update({k: v for k, v in request.json.items() if k != "id"})
            save_data(data)
            return jsonify(task)
    return jsonify({"error": "Not found"}), 404

@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    data = load_data()
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    return jsonify({"ok": True})

@app.route("/api/tasks/<task_id>/move", methods=["POST"])
def move_task(task_id):
    data = load_data()
    col = request.json.get("column")
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["column"] = col
            save_data(data)
            return jsonify(task)
    return jsonify({"error": "Not found"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)