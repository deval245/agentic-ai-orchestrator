from langchain_core.runnables import Runnable
from typing import Dict, Any
from langchain_openai import ChatOpenAI
import json

class ResponderAgent(Runnable):
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)

    def invoke(self, input: Dict[str, Any], config: Any = None) -> Dict[str, Any]:
        redacted_input = input.get("redacted_input", input.get("user_input", ""))
        chunks = input.get("retrieved_chunks", [])
        context_text = "\n".join(f"- {c}" for c in chunks) if chunks else "No relevant context found."

        prompt = f"""
You are a helpful and compliance-aligned AI assistant. Your role is to answer user questions using ONLY the provided context and adhering strictly to privacy, safety, and compliance standards.

User Question (redacted for safety):
\"\"\"{redacted_input}\"\"\"

Context from the Document:
{context_text}

Instructions:
- Use ONLY the context to infer a useful, practical answer.
- Avoid hallucinating or making up facts not in the context.
- If unsure, say "Based on the provided context..." and offer general guidance.
- Be helpful, respectful, and clear.
- Ensure answers comply with privacy and PII guidelines. Do not output any sensitive or non-compliant information.

Answer:
"""

        response = self.llm.invoke(prompt)
        raw_output = getattr(response, "content", str(response) if response else "").strip()
        lines = raw_output.split("\n")

        # Separate final answer and structured subtasks if detected
        final_answer_lines = []
        subtask_lines = []
        subtask_section_started = False
        for line in lines:
            if "Step" in line:
                subtask_section_started = True
            if subtask_section_started:
                subtask_lines.append(line.strip())
            else:
                final_answer_lines.append(line.strip())

        final_answer = "\n".join(final_answer_lines).strip()
        subtasks = "\n".join(subtask_lines).strip()

        return {
            "final_answer": final_answer,
            "subtasks": json.loads(json.dumps(subtasks.split("\n"))) if subtasks else []
        }