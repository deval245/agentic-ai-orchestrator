# app/routers/agent_router.py

from fastapi import APIRouter, UploadFile, File, Form
from orchestrate import run_graph
import tempfile
import shutil

router = APIRouter()

@router.post("/run-agent")
async def run_agent(user_input: str = Form(...), file: UploadFile = File(...)):
    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    payload = {
        "user_input": user_input,
        "uploaded_file_path": tmp_path,
        "subtasks": [],
        "retrieved_chunks": [],
        "final_answer": "",
        "warning": "",
        "compliance_log": {},
        "audit_metadata": {},
        "risk_level": "",
        "risk_categories_triggered": []
    }

    result = run_graph(payload)
    return result