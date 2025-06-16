# agents/planner.py

import os
from typing import Dict, Any, List
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import TextLoader
from utils.log_agent_output import log_agent_output
import ast
from langchain_core.messages import AIMessage

class PlannerAgent(Runnable):
    def __init__(self, api_key: str = None):
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            print("🔍 DEBUG: Missing OPENAI_API_KEY. Check your environment variables or pass api_key explicitly.")
            raise ValueError("❌ OPENAI_API_KEY is not set in environment or passed explicitly.")
        self.llm = ChatOpenAI(temperature=0, api_key=key)

    def infer_query_from_doc(self, file_path: str) -> str:
        try:
            loader = TextLoader(file_path)
            text = loader.load()[0].page_content[:1000]
            prompt = (
                f"The following is the start of a document:\n\n{text}\n\n"
                "User didn't provide a query. Suggest a clear task they might want (e.g. summarizing, extracting key points). "
                "Return a concise user-like instruction."
            )
            resp = self.llm.invoke(prompt)
            if hasattr(resp, "content"):
                task = resp.content.strip()
            else:
                task = str(resp).strip()
            log_agent_output("Planner::infer_query", {"file_snippet": text[:200]}, {"query": task})
            return task
        except Exception as e:
            log_agent_output("Planner::infer_query_error", {"file_path": file_path}, {"error": str(e)})
            return "Please provide a query or a valid document."

    def choose_strategy(self, user_input: str) -> str:
        try:
            resp = self.llm.invoke(
                f"User query: {user_input}. Is this a direct, structured, or unclear request? Direct/Structured/Ask Clarification."
            )
            choice = resp.content.strip()
            log_agent_output("Planner::strategy", {"query": user_input}, {"choice": choice})
            return choice
        except Exception as e:
            log_agent_output("Planner::strategy_error", {"query": user_input}, {"error": str(e)})
            return "Ask Clarification"

    def invoke(self, input: Dict[str, Any], config: Any = None) -> List[str]:
        ui = input.get("user_input", "")
        if isinstance(ui, AIMessage):
            ui = ui.content.strip()
        else:
            ui = str(ui).strip()
        # Auto-infer query from document if user input is empty
        if not ui and input.get("uploaded_file_path"):
            ui = self.infer_query_from_doc(input["uploaded_file_path"])

        strat = self.choose_strategy(ui)
        # Guardrails for safety and routing context
        if not strat:
            return ["Unable to determine a strategy. Please try again."]
        if strat == "Ask Clarification":
            return ["Please clarify your task or ask a specific question."]
        if strat == "Direct":
            return [ui]

        resp = self.llm.invoke(
            f"User wants a structured set of steps: {ui}\n"
            "Make 3–7 clear, concise bullet points (JSON list)."
        )
        steps_json = resp.content.strip()
        try:
            steps_dict = ast.literal_eval(steps_json)
            if isinstance(steps_dict, dict):
                steps = [f"{step}: {desc}" for step, desc in steps_dict.items()]
            elif isinstance(steps_dict, list):
                steps = [str(item) for item in steps_dict]
            else:
                raise ValueError("Parsed content is neither a list nor a dict.")
        except Exception as e:
            log_agent_output("Planner::steps_eval_error", {"raw_response": steps_json}, {"error": str(e)})
            steps = [steps_json]
        log_agent_output("Planner::steps", {"query": ui}, {"steps": steps})
        steps = [s.replace("\\n", "\n") for s in steps]
        # Ensure output is a dictionary for LangGraph state
        return {"subtasks": steps}
