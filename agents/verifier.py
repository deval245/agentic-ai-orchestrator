from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
import os

class VerifierAgent(Runnable):
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ OPENAI_API_KEY is missing. Set it in your .env file or environment.")
        self.llm = ChatOpenAI(temperature=0, api_key=api_key)

    def choose_verification_strategy(self, user_input: str, config: dict = None) -> str:
        meta_prompt = f"""
You are a strategy selector for validating AI-generated answers.
Given the user query below, select the best verification strategy:
- If it's a fact-based or data-driven query, return 'Strict'.
- If it's subjective or opinion-based, return 'Lenient'.
- If it's unclear or vague, return 'Ask Clarification'.

User Query:
{user_input}

Respond with one word only: Strict / Lenient / Ask Clarification
"""
        response = self.llm.invoke(meta_prompt)
        return response.content.strip()

    def invoke(self, input: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
        answer = input.get("final_answer", "")
        user_input = input.get("user_input", "")

        strategy = self.choose_verification_strategy(user_input, config)

        if strategy == "Ask Clarification":
            return {
                **input,
                "verification_result": "Please clarify your query for accurate verification."
            }

        prompt = f"""
You are a fact-checking and validation agent.
Verification Strategy: {strategy}

Your task is to verify the following answer:
---
Question: {user_input}
Answer: {answer}
---

✅ If the answer is accurate, return a short confirmation like "Verified: Looks good."
❌ If the answer is vague or not based on the input, return "Needs improvement" and explain why.
"""
        result = self.llm.invoke(prompt)
        return {
            **input,
            "verification_result": result.content.strip()
        }
