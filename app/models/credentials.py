from sqlalchemy import Column, String,Integer ,DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base
import uuid

class Credential(Base):
    __tablename__ = "credentials"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    title = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())