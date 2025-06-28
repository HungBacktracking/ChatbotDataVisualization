from datetime import datetime
from typing import Optional

from sqlmodel import Column, DateTime, Field, func, Index
from app.model.base_model import BaseModel
from sqlalchemy import Text

class User(BaseModel, table=True):
    __table_args__ = (
        Index("ix_user", "id", "email", unique=True),
    )

    email: str = Field(unique=True)
    password: str = Field()
    name: Optional[str] = Field(default=None, nullable=True)

    created_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), default=func.now()))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), default=func.now(), onupdate=func.now()))
    deleted_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
