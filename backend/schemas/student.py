from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from models.student import StudentStatus


# Request Schemas
class StudentCreate(BaseModel):
    student_id: str
    first_name: str
    last_name: str
    email: EmailStr
    department: str
    year: int = Field(ge=1, le=8)
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    contact_number: Optional[str] = None
    address: Optional[str] = None
    courses: List[str] = Field(default_factory=list)


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    year: Optional[int] = Field(None, ge=1, le=8)
    status: Optional[StudentStatus] = None
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    contact_number: Optional[str] = None
    address: Optional[str] = None
    courses: Optional[List[str]] = None


# Response Schemas
class StudentResponse(BaseModel):
    id: str
    student_id: str
    first_name: str
    last_name: str
    email: EmailStr
    department: str
    year: int
    enrollment_date: datetime
    status: StudentStatus
    gpa: Optional[float]
    contact_number: Optional[str]
    address: Optional[str]
    courses: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StudentListResponse(BaseModel):
    students: List[StudentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BulkDeleteRequest(BaseModel):
    student_ids: List[str]
