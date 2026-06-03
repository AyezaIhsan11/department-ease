from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import os
import uuid
from datetime import datetime
from models.voucher import Voucher
from models.student import Student
from auth.dependencies import get_current_user
from services.email_service import email_service
import asyncio

router = APIRouter(prefix="/api/vouchers", tags=["vouchers"])

UPLOAD_DIR = "uploads/vouchers"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/{student_id}")
async def upload_voucher(student_id: str, file: UploadFile = File(...)):
    """Upload a voucher for a student"""
    
    # Check if student exists
    student = await Student.find_one(Student.student_id == student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check file type
    allowed_extensions = {".jpg", ".jpeg", ".png", ".pdf"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: JPG, PNG, PDF")
    
    # Generate unique filename
    filename = f"{student_id}_{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
    
    # Create database record
    voucher = Voucher(
        student_id=student_id,
        student_name=student.full_name,
        filename=filename,
        file_path=f"/uploads/vouchers/{filename}"
    )
    await voucher.insert()
    
    return {"message": "Voucher uploaded successfully", "voucher_id": str(voucher.id)}

@router.get("", response_model=List[Voucher])
async def get_all_vouchers(current_user: dict = Depends(get_current_user)):
    """Get all vouchers (Admin only)"""
    return await Voucher.find_all().sort("-upload_date").to_list()

@router.get("/student/{student_id}", response_model=List[Voucher])
async def get_student_vouchers(student_id: str, current_user: dict = Depends(get_current_user)):
    """Get vouchers for a specific student"""
    return await Voucher.find(Voucher.student_id == student_id).sort("-upload_date").to_list()

@router.patch("/{voucher_id}/status")
async def update_voucher_status(voucher_id: str, status: str, current_user: dict = Depends(get_current_user)):
    """Update voucher status"""
    voucher = await Voucher.get(voucher_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    voucher.status = status
    await voucher.save()
    
    # Notify student
    student = await Student.find_one(Student.student_id == voucher.student_id)
    if student and student.email:
        subject = f"Fee Voucher Status Update"
        body = f"""
        <h2>Voucher Status Updated</h2>
        <p>Dear {student.first_name},</p>
        <p>The status of your fee voucher has been updated to: <strong>{status}</strong>.</p>
        <p>If you have any questions, please contact the administration office.</p>
        <br>
        <p>Best regards,<br>Department Administration Team</p>
        """
        asyncio.create_task(
            email_service.send_email(
                to_emails=[student.email],
                subject=subject,
                body=body,
                html=True
            )
        )
    
    return {"message": f"Voucher status updated to {status}"}

@router.delete("/{voucher_id}")
async def delete_voucher(voucher_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a voucher (removes DB record and file from disk)"""
    voucher = await Voucher.get(voucher_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")

    # Remove file from disk
    disk_path = os.path.join(UPLOAD_DIR, voucher.filename)
    if os.path.exists(disk_path):
        try:
            os.remove(disk_path)
        except Exception:
            pass  # Non-fatal — still delete the DB record

    await voucher.delete()
    return {"message": "Voucher deleted successfully"}
