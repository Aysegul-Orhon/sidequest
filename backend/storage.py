import json
def save_tasks(tasks, filename="tasks.json"):
    with open(filename, "w") as f:
        json.dump(tasks, f, indent=2)

def load_tasks(filename="tasks.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
