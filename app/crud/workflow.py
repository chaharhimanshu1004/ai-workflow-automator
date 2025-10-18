from sqlalchemy.orm import Session
from app.models.workflow import Workflow
from datetime import datetime

def get_user_workflows(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return (
        db.query(Workflow)
        .filter(Workflow.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_workflow(db: Session, user_id: str, title: str, enabled: bool, nodes: dict, connections: dict):
    new_workflow = Workflow(
        user_id=user_id,
        title=title,
        enabled=enabled,
        nodes=nodes,
        connections=connections,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(new_workflow)
    db.commit()
    db.refresh(new_workflow)
    return new_workflow

def get_workflow(db: Session, workflow_id: str, user_id: str):
    return db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.user_id == user_id
    ).first()

def update_workflow(db: Session, workflow_id: str, user_id: str, nodes: dict = None, connections: dict = None):
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.user_id == user_id
    ).first()

    if not workflow:
        return None
    
    if nodes is not None:
        workflow.nodes = nodes
    if connections is not None:
        workflow.connections = connections

    workflow.updated_at = datetime.now()
    db.commit()
    db.refresh(workflow)
    
    return workflow

