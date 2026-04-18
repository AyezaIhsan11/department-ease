from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId


class ChatHistory(Document):
    user_id: ObjectId  # Reference to User
    conversation_id: str  # Session identifier
    message: str
    response: str
    action_taken: Optional[Dict[str, Any]] = None  # Details of action performed
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "chat_history"
        indexes = [
            "user_id",
            "conversation_id",
            "timestamp"
        ]
        
    model_config = {
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "message": "Add a new student named John Doe",
                "response": "I've added John Doe to the student database.",
                "action_taken": {
                    "action": "create_student",
                    "student_id": "CS2024001"
                }
            }
        }
    }

