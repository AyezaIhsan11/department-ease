from beanie import Document, Indexed
from pydantic import EmailStr, Field
from datetime import datetime
from passlib.context import CryptContext
from enum import Enum
from typing import Optional


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class UserRole(str, Enum):
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class User(Document):
    username: Indexed(str, unique=True)
    email: Indexed(EmailStr, unique=True)
    password_hash: str
    role: UserRole = UserRole.ADMIN
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(password, self.password_hash)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    class Settings:
        name = "users"
        indexes = [
            "username",
            "email"
        ]
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "username": "admin",
                "email": "admin@university.edu",
                "role": "admin"
            }
        }
    }

