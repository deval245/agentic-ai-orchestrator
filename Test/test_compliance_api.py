import requests
import os
import pytest

API_URL = "http://127.0.0.1:8000/run-agent"
TEST_DOC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "Amazon Leadership Principles.docx.pdf"))
@pytest.mark.parametrize("user_input,expected_warning,expected_tags", [
    ("Email me at jane.doe@example.com", "⚠️", ["EMAIL"]),
    ("My SSN is 123-45-6789", "⚠️", ["SSN"]),
    ("Call 555-123-4567 for more info", "⚠️", ["PHONE"]),
    ("Send a copy to john.doe@example.com and call 999-111-2222", "⚠️", ["EMAIL", "PHONE"]),
    ("My email is alice@xyz.com and SSN is 000-11-2222", "⚠️", ["EMAIL", "SSN"]),
    ("No sensitive info here", "✅", []),
    ("The product SKU is 123-45-678, not a SSN", "✅", []),
])
def test_compliance_api_pii_detection(user_input, expected_warning, expected_tags):
    with open(TEST_DOC_PATH, "rb") as f:
        response = requests.post(
            API_URL,
            files={
                "file": ("Amazon_Leadership_Principles.docx.pdf", f, "application/pdf")
            },
            data={"user_input": user_input},
        )

    assert response.status_code == 200
    json_response = response.json()

    # Check warning symbol
    assert json_response["warning"].startswith(expected_warning)

    # Check detected sensitivity tags
    if expected_tags:
        assert "sensitivity_flags" in json_response["audit_metadata"]
        for tag in expected_tags:
            assert tag in json_response["audit_metadata"]["sensitivity_flags"]
    else:
        assert json_response["audit_metadata"]["sensitivity_flags"] == []