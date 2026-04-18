from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from models.event import EventCategory


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    category: EventCategory = EventCategory.OTHER


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category: Optional[EventCategory] = None


class EventResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    start_date: datetime
    end_date: datetime
    category: EventCategory
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
