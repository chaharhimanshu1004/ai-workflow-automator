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
        created_at=datetime.isoformat(),
        updated_at=datetime.isoformat()
    )
    db.add(new_workflow)
    db.commit()
    db.refresh(new_workflow)
    return new_workflow
