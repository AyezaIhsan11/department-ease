from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from models.student import Student
from models.user import User
from auth.dependencies import get_current_user
from services.pdf_generator import pdf_generator
from datetime import datetime


router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/monthly")
async def generate_monthly_report(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user)
):
    """Generate monthly PDF report"""
    
    pdf_buffer = pdf_generator.generate_monthly_report(year, month)
    
    filename = f"monthly_report_{year}_{month:02d}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/yearly")
async def generate_yearly_report(
    year: int = Query(..., ge=2000, le=2100),
    current_user: User = Depends(get_current_user)
):
    """Generate yearly PDF report"""
    
    pdf_buffer = pdf_generator.generate_yearly_report(year)
    
    filename = f"yearly_report_{year}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/student-list")
async def generate_student_list_report(
    department: str = None,
    current_user: User = Depends(get_current_user)
):
    """Generate student list PDF report"""
    
    query = {}
    if department:
        query["department"] = department
    
    students = await Student.find(query).to_list()
    
    pdf_buffer = await pdf_generator.generate_student_list_report(students)
    
    filename = f"student_list_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
