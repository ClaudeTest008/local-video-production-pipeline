"""Shared API schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Timestamped(OrmModel):
    id: int
    created_at: datetime
    updated_at: datetime


class Message(BaseModel):
    detail: str
