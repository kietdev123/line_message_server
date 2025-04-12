from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    line_user_id = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Nonce(Base):
    __tablename__ = "nonces"

    id = Column(Integer, primary_key=True, index=True)
    nonce = Column(String(255), unique=True, index=True)
    username = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow) 