import pytest
from agents.compliance import ComplianceVerifierAgent

@pytest.fixture
def compliance_agent():
    return ComplianceVerifierAgent()

@pytest.mark.parametrize("input_text,expected_warning", [
    ("My email is test@example.com", True),
    ("Call me at 123-456-7890", True),
    ("My SSN is 123-45-6789", True),
    ("No PII here", False),
])
def test_compliance_detection(compliance_agent, input_text, expected_warning):
    input_data = {"user_input": input_text}
    result = compliance_agent.invoke(input_data)
    assert ("EMAIL" in result["risk_categories_triggered"] or
            "PHONE" in result["risk_categories_triggered"] or
            "SSN" in result["risk_categories_triggered"]) == expected_warning
    if expected_warning:
        assert result["warning"].startswith("⚠️")
    else:
        assert result["warning"].startswith("✅")

