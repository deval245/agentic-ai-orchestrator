# Create virtual environment and install dependencies
setup:
	python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# Format code using black
format:
	black .

# Run the FastAPI server
serve:
	uvicorn server.main:app --reload

# Generate LangGraph DOT structure
graph:
	mkdir -p scripts
	if [ ! -f scripts/generate_graph_dot.py ]; then \
		echo 'from langgraph.graph import StateGraph\nfrom graph.orchestrate import workflow\n\nwith open("graph_structure.dot", "w") as f:\n    f.write(workflow.get_graph().get_graph().to_dot())' > scripts/generate_graph_dot.py; \
	fi && python scripts/generate_graph_dot.py
# Visualize the graph
view-graph:
	dot -Tpng graph_structure.dot -o graph.png && open graph.png

# Run tests (if pytest is used)
test:
	pytest

# Lint the code
lint:
	ruff .

# Clean up generated files
clean:
	rm -f graph.png graph_structure.dot

pr:
	gh pr create --base dev --title "Feature: Add new capability to orchestrator" --body "This PR introduces a new feature as discussed. Please review the changes and suggest improvements." && gh pr view --web
