from fastapi import FastAPI
from app.api.routes import workflow

app = FastAPI(title="AI Workflow Automator")

app.include_router(workflow.router)
