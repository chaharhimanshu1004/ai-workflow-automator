from sqlalchemy import Column, String, DateTime, func
from app.db.base import Base
import uuid

class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    header = Column(String, nullable=True)
    secret = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
