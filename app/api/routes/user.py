from fastapi import APIRouter, HTTPException, Depends, Request, Body
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.users import User
from app.core.config import settings
from jose import jwt, JWTError
from app.api.deps import get_db
from app.schemas.auth import GoogleTokenRequest
from app.models.token import Token
import requests

router = APIRouter()

GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"

@router.post('/auth/google')
async def google_signin(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    token = body["token"]
    resp = requests.get(GOOGLE_TOKEN_INFO_URL, params={"id_token": token})
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
    token_obj = db.query(Token).filter(Token.user_id == user.user_id).first()
    if token_obj:
        token_obj.token = access_token
    else:
        token_obj = Token(user_id=user.user_id, token=access_token)
        db.add(token_obj)
    db.commit()
    return { "access_token": access_token, "token_type": "bearer" }

@router.get('/user/profile')
async def get_user_profile(request: Request, db: Session = Depends(get_db)):
    authorization: str = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
        token_obj = db.query(Token).filter(Token.token == token).first()
        if not token_obj:
            raise HTTPException(status_code=401, detail="Token not found or expired")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email
        }
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")