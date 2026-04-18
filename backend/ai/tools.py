from langchain.tools import tool
from models.student import Student, StudentStatus
from typing import List, Dict, Any, Optional
from datetime import datetime


@tool
async def create_student_tool(
    student_id: str,
    first_name: str,
    last_name: str,
    email: str,
    department: str,
    year: int,
    gpa: Optional[float] = None,
    contact_number: Optional[str] = None
) -> str:
    """
    Create a new student record.
    
    Args:
        student_id: Unique student ID
        first_name: Student's first name
        last_name: Student's last name
        email: Student's email address
        department: Department name
        year: Academic year (1-8)
        gpa: Grade point average (0.0-4.0), optional
        contact_number: Contact phone number, optional
    
    Returns:
        Success message with student ID
    """
    
    # Check if student already exists
    existing = await Student.find_one(Student.student_id == student_id)
    if existing:
        return f"Error: Student with ID {student_id} already exists."
    
    # Create student
    student = Student(
        student_id=student_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        department=department,
        year=year,
        gpa=gpa,
        contact_number=contact_number
    )
    
    await student.insert()
    
    return f"Successfully created student record for {first_name} {last_name} (ID: {student_id})"


@tool
async def search_students_tool(
    search_term: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[str] = None
) -> str:
    """
    Search for students by various criteria.
    
    Args:
        search_term: Search in name, ID, or email
        department: Filter by department
        status: Filter by status (active, inactive, graduated)
    
    Returns:
        Formatted list of matching students
    """
    
    query = {}
    
    if search_term:
        query["$or"] = [
            {"student_id": {"$regex": search_term, "$options": "i"}},
            {"first_name": {"$regex": search_term, "$options": "i"}},
            {"last_name": {"$regex": search_term, "$options": "i"}},
            {"email": {"$regex": search_term, "$options": "i"}}
        ]
    
    if department:
        query["department"] = department
    
    if status:
        query["status"] = status
    
    students = await Student.find(query).limit(10).to_list()
    
    if not students:
        return "No students found matching the criteria."
    
    result = f"Found {len(students)} student(s):\n\n"
    for s in students:
        result += f"- {s.full_name} (ID: {s.student_id})\n"
        result += f"  Email: {s.email}, Department: {s.department}, Year: {s.year}\n"
        if s.gpa:
            result += f"  GPA: {s.gpa}\n"
        result += "\n"
    
    return result


@tool
async def get_student_details_tool(student_id: str) -> str:
    """
    Get detailed information about a specific student.
    
    Args:
        student_id: The student's unique ID
    
    Returns:
        Detailed student information
    """
    
    student = await Student.find_one(Student.student_id == student_id)
    
    if not student:
        return f"No student found with ID: {student_id}"
    
    details = f"""
Student Details:
================
ID: {student.student_id}
Name: {student.full_name}
Email: {student.email}
Department: {student.department}
Year: {student.year}
Status: {student.status}
GPA: {student.gpa if student.gpa else 'N/A'}
Contact: {student.contact_number if student.contact_number else 'N/A'}
Enrolled: {student.enrollment_date.strftime('%Y-%m-%d')}
"""
    
    if student.courses:
        details += f"\nCourses: {', '.join(student.courses)}"
    
    return details


@tool
async def update_student_tool(
    student_id: str,
    field: str,
    value: str
) -> str:
    """
    Update a specific field for a student.
    
    Args:
        student_id: The student's unique ID
        field: Field to update (email, gpa, status, year, contact_number, department)
        value: New value for the field
    
    Returns:
        Success or error message
    """
    
    student = await Student.find_one(Student.student_id == student_id)
    
    if not student:
        return f"No student found with ID: {student_id}"
    
    # Update the field
    allowed_fields = ['email', 'gpa', 'status', 'year', 'contact_number', 'department', 'first_name', 'last_name']
    
    if field not in allowed_fields:
        return f"Cannot update field '{field}'. Allowed fields: {', '.join(allowed_fields)}"
    
    # Type conversion
    if field == 'gpa':
        value = float(value)
    elif field == 'year':
        value = int(value)
    elif field == 'status':
        value = StudentStatus(value)
    
    setattr(student, field, value)
    student.updated_at = datetime.utcnow()
    await student.save()
    
    return f"Successfully updated {field} for student {student_id} to: {value}"


@tool
async def delete_student_tool(student_id: str) -> str:
    """
    Delete a student record.
    
    Args:
        student_id: The student's unique ID
    
    Returns:
        Success or error message
    """
    
    student = await Student.find_one(Student.student_id == student_id)
    
    if not student:
        return f"No student found with ID: {student_id}"
    
    student_name = student.full_name
    await student.delete()
    
    return f"Successfully deleted student record for {student_name} (ID: {student_id})"


@tool
async def get_statistics_tool() -> str:
    """
    Get overall statistics about students.
    
    Returns:
        Formatted statistics
    """
    
    total = await Student.find().count()
    active = await Student.find(Student.status == StudentStatus.ACTIVE).count()
    
    # Get all students with GPA
    students_with_gpa = await Student.find(Student.gpa != None).to_list()
    avg_gpa = sum(s.gpa for s in students_with_gpa if s.gpa) / len(students_with_gpa) if students_with_gpa else 0
    
    stats = f"""
Student Statistics:
==================
Total Students: {total}
Active Students: {active}
Average GPA: {avg_gpa:.2f}
"""
    
    return stats


# List of all tools
STUDENT_TOOLS = [
    create_student_tool,
    search_students_tool,
    get_student_details_tool,
    update_student_tool,
    delete_student_tool,
    get_statistics_tool
]
