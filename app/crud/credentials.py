from sqlalchemy.orm import Session
from app.models.credentials import Credential
import json


def save_creds(db: Session, user_id: str, title: str, platform: str, data: str):
    json_data = json.loads(data) if isinstance(data, str) else data
    credential = Credential(
        user_id=user_id,
        title=title,
        platform=platform,
        data=json_data
    )

    db.add(credential)
    db.commit()
    db.refresh(credential)
    return credential
