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

from app.models.credentials import Credential

def get_user_credentials(db: Session, user_id: str):
    results = db.query(
        Credential.id,
        Credential.user_id,
        Credential.title,
        Credential.platform,
        Credential.created_at,
        Credential.updated_at
    ).filter(Credential.user_id == user_id).all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "title": r.title,
            "platform": r.platform,
            "created_at": r.created_at,
            "updated_at": r.updated_at
        }
        for r in results
    ]

def delete_credential(db: Session, credential_id: str, user_id: str):
    credential = db.query(Credential).filter(
        Credential.id == credential_id,
        Credential.user_id == user_id
    ).first()
    if not credential:
        return False
    db.delete(credential)
    db.commit()
    return True

def get_credential_by_platform(db: Session, user_id: str, platform: str):
    return db.query(Credential).filter(
        Credential.user_id == user_id,
        Credential.platform == platform
    ).first()
