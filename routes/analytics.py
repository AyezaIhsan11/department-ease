from fastapi import APIRouter, Depends
from models.student import Student, StudentStatus
from models.user import User
from auth.dependencies import get_current_user
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict


router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview")
async def get_overview_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get dashboard overview statistics"""
    
    # Total students
    total_students = await Student.find().count()
    
    # Active students
    active_students = await Student.find(Student.status == StudentStatus.ACTIVE).count()
    
    # Students by status
    inactive_students = await Student.find(Student.status == StudentStatus.INACTIVE).count()
    graduated_students = await Student.find(Student.status == StudentStatus.GRADUATED).count()
    
    # Average GPA
    all_students = await Student.find(Student.gpa != None).to_list()
    avg_gpa = sum(s.gpa for s in all_students if s.gpa) / len(all_students) if all_students else 0
    
    # Students enrolled in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_enrollments = await Student.find(
        Student.enrollment_date >= thirty_days_ago
    ).count()
    
    return {
        "total_students": total_students,
        "active_students": active_students,
        "inactive_students": inactive_students,
        "graduated_students": graduated_students,
        "average_gpa": round(avg_gpa, 2),
        "recent_enrollments": recent_enrollments
    }


@router.get("/department-distribution")
async def get_department_distribution(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get student distribution by department"""
    
    students = await Student.find().to_list()
    
    dept_count = defaultdict(int)
    for student in students:
        dept_count[student.department] += 1
    
    return [
        {"department": dept, "count": count}
        for dept, count in dept_count.items()
    ]


@router.get("/year-distribution")
async def get_year_distribution(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get student distribution by year"""
    
    students = await Student.find().to_list()
    
    year_count = defaultdict(int)
    for student in students:
        year_count[student.year] += 1
    
    return [
        {"year": year, "count": count}
        for year, count in sorted(year_count.items())
    ]


@router.get("/enrollment-trends")
async def get_enrollment_trends(
    months: int = 12,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get enrollment trends over time"""
    
    students = await Student.find().to_list()
    
    # Group by month
    monthly_enrollments = defaultdict(int)
    
    for student in students:
        month_key = student.enrollment_date.strftime('%Y-%m')
        monthly_enrollments[month_key] += 1
    
    # Get last N months
    result = []
    current_date = datetime.utcnow()
    
    for i in range(months - 1, -1, -1):
        target_date = current_date - timedelta(days=i * 30)
        month_key = target_date.strftime('%Y-%m')
        result.append({
            "month": month_key,
            "enrollments": monthly_enrollments.get(month_key, 0)
        })
    
    return result


@router.get("/gpa-distribution")
async def get_gpa_distribution(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get GPA distribution statistics"""
    
    students = await Student.find(Student.gpa != None).to_list()
    
    if not students:
        return {
            "ranges": [],
            "average": 0,
            "highest": 0,
            "lowest": 0
        }
    
    # GPA ranges
    ranges = {
        "0.0-1.0": 0,
        "1.0-2.0": 0,
        "2.0-3.0": 0,
        "3.0-4.0": 0
    }
    
    gpas = [s.gpa for s in students if s.gpa is not None]
    
    for gpa in gpas:
        if gpa < 1.0:
            ranges["0.0-1.0"] += 1
        elif gpa < 2.0:
            ranges["1.0-2.0"] += 1
        elif gpa < 3.0:
            ranges["2.0-3.0"] += 1
        else:
            ranges["3.0-4.0"] += 1
    
    return {
        "ranges": [{"range": k, "count": v} for k, v in ranges.items()],
        "average": round(sum(gpas) / len(gpas), 2),
        "highest": round(max(gpas), 2),
        "lowest": round(min(gpas), 2)
    }
