from langchain_core.runnables import Runnable
from typing import Dict, Any, List
from utils.log_agent_output import log_agent_output
import re
from datetime import datetime

PII_PATTERNS = {
    "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "PHONE": r"\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b"
}

class ComplianceVerifierAgent(Runnable):
    def __init__(self):
        self.redaction_token = "[REDACTED]"

    def invoke(self, input: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
        original_text = input["user_input"]
        redacted_text = original_text

        matches = {}
        for tag, pattern in PII_PATTERNS.items():
            found = re.findall(pattern, redacted_text)
            if found:
                matches[tag] = found
                redacted_text = re.sub(pattern, self.redaction_token, redacted_text)

        redaction_occurred = bool(matches)

        compliance_log = {
            "original_input": original_text,
            "redacted_input": redacted_text,
            "pii_detected": matches if redaction_occurred else "None detected",
            "audit_timestamp": datetime.utcnow().isoformat() + "Z"
        }

        warning_message = "⚠️ PII detected and redacted." if redaction_occurred else "✅ No PII detected."

        pii_total_count = sum(len(v) for v in matches.values())
        if pii_total_count == 0:
            risk_level = "None"
        elif pii_total_count <= 2:
            risk_level = "Low"
        elif pii_total_count <= 5:
            risk_level = "Medium"
        else:
            risk_level = "High"

        # Log externally for audit/compliance purposes
        log_agent_output("ComplianceVerifierAgent", {"user_input": original_text}, compliance_log)

        return {
            **input,
            "user_input": redacted_text,
            "redacted_input": redacted_text,
            "compliance_log": compliance_log,
            "warning": warning_message,
            "risk_level": risk_level,
            "risk_categories_triggered": list(matches.keys()),
            "audit_metadata": {
                "audit_timestamp": compliance_log["audit_timestamp"],
                "compliance_score": 100 if not redaction_occurred else 80,
                "sensitivity_flags": list(matches.keys())
            }
        }
