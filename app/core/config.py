from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    MIGRATION_DATABASE_URL: str

    GMAIL_CLIENT_ID: str
    GMAIL_CLIENT_SECRET: str
    GMAIL_REDIRECT_URI: str
    
    CORS_ORIGINS: str 

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
