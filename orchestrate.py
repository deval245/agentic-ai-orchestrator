# orchestrate.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List

from dotenv import load_dotenv
import os

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("❌ OPENAI_API_KEY is not set in environment or .env file.")

from agents.compliance import ComplianceVerifierAgent
from agents.planner import PlannerAgent
from agents.retriever import RetrieverAgent
from agents.responder import ResponderAgent
from agents.verifier import VerifierAgent

# 1. Define Shared State
task_input = Annotated[str, "user_input"]
chunks = Annotated[List[str], "retrieved_chunks"]
subtasks = Annotated[List[str], "subtasks"]
final_answer = Annotated[str, "final_answer"]

class AgentState(TypedDict, total=False):
    user_input: str
    redacted_input: str
    uploaded_file_path: str
    retrieved_chunks: List[str]
    subtasks: List[str]
    final_answer: str
    compliance_log_summary: dict
    audit_metadata: dict
    warning: str
    risk_level: str
    risk_categories_triggered: List[str]

def score_and_filter_chunks(chunks: List[str], query: str, threshold: float = 0.7) -> List[str]:
    if not chunks or not query:
        return chunks

    embeddings = OpenAIEmbeddings()
    query_emb = embeddings.embed_query(query)
    chunk_docs = [Document(page_content=c) for c in chunks]
    vectorstore = FAISS.from_documents(chunk_docs, embeddings)

    scores_and_docs = vectorstore.similarity_search_with_score_by_vector(query_emb, k=len(chunks))
    return [doc.page_content.replace("\n", " ") for doc, score in scores_and_docs if score >= threshold]

# 2. Initialize agents
compliance = ComplianceVerifierAgent()
planner = PlannerAgent(api_key=os.getenv("OPENAI_API_KEY"))
retriever = RetrieverAgent()
responder = ResponderAgent()
verifier = VerifierAgent()

# 3. Create graph
graph = StateGraph(AgentState)
graph.add_node("compliance", compliance)
graph.add_node("planner", planner)
graph.add_node("retriever", retriever)
graph.add_node("responder", responder)
graph.add_node("verifier", verifier)

# 4. Define edges
graph.set_entry_point("compliance")
graph.add_edge("compliance", "planner")
graph.add_edge("planner", "retriever")
graph.add_edge("retriever", "responder")
graph.add_edge("responder", "verifier")
graph.add_edge("verifier", END)

# 5. Compile
dag_executor = graph.compile()


# Export graph structure to DOT format for visualization
with open("graph_structure.dot", "w") as f:
    f.write(graph.compile().get_graph().to_dot())
print("✅ DOT file for LangGraph structure saved as 'graph_structure.dot'")


def run_graph(state: AgentState, config=None):
    if "retrieved_chunks" in state:
        cleaned_chunks = [chunk.replace("\\n", "\n").replace("\n", " ") for chunk in state["retrieved_chunks"]]
        query = state.get("redacted_input") or state.get("user_input", "")
        state["retrieved_chunks"] = score_and_filter_chunks(cleaned_chunks, query)
    return dag_executor.invoke(state, config=config)


def build_agent_graph():
    return graph


def workflow():
    from orchestrate import build_agent_graph
    return build_agent_graph()