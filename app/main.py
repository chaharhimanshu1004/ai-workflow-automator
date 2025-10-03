from fastapi import FastAPI
from app.api.routes import workflow
from app.api.routes import user
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
load_dotenv()

app = FastAPI(title="AI Workflow Automator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workflow.router)
app.include_router(user.router)

@app.get("/health")
def health_check():
    return {"message": "Healthy"}
