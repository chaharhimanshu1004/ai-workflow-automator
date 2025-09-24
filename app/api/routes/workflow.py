from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.schemas.workflow import WorkflowOut, WorkflowBase
from app.api.deps import get_db
from app.crud import workflow as crud_workflow
from app.core.security import get_current_user

router = APIRouter()

# Get workflow API 
@router.get("/workflow", response_model=List[WorkflowOut])
def read_workflows(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    return crud_workflow.get_user_workflows(db, user_id=user_id, skip=skip, limit=limit)

# Create workflow API
@router.post("/create-workflow", response_model=WorkflowOut)
def create_workflow(workflow_in: WorkflowBase, db:Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    return crud_workflow.create_workflow(
        db,
        user_id=user_id,
        title=workflow_in.title,
        enabled=workflow_in.enabled,
        nodes=workflow_in.nodes,
        connections=workflow_in.connections
    )