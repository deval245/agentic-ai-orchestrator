# scripts/generate_graph_dot.py

import sys, os

# Ensure root path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrate import workflow

with open("graph_structure.dot", "w") as f:
    f.write(workflow.get_graph().get_graph().to_dot())

print("✅ DOT file saved as graph_structure.dot")