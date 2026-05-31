from beanie import Document, Indexed
from pydantic import EmailStr, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class StudentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"


def normalize_degree(dept_str: Optional[str]) -> str:
    """Normalize degree program string to standardized names."""
    if not dept_str:
        return "BS Computer Science (CS)"
    
    val = dept_str.strip().lower()
    
    # 1. Software Engineering
    if "software" in val or "se" == val or "bsse" in val or "bs se" in val:
        return "BS Software Engineering (SE)"
    
    # 2. Artificial Intelligence
    if "artificial" in val or "intelligence" in val or "ai" == val or "bsai" in val or "bs ai" in val:
        return "BS Artificial Intelligence (AI)"
        
    # 3. Data Science
    if "data" in val or "ds" == val or "bsds" in val or "bs ds" in val:
        return "BS Data Science (DS)"
            
    # 4. Information Technology
    if "information" in val or "technology" in val or "it" == val or "bsit" in val or "bs it" in val:
        return "BS Information Technology (IT)"
        
    # 5. Computer Science
    if "computer" in val or "cs" == val or "bscs" in val or "bs cs" in val or "science" in val:
        return "BS Computer Science (CS)"
        
    # Fallback to Title Case of the input if unrecognized
    return dept_str.strip().title()


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

