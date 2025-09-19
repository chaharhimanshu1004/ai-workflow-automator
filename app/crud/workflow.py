from sqlalchemy.orm import Session
from app.models.workflow import Workflow

def get_user_workflows(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return (
        db.query(Workflow)
        .filter(Workflow.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
