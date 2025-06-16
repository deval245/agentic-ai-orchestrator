import json
import os
from datetime import datetime

def log_agent_output(agent_name: str, input_data: dict, output_data: dict):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)  # ✅ Create logs/ if it doesn't exist

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent": agent_name,
        "input": input_data,
        "output": output_data
    }

    with open(os.path.join(log_dir, "agent_audit_log.jsonl"), "a") as log_file:
        log_file.write(json.dumps(log_entry) + "\n")
