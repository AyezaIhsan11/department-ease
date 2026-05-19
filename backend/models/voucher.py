from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime
from typing import Optional


class Voucher(Document):
    student_id: Indexed(str)
    student_name: str
    filename: str
    file_path: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, verified, rejected
    notes: Optional[str] = None

    class Settings:
        name = "vouchers"
        indexes = [
            "student_id",
            "upload_date",
            "status"
        ]
