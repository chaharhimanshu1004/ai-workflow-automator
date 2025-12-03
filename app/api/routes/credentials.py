from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_user
from app.crud import credentials as crud_credentials
from app.schemas.credentials import CredentialCreate

router = APIRouter()

@router.post("/save-creds")
def save_creds(credential: CredentialCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    return crud_credentials.save_creds(db, user_id, credential.title, credential.platform, credential.data)

@router.get("/credentials")
def get_credentials(db: Session = Depends(get_db),user_id: str = Depends(get_current_user)):
    return crud_credentials.get_user_credentials(db, user_id=user_id)

@router.delete("/credentials/{credential_id}", response_model=dict)
def delete_credential(
    credential_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    deleted = crud_credentials.delete_credential(db, credential_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Credential not found or not authorized")
    return {"detail": "Credential deleted successfully"}