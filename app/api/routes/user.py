from fastapi import APIRouter, HTTPException, Depends, Request, Body
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.users import User
from app.core.config import settings
from jose import jwt
from app.api.deps import get_db
from app.schemas.auth import GoogleTokenRequest
import requests

router = APIRouter()

GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"

@router.post('/auth/google')
def google_signin(token: GoogleTokenRequest, db: Session = Depends(get_db)):
    print('->>>>>>>req comes with payload', payload)
    resp = requests.get(GOOGLE_TOKEN_INFO_URL, params={"id_token": token})
    print('---------response', resp)
    if(resp.status_code != 200):
        raise HTTPException(status_code=401, detail="Invalid Google token")
    data = resp.json()
    email = data.get("email")
    name = data.get("name")

    if not email:
        raise HTTPException(status_code=400, detail="Email not found in Google token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user: 
        user = User(name=name, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    payload = { "sub": str(user.user_id), "email": user.email }
    access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    print('-------access_token', access_token)
    return { "access_token": access_token, "token_type": "bearer" }