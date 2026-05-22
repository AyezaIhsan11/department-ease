from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional
from enum import Enum


class EventCategory(str, Enum):
    ACADEMIC = "academic"
    EXAMINATION = "examination"
    HOLIDAY = "holiday"
    WORKSHOP = "workshop"
    SEMINAR = "seminar"
    CULTURAL = "cultural"
    SPORTS = "sports"
    OTHER = "other"


class Event(Document):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    category: EventCategory = EventCategory.OTHER
    created_by: str  # username of creator
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "events"
        indexes = [
            "start_date",
            "category",
            "created_by"
        ]
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "title": "Mid-Term Examinations",
                "description": "Mid-term exams for all departments",
                "start_date": "2024-03-15T09:00:00",
                "end_date": "2024-03-22T17:00:00",
                "category": "examination"
            }
        }
    }
