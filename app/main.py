from fastapi import FastAPI
from app.api.routes import workflow
from app.api.routes import user
from app.api.routes import credentials
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import oauth
import os
load_dotenv()

app = FastAPI(title="AI Workflow Automator")

cors_origins = os.getenv("CORS_ORIGINS", "")
allowed_origins = [origin.strip() for origin in cors_origins.split(",") if origin]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(workflow.router)
app.include_router(user.router)
app.include_router(credentials.router)
app.include_router(oauth.router)

@app.get("/health")
def health_check():
    return {"message": "Healthy"}
