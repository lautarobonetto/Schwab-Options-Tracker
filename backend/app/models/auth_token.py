from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db.base import Base

class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(Text, nullable=False)  # Encrypted
    refresh_token = Column(Text, nullable=False) # Encrypted
    id_token = Column(Text, nullable=True)       # Encrypted
    token_type = Column(String, default="Bearer")
    expires_at = Column(DateTime, nullable=False)
