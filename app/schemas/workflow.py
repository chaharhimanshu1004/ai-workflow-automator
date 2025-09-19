from pydantic import BaseModel
from typing import Any
from datetime import datetime

class WorkflowBase(BaseModel):
    title: str
    enabled: bool
    nodes: Any
    connections: Any

class WorkflowOut(WorkflowBase):
    id: str
    created_at: datetime
    updated_at: datetime | None

    class Config:
        orm_mode = True
