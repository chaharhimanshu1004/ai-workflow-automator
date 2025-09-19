from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base
import uuid

class Credential(Base):
    __tablename__ = "credentials"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    data = Column(JSONB, nullable=False)  # stores JSON securely
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())