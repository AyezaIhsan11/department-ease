from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from models.student import Student, StudentStatus
from models.user import User
from schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentListResponse,
    BulkDeleteRequest
)
from auth.dependencies import get_current_user
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import pandas as pd
import io
import csv


router = APIRouter(prefix="/api/students", tags=["Students"])


def student_to_response(student: Student) -> StudentResponse:
    """Convert Student model to response schema"""
    return StudentResponse(
        id=str(student.id),
        student_id=student.student_id,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.email,
        department=student.department,
        year=student.year,
        enrollment_date=student.enrollment_date,
        status=student.status,
        gpa=student.gpa,
        contact_number=student.contact_number,
        address=student.address,
        courses=student.courses,
        created_at=student.created_at,
        updated_at=student.updated_at
    )


@router.get("", response_model=StudentListResponse)
async def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[StudentStatus] = None,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Get list of students with pagination and filters"""
    
    # Build query
    query = {}
    
    if search:
        query["$or"] = [
            {"student_id": {"$regex": search, "$options": "i"}},
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    if department:
        query["department"] = department
    
    if status:
        query["status"] = status
    
    if year:
        query["year"] = year
    
    # Get total count
    total = await Student.find(query).count()
    
    # Calculate pagination
    skip = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size
    
    # Get students
    students = await Student.find(query).skip(skip).limit(page_size).to_list()
    
    return StudentListResponse(
        students=[student_to_response(s) for s in students],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a single student by ID"""
    
    student = await Student.find_one(Student.student_id == student_id)
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    return student_to_response(student)


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new student"""
    
    # Check if student_id already exists
    existing = await Student.find_one(Student.student_id == student_data.student_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student ID already exists"
        )
    
    # Check if email already exists
    existing_email = await Student.find_one(Student.email == student_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create student
    student = Student(**student_data.model_dump())
    await student.insert()
    
    return student_to_response(student)


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: str,
    student_data: StudentUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a student"""
    
    student = await Student.find_one(Student.student_id == student_id)
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Update fields
    update_data = student_data.model_dump(exclude_unset=True)
    
    # Check email uniqueness if email is being updated
    if "email" in update_data:
        existing_email = await Student.find_one(
            Student.email == update_data["email"],
            Student.student_id != student_id
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    for field, value in update_data.items():
        setattr(student, field, value)
    
    student.updated_at = datetime.utcnow()
    await student.save()
    
    return student_to_response(student)


@router.delete("/{student_id}")
async def delete_student(
    student_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a student"""
    
    student = await Student.find_one(Student.student_id == student_id)
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    await student.delete()
    
    return {"message": "Student deleted successfully"}


@router.post("/bulk/delete")
async def bulk_delete_students(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user)
):
    """Bulk delete students"""
    
    deleted_count = 0
    errors = []
    
    for student_id in request.student_ids:
        student = await Student.find_one(Student.student_id == student_id)
        if student:
            await student.delete()
            deleted_count += 1
        else:
            errors.append(f"Student {student_id} not found")
    
    return {
        "deleted_count": deleted_count,
        "total_requested": len(request.student_ids),
        "errors": errors
    }


@router.post("/upload/csv")
async def upload_students_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload students from CSV file"""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        required_columns = ['student_id', 'first_name', 'last_name', 'email', 'department', 'year']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        created_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Check if student already exists
                existing = await Student.find_one(Student.student_id == row['student_id'])
                if existing:
                    errors.append(f"Row {index + 1}: Student ID {row['student_id']} already exists")
                    continue
                
                # Create student
                student_data = {
                    'student_id': row['student_id'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'email': row['email'],
                    'department': row['department'],
                    'year': int(row['year'])
                }
                
                # Optional fields
                if 'gpa' in df.columns and pd.notna(row['gpa']):
                    student_data['gpa'] = float(row['gpa'])
                if 'contact_number' in df.columns and pd.notna(row['contact_number']):
                    student_data['contact_number'] = str(row['contact_number'])
                if 'address' in df.columns and pd.notna(row['address']):
                    student_data['address'] = str(row['address'])
                if 'courses' in df.columns and pd.notna(row['courses']):
                    student_data['courses'] = [c.strip() for c in str(row['courses']).split(',')]
                
                student = Student(**student_data)
                await student.insert()
                created_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        return {
            "created_count": created_count,
            "total_rows": len(df),
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing CSV: {str(e)}"
        )


@router.get("/export/csv")
async def export_students_csv(
    department: Optional[str] = None,
    status: Optional[StudentStatus] = None,
    current_user: User = Depends(get_current_user)
):
    """Export students to CSV"""
    
    # Build query
    query = {}
    if department:
        query["department"] = department
    if status:
        query["status"] = status
    
    students = await Student.find(query).to_list()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'student_id', 'first_name', 'last_name', 'email', 'department',
        'year', 'status', 'gpa', 'contact_number', 'enrollment_date'
    ])
    
    # Write data
    for student in students:
        writer.writerow([
            student.student_id,
            student.first_name,
            student.last_name,
            student.email,
            student.department,
            student.year,
            student.status,
            student.gpa or '',
            student.contact_number or '',
            student.enrollment_date.strftime('%Y-%m-%d')
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students.csv"}
    )
