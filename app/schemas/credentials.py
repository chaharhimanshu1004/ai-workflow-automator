from pydantic import BaseModel
from typing import Any, Dict

class CredentialCreate(BaseModel):
    title: str
    platform: str
    data: Dict[str, Any]