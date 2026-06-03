from langchain.tools import tool
from models.student import Student, StudentStatus, normalize_degree
from models.event import Event, EventCategory
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from services.email_service import email_service
import os
import csv
import io
import asyncio
from routes.events import notify_students_of_event
from config import settings


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
        department=normalize_degree(department),
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
        parts = search_term.strip().split()
        or_queries = [
            {"student_id": {"$regex": search_term, "$options": "i"}},
            {"first_name": {"$regex": search_term, "$options": "i"}},
            {"last_name": {"$regex": search_term, "$options": "i"}},
            {"email": {"$regex": search_term, "$options": "i"}}
        ]
        if len(parts) >= 2:
            or_queries.append({
                "$and": [
                    {"first_name": {"$regex": parts[0], "$options": "i"}},
                    {"last_name": {"$regex": " ".join(parts[1:]), "$options": "i"}}
                ]
            })
        query["$or"] = or_queries
    
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
    converted_value: Any = value
    if field == 'gpa':
        converted_value = float(value)
    elif field == 'year':
        converted_value = int(value)
    elif field == 'status':
        converted_value = StudentStatus(value)
    elif field == 'department':
        converted_value = normalize_degree(value)
    
    setattr(student, field, converted_value)
    student.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await student.save()
    
    return f"Successfully updated {field} for student {student_id} to: {converted_value}"


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
async def generate_monthly_report_tool(year: int, month: int) -> str:
    """
    Generate a download link for a monthly student report PDF.
    
    Args:
        year: The year (e.g. 2024)
        month: The month (1-12)
    
    Returns:
        The URL to download the report
    """
    return f"The monthly report for {month}/{year} has been generated. you can download it here: {settings.BACKEND_URL}/api/reports/monthly?year={year}&month={month}"


@tool
async def generate_yearly_report_tool(year: int) -> str:
    """
    Generate a download link for a yearly student report PDF.
    
    Args:
        year: The year (e.g. 2024)
    
    Returns:
        The URL to download the report
    """
    return f"The yearly report for {year} has been generated. you can download it here: {settings.BACKEND_URL}/api/reports/yearly?year={year}"


@tool
async def generate_student_list_report_tool(department: Optional[str] = None) -> str:
    """
    Generate a download link for the full student list PDF.
    
    Args:
        department: Optional department to filter by
    
    Returns:
        The URL to download the report
    """
    url = f"{settings.BACKEND_URL}/api/reports/student-list"
    if department:
        url += f"?department={department}"
    return f"The student list report has been generated. you can download it here: {url}"


@tool
async def get_statistics_tool() -> str:
    """
    Get general statistics about the student population.
    
    Returns:
        Summary of student statistics
    """
    
    total = await Student.find().count()
    active = await Student.find(Student.status == StudentStatus.ACTIVE).count()
    
    all_students = await Student.find(Student.gpa != None).to_list()
    avg_gpa = sum(s.gpa for s in all_students if s.gpa) / len(all_students) if all_students else 0
    
    stats = f"""
Department Statistics:
======================
Total Students: {total}
Active Students: {active}
Average GPA: {avg_gpa:.2f}
"""
    return stats


@tool
async def send_email_tool(
    student_id: str,
    subject: str,
    body: str,
    attachment_path: Optional[str] = None
) -> str:
    """
    Send an email to a student, optionally with an attachment.
    
    Args:
        student_id: The unique ID of the student
        subject: The email subject line
        body: The content of the email
        attachment_path: Optional path to a file to attach
    
    Returns:
        Confirmation or error message
    """
    
    student = await Student.find_one(Student.student_id == student_id)
    
    if not student:
        return f"Error: No student found with ID {student_id}"
    
    if not student.email:
        return f"Error: Student {student_id} does not have an email address recorded."
    
    attachments = None
    if attachment_path:
        try:
            import os
            if os.path.exists(attachment_path):
                filename = os.path.basename(attachment_path)
                with open(attachment_path, "rb") as f:
                    content = f.read()
                attachments = [(filename, content)]
            else:
                return f"Error: Attachment file not found at {attachment_path}"
        except Exception as e:
            return f"Error reading attachment: {str(e)}"
    
    try:
        asyncio.create_task(
            email_service.send_email(
                to_emails=[student.email],
                subject=subject,
                body=body,
                attachments=attachments
            )
        )
        return f"Successfully queued email to be sent to {student.full_name} ({student.email}) in the background{ ' with attachment' if attachments else ''}."
    except Exception as e:
        return f"Failed to initiate email sending: {str(e)}."


@tool
async def request_voucher_tool(student_id: str) -> str:
    """
    Send an email to a student requesting they upload their fee voucher.
    
    Args:
        student_id: The unique ID of the student
    
    Returns:
        Confirmation or error message
    """
    
    student = await Student.find_one(Student.student_id == student_id)
    
    if not student:
        return f"Error: No student found with ID {student_id}"
    
    upload_url = f"{settings.FRONTEND_URL}/upload-voucher/{student_id}"
    
    subject = "Action Required: Please Upload Your Fee Voucher"
    body = f"""
    <h2>Hello {student.first_name},</h2>
    <p>Please upload a clear picture of your paid fee voucher to complete your registration process.</p>
    <p>You can upload it by clicking the link below:</p>
    <p><a href="{upload_url}" style="display:inline-block;padding:10px 20px;background-color:#0ea5e9;color:white;text-decoration:none;border-radius:5px;">Upload Fee Voucher</a></p>
    <p>If the button doesn't work, copy and paste this link: {upload_url}</p>
    <br>
    <p>Best regards,<br>Department Administration Team</p>
    """
    
    try:
        asyncio.create_task(
            email_service.send_email(
                to_emails=[student.email],
                subject=subject,
                body=body,
                html=True
            )
        )
        return f"Successfully queued voucher upload request to be sent to {student.full_name} in the background."
    except Exception as e:
        return f"Failed to initiate voucher request: {str(e)}"


@tool
async def create_event_tool(
    title: str,
    start_date: str,
    end_date: str,
    description: Optional[str] = None,
    category: str = "other"
) -> str:
    """
    Create a new department event.
    
    Args:
        title: Title of the event
        start_date: Start date and time (ISO format: YYYY-MM-DDTHH:MM:SS)
        end_date: End date and time (ISO format: YYYY-MM-DDTHH:MM:SS)
        description: Optional description of the event
        category: Event category (academic, examination, holiday, workshop, seminar, cultural, sports, other)
    
    Returns:
        Success or error message
    """
    
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        if start_dt >= end_dt:
            return "Error: End date must be after start date."
        
        event = Event(
            title=title,
            start_date=start_dt,
            end_date=end_dt,
            description=description,
            category=EventCategory(category.lower()),
            created_by="system"  # Defaulting to system for tool-created events
        )
        
        await event.insert()
        
        # Notify students
        asyncio.create_task(notify_students_of_event(event))
        
        return f"Successfully created event: {title} on {start_dt.strftime('%Y-%m-%d %H:%M')}"
        
    except ValueError as e:
        return f"Error parsing dates or category: {str(e)}. Use format YYYY-MM-DDTHH:MM:SS"
    except Exception as e:
        return f"Error creating event: {str(e)}"


@tool
async def import_students_from_csv_tool(file_path: str) -> str:
    """
    Read a CSV file and bulk-create student records from it.
    Use this when the user uploads a CSV file and asks to add/import students from it.

    Args:
        file_path: The absolute path to the uploaded CSV file

    Returns:
        A summary of how many students were created and any errors per row
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"

    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        return f"Error reading CSV file: {str(e)}"

    required_columns = {"student_id", "first_name", "last_name", "email", "department", "year"}
    if not rows:
        return "Error: The CSV file is empty."

    actual_columns = set(rows[0].keys())
    missing = required_columns - actual_columns
    if missing:
        return f"Error: CSV is missing required columns: {', '.join(missing)}. Required: student_id, first_name, last_name, email, department, year"

    created_count = 0
    errors = []

    for i, row in enumerate(rows, start=2):  # start=2 because row 1 is header
        try:
            student_id = str(row["student_id"]).strip()
            first_name = str(row["first_name"]).strip()
            last_name = str(row["last_name"]).strip()
            email = str(row["email"]).strip()
            department = str(row["department"]).strip()
            year = int(str(row["year"]).strip())

            if not all([student_id, first_name, last_name, email, department]):
                errors.append(f"Row {i}: Missing required value in one of the fields")
                continue

            # Check duplicates
            existing = await Student.find_one(Student.student_id == student_id)
            if existing:
                errors.append(f"Row {i}: Student ID '{student_id}' already exists")
                continue

            existing_email = await Student.find_one(Student.email == email)
            if existing_email:
                errors.append(f"Row {i}: Email '{email}' already registered")
                continue

            student_data: Dict[str, Any] = {
                "student_id": student_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "department": normalize_degree(department),
                "year": year,
            }

            gpa_val = row.get("gpa", "").strip()
            if gpa_val:
                student_data["gpa"] = float(gpa_val)

            contact = row.get("contact_number", "").strip()
            if contact:
                student_data["contact_number"] = contact

            address = row.get("address", "").strip()
            if address:
                student_data["address"] = address

            courses_raw = row.get("courses", "").strip()
            if courses_raw:
                student_data["courses"] = [c.strip() for c in courses_raw.split(",")]

            student = Student(**student_data)
            await student.insert()
            created_count += 1

        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")

    summary = f"✅ Import complete: {created_count} of {len(rows)} students created."
    if errors:
        summary += f"\n\n⚠️ {len(errors)} error(s):\n" + "\n".join(errors)
    return summary


@tool
async def import_students_from_pdf_tool(file_path: str) -> str:
    """
    Read a PDF file and bulk-create student records from it.
    Use this when the user uploads a PDF file and asks to add/import students from it.

    Args:
        file_path: The absolute path to the uploaded PDF file

    Returns:
        A summary of how many students were created and any errors per row
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"

    try:
        import pdfplumber
    except ImportError:
        return "Error: pdfplumber library is not installed. PDF parsing is unavailable."

    rows = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # Clean up None values
                        clean_row = [cell.strip() if cell is not None else "" for cell in row]
                        # Only add non-empty rows
                        if any(clean_row):
                            rows.append(clean_row)
    except Exception as e:
        return f"Error reading PDF file: {str(e)}"

    if not rows:
        return "Error: Could not find any readable tables in the PDF file."

    # First row should be headers
    headers = [h.lower().replace(' ', '_').strip() for h in rows[0]]
    data_rows = rows[1:]

    required_columns = {"student_id", "first_name", "last_name", "email", "department", "year"}
    actual_columns = set(headers)
    missing = required_columns - actual_columns
    
    if missing:
        # Fallback to try finding headers in the first few rows if the first row wasn't it
        found_headers = False
        for i in range(min(5, len(rows))):
            test_headers = [h.lower().replace(' ', '_').strip() for h in rows[i]]
            if required_columns.issubset(set(test_headers)):
                headers = test_headers
                data_rows = rows[i+1:]
                found_headers = True
                missing = set()
                break
                
        if not found_headers:
            return f"Error: PDF table is missing required columns: {', '.join(missing)}. Required: student_id, first_name, last_name, email, department, year"

    created_count = 0
    errors = []

    for i, row in enumerate(data_rows, start=1):
        try:
            # Map row to dictionary using headers
            row_dict = {}
            for j, header in enumerate(headers):
                if j < len(row):
                    row_dict[header] = row[j]
                else:
                    row_dict[header] = ""
                    
            student_id = row_dict.get("student_id", "").strip()
            first_name = row_dict.get("first_name", "").strip()
            last_name = row_dict.get("last_name", "").strip()
            email = row_dict.get("email", "").strip()
            department = row_dict.get("department", "").strip()
            year_str = row_dict.get("year", "").strip()

            if not all([student_id, first_name, last_name, email, department, year_str]):
                errors.append(f"Row {i}: Missing required value in one of the fields")
                continue

            try:
                year = int(year_str)
            except ValueError:
                errors.append(f"Row {i}: Invalid year value '{year_str}'")
                continue

            # Check duplicates
            existing = await Student.find_one(Student.student_id == student_id)
            if existing:
                errors.append(f"Row {i}: Student ID '{student_id}' already exists")
                continue

            existing_email = await Student.find_one(Student.email == email)
            if existing_email:
                errors.append(f"Row {i}: Email '{email}' already registered")
                continue

            student_data = {
                "student_id": student_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "department": normalize_degree(department),
                "year": year,
            }

            gpa_val = row_dict.get("gpa", "").strip()
            if gpa_val:
                try:
                    student_data["gpa"] = float(gpa_val)
                except ValueError:
                    pass

            contact = row_dict.get("contact_number", "").strip()
            if contact:
                student_data["contact_number"] = contact

            address = row_dict.get("address", "").strip()
            if address:
                student_data["address"] = address

            courses_raw = row_dict.get("courses", "").strip()
            if courses_raw:
                student_data["courses"] = [c.strip() for c in courses_raw.split(",")]

            student = Student(**student_data)
            await student.insert()
            created_count += 1

        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")

    summary = f"✅ PDF Import complete: {created_count} of {len(data_rows)} students created."
    if errors:
        # Only show first 10 errors to avoid huge responses
        display_errors = errors[:10]
        summary += f"\n\n⚠️ {len(errors)} error(s) total. First few:\n" + "\n".join(display_errors)
    return summary


STUDENT_TOOLS = [
    create_student_tool,
    search_students_tool,
    get_student_details_tool,
    update_student_tool,
    delete_student_tool,
    get_statistics_tool,
    generate_monthly_report_tool,
    generate_yearly_report_tool,
    generate_student_list_report_tool,
    send_email_tool,
    request_voucher_tool,
    create_event_tool,
    import_students_from_csv_tool,
    import_students_from_pdf_tool
]
