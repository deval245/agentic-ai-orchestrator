import os
import pytest
from agents.planner import PlannerAgent

@pytest.fixture
def planner_agent(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-xxxxx")  # Replace with a dummy or actual test key
    return PlannerAgent()

def test_planner_thoughts(planner_agent):
    input_data = {"user_input": "How to grow a team with leadership principles?"}
    result = planner_agent.invoke(input_data)
    assert "thoughts" in result
    assert "steps" in result
    assert isinstance(result["steps"], list)