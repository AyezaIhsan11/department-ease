from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "department_ease"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Gemini AI
    GEMINI_API_KEY: Optional[str] = None
    
    # SMTP
    SMTP_HOST: Optional[str] = "smtp.gmail.com"
    SMTP_PORT: Optional[int] = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: Optional[str] = "Department Ease"
    
    # Resend Email API (Optional, used if SMTP is blocked in cloud environments)
    RESEND_API_KEY: Optional[str] = None
    
    # Brevo Email API (Optional)
    BREVO_API_KEY: Optional[str] = None
    
    # Redis
    REDIS_URL: Optional[str] = None
    
    # Application
    APP_NAME: str = "Department Ease"
    CORS_ORIGINS: str = "http://localhost:3000"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8001"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        import os
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", ".env") if "backend" not in os.path.basename(os.path.dirname(os.path.abspath(__file__))) else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        case_sensitive = True


settings = Settings()
