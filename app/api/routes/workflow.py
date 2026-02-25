from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi import Body

from app.schemas.workflow import WorkflowOut, WorkflowBase, UpdateWorkflow
from app.api.deps import get_db
from app.crud import workflow as crud_workflow
from app.core.security import get_current_user
from app.core.execution_engine import WorkflowExecutor

router = APIRouter(prefix="/workflow")

# Get workflow API 
@router.get("/", response_model=List[WorkflowOut])
def read_workflows(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    return crud_workflow.get_user_workflows(db, user_id=user_id, skip=skip, limit=limit)

# Create workflow API
@router.post("/create", response_model=WorkflowOut)
def create_workflow(workflow_in: WorkflowBase, db:Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    return crud_workflow.create_workflow(
        db,
        user_id=user_id,
        title=workflow_in.title,
        enabled=workflow_in.enabled,
        nodes=workflow_in.nodes,
        connections=workflow_in.connections
    )

@router.get("/trigger-types")
def get_trigger_types():
    # returning dummy data 
    trigger_types = [
        {
            "id": 'MANUAL',
            "label": 'Manual Trigger',
            "color": '#10B981',
            "description": 'Triggered manually by the user',
        }
    ]
    return trigger_types

@router.get("/action-types")
def get_action_types():
    # returning dummy data
    return [
        {
            "id": "telegram-api",
            "label": "Telegram API",
            "color": "#0088CC",
            "description": "Send a message via Telegram",
            "configFields": [
                {
                    "type": "text",
                    "label": "Chat ID",
                    "placeholder": "Enter recipient chat ID",
                    "required": True,
                    "key": "chatId"
                },
                {
                    "type": "textarea",
                    "label": "Message",
                    "placeholder": "Enter your message",
                    "required": True,
                    "key": "message"
                }
            ]
        },
        {
            "id": "email-send",
            "label": "Email Send",
            "color": "#EF4444",
            "description": "Send an email to recipients",
            "configFields": [
                {
                    "type": "email",
                    "label": "Recipient",
                    "placeholder": "recipient@example.com",
                    "required": True,
                    "key": "to"
                },
                {
                    "type": "email",
                    "label": "CC",
                    "placeholder": "cc@example.com",
                    "required": False,
                    "key": "cc"
                },
                {
                    "type": "text",
                    "label": "Subject",
                    "placeholder": "Email subject",
                    "required": True,
                    "key": "subject"
                },
                {
                    "type": "textarea",
                    "label": "Body",
                    "placeholder": "Email content",
                    "required": True,
                    "key": "body"
                }
            ]
        },
        {
            "id": "gemini",
            "label": "Gemini",
            "color": "#6366F1",
            "description": "Use Gemini to generate content",
            "configFields": [
                {
                    "type": "text",
                    "label": "Prompt",
                    "placeholder": "Enter your prompt or query",
                    "required": True,
                    "key": "prompt"
                },
                {
                    "type": "select",
                    "label": "Model",
                    "required": True,
                    "options": [
                        { "label": "Gemini-2.5 Flash", "value": "gemini-2.5-flash" },
                        { "label": "Gemini-3", "value": "gemini-2.5-pro" }
                    ],
                    "key": "model"
                }
            ]
        }
    ]


@router.get("/{workflow_id}", response_model=WorkflowOut)
def read_workflow_by_id(
    workflow_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    workflow = crud_workflow.get_workflow(db, workflow_id=workflow_id, user_id=user_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.put("/{workflow_id}", response_model=WorkflowOut)
def update_workflow_by_id(workflow_id: str, workflow_in: UpdateWorkflow, db:Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    return crud_workflow.update_workflow(
        db,
        workflow_id=workflow_id,
        user_id=user_id,
        nodes=workflow_in.nodes,
        connections=workflow_in.connections
    )

@router.delete("/{workflow_id}", response_model=dict)
def delete_workflow_by_id(
    workflow_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    deleted = crud_workflow.delete_workflow(db, workflow_id=workflow_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found or not authorized")
    return {"detail": "Workflow deleted successfully"}

@router.post("/{workflow_id}/execute")
def execute_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    executor = WorkflowExecutor(workflow_id=workflow_id, user_id=user_id, db=db)
    result = executor.execute()
    return result

@router.patch("/{workflow_id}", response_model=WorkflowOut)
def patch_workflow_title(
    workflow_id: str,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    title = data.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    updated_workflow = crud_workflow.update_workflow_title(
        db=db,
        workflow_id=workflow_id,
        user_id=user_id,
        title=title
    )
    if not updated_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found or not authorized")
    return updated_workflow