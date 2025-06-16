from dotenv import load_dotenv
import os
from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, END


from agents.compliance import ComplianceVerifierAgent
from agents.planner import PlannerAgent
from agents.retriever import RetrieverAgent
from agents.responder import ResponderAgent

load_dotenv()

# 🧠 Define Stateful Agent Memory
class AgentState(TypedDict):
    user_input: str
    uploaded_file_path: str
    subtasks: List[str]
    retrieved_chunks: List[str]
    final_answer: str
    warning: str
    compliance_log: dict
    audit_metadata: dict
    risk_level: str
    risk_categories_triggered: List[str]

# 🛡️ Node: Compliance Verification
def compliance_node(state: AgentState) -> AgentState:
    verifier = ComplianceVerifierAgent()
    output = verifier.invoke({"user_input": state["user_input"]})
    return {
        **state,
        "user_input": output.get("user_input", state["user_input"]),
        "warning": output.get("warning", ""),
        "compliance_log": output.get("compliance_log", {}),
        "audit_metadata": output.get("audit_metadata", {}),
        "risk_level": output.get("risk_level", ""),
        "risk_categories_triggered": output.get("risk_categories_triggered", [])
    }

# 📋 Node: Planner
def planner_node(state: AgentState) -> AgentState:
    planner = PlannerAgent(api_key=os.getenv("OPENAI_API_KEY"))
    user_input = state["user_input"]

    if not user_input.strip():
        user_input = planner.infer_query_from_doc(state["uploaded_file_path"])

    subtasks = planner.invoke({
        "user_input": user_input,
        "uploaded_file_path": state["uploaded_file_path"]
    })

    if subtasks == ["Please clarify your query for effective task planning."]:
        subtasks = ["Break down the query and retrieve the most relevant principles from the document."]

    if not subtasks or not isinstance(subtasks, list):
        subtasks = ["Process the query directly"]

    return {
        **state,
        "user_input": user_input,
        "subtasks": subtasks
    }

# 🔍 Node: Retriever
def retriever_node(state: AgentState) -> AgentState:
    retriever = RetrieverAgent()
    subtasks = state.get("subtasks", [])

    if not subtasks:
        return {
            **state,
            "retrieved_chunks": ["⚠️ No subtasks provided to retrieve."]
        }

    # Use user_input if subtask is too generic
    subtask_query = subtasks[0]
    if subtask_query.lower() == "process the query directly":
        subtask_query = state["user_input"]

    chunks = retriever.invoke({
        "subtask": subtask_query,
        "user_input": state["user_input"],
        "uploaded_file_path": state["uploaded_file_path"]
    })

    return {
        **state,
        "retrieved_chunks": chunks
    }

# 🧠 Node: Responder
# 🧠 Responder Node
def responder_node(state: AgentState) -> AgentState:
    responder = ResponderAgent()
    chunks = state.get("retrieved_chunks", [])

    if not chunks or "⚠️" in chunks[0]:
        return {
            **state,
            "final_answer": "❗ Could not extract enough relevant content from the document.",
            "subtasks": ["Try uploading a clearer file or rephrasing your input."]
        }

    print("\n📄 Retrieved Chunks:")
    for chunk in chunks:
        print("-", chunk[:200])  # first 200 chars

    if state.get("warning"):
        print(f"\n⚠️ Compliance Warning: {state['warning']}")

    try:
        answer = responder.invoke({
            "user_input": state["user_input"],
            "retrieved_chunks": chunks
        })
    except Exception as e:
        answer = f"❌ Error in responder: {e}"

    return {
        **state,
        "final_answer": answer,
        "compliance_log": state.get("compliance_log"),
        "warning": state.get("warning"),
        "audit_metadata": state.get("audit_metadata"),
        "risk_level": state.get("risk_level"),
        "risk_categories_triggered": state.get("risk_categories_triggered")
    }
# 🧩 LangGraph Flow Definition
def build_agent_graph():
    workflow = StateGraph(AgentState)

    # Register nodes
    workflow.add_node("compliance", compliance_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("responder", responder_node)

    # Define flow
    workflow.set_entry_point("compliance")
    workflow.add_edge("compliance", "planner")
    workflow.add_edge("planner", "retriever")
    workflow.add_edge("retriever", "responder")
    workflow.add_edge("responder", END)

    return workflow.compile()

# 🧪 Standalone CLI for Testing
if __name__ == "__main__":
    graph = build_agent_graph()

    user_input = "Explain leadership principles"
    uploaded_file_path = "temp_docs/Amazon Leadership Principles.docx.pdf"

    result = graph.invoke({
        "user_input": user_input,
        "uploaded_file_path": uploaded_file_path,
        "subtasks": [],
        "retrieved_chunks": [],
        "final_answer": "",
        "warning": "",
        "compliance_log": {},
        "audit_metadata": {},
        "risk_level": "",
        "risk_categories_triggered": []
    })

    print("\n✅ Final Answer:")
    print(result["final_answer"])

    print("\n⚠️ Warning:")
    print(result.get("warning", "None"))

    print("\n📋 Subtasks:")
    for idx, task in enumerate(result["subtasks"], 1):
        print(f"{idx}. {task}")

    print("\n🛡️ Compliance Log:")
    print(result.get("compliance_log", {}))

    print("\n📊 Audit Metadata:")
    print(result.get("audit_metadata", {}))

    print("\n🔥 Risk Level:", result.get("risk_level", "Unknown"))
    print("🚩 Risk Categories:", result.get("risk_categories_triggered", []))