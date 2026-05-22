from beanie import Document, Indexed
from pydantic import EmailStr, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class StudentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"


class Student(Document):
    student_id: Indexed(str, unique=True)
    first_name: str
    last_name: str
    email: Indexed(EmailStr, unique=True)
    department: str
    year: int = Field(ge=1, le=8)  # 1-8 years
    enrollment_date: datetime = Field(default_factory=datetime.utcnow)
    status: StudentStatus = StudentStatus.ACTIVE
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    contact_number: Optional[str] = None
    address: Optional[str] = None
    courses: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    class Settings:
        name = "students"
        indexes = [
            "student_id",
            "email",
            "department",
            "status"
        ]
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "student_id": "CS2024001",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@university.edu",
                "department": "Computer Science",
                "year": 2,
                "gpa": 3.5,
                "contact_number": "+1234567890",
                "courses": ["Data Structures", "Algorithms", "Databases"]
            }
        }
    }

