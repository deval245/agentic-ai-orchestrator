# app/main.py
from fastapi import FastAPI
from app.agents.routers.agent_router import router as agent_router
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()
app.include_router(agent_router)