from pydantic import BaseModel

class GoogleTokenRequest(BaseModel):
    credential: str