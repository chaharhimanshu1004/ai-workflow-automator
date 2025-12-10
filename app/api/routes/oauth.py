from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests
import secrets
from urllib.parse import urlencode
import os

from app.api.deps import get_db
from app.core.security import get_current_user
from app.crud import credentials as crud_credentials

router = APIRouter(prefix="/oauth")

# Gmail OAuth configuration
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI")
GMAIL_SCOPES = "https://www.googleapis.com/auth/gmail.send"

@router.get("/gmail/authorize")
def gmail_oauth_authorize(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):  
    if not all([GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REDIRECT_URI]):
        raise HTTPException(status_code=500, detail="Gmail OAuth not configured")
    
    state = "gmail_oauth"
    
    auth_params = {
        "client_id": GMAIL_CLIENT_ID,
        "redirect_uri": GMAIL_REDIRECT_URI,
        "scope": GMAIL_SCOPES,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "state": state
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(auth_params)}"
    
    return {"auth_url": auth_url}

@router.post("/gmail/callback")
def gmail_oauth_callback(
    callback_data: dict,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    code = callback_data.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code required")
    print('REQUEST HERE', code)
    token_data = {
        "client_id": GMAIL_CLIENT_ID,
        "client_secret": GMAIL_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GMAIL_REDIRECT_URI,
    }
    print('TOKEN DATA',token_data)
    
    try:
        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data=token_data
        )
        print('RESPONSE', response)
        response.raise_for_status()
        tokens = response.json()
        
        user_info_response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        user_info = user_info_response.json()
        user_email = user_info.get("email", "Unknown")
        
        credential_data = {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "token_type": tokens.get("token_type", "Bearer"),
            "expires_in": tokens.get("expires_in"),
            "user_email": user_email
        }

        print('CREDENTIALS DATA', credential_data)
        
        crud_credentials.save_creds(
            db=db,
            user_id=user_id,
            title=f"Gmail - {user_email}",
            platform="gmail",
            data=credential_data
        )
        
        return {"message": "Gmail credentials saved successfully", "email": user_email}
        
    except requests.RequestException as e:
        print('ERROR --> ', e)
        raise HTTPException(status_code=400, detail=f"Failed to exchange code for tokens: {str(e)}")
    except Exception as e:
        print('ERROR --> ', e)
        raise HTTPException(status_code=500, detail=f"Error saving credentials: {str(e)}")