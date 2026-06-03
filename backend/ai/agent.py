from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from ai.langchain_setup import llm, SYSTEM_PROMPT
from ai.tools import STUDENT_TOOLS
from typing import Dict, Any, Optional
import uuid
import asyncio
import re
import datetime


def _parse_retry_delay(error_str: str) -> int:
    """Extract retry delay in seconds from a RESOURCE_EXHAUSTED error message."""
    match = re.search(r'retry[_ ]in[_ ](\d+)', error_str, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 60  # default 60s if not parseable


def _is_quota_error(error: Exception) -> bool:
    """Check if the error is a Gemini API quota/rate-limit error."""
    msg = str(error).upper()
    return "RESOURCE_EXHAUSTED" in msg or "429" in msg or "QUOTA" in msg


async def _find_student_by_target(target: str) -> Optional[Any]:
    """
    Helper to find a student by email, student_id, first_name, last_name, or full name.
    Supports names split by space.
    """
    from models.student import Student
    
    target = target.strip()
    if not target:
        return None
        
    if "@" in target:
        return await Student.find_one(Student.email == target)
        
    # Try finding by student_id
    student = await Student.find_one(Student.student_id == target.upper())
    if student:
        return student
        
    # Search by first name, last name, or split first/last name
    parts = target.split()
    or_queries = [
        {"first_name": {"$regex": target, "$options": "i"}},
        {"last_name": {"$regex": target, "$options": "i"}}
    ]
    if len(parts) >= 2:
        or_queries.append({
            "$and": [
                {"first_name": {"$regex": parts[0], "$options": "i"}},
                {"last_name": {"$regex": " ".join(parts[1:]), "$options": "i"}}
            ]
        })
        
    students = await Student.find({"$or": or_queries}).to_list()
    if students:
        return students[0]
    return None


class StudentManagementAgent:
    """AI Agent for student management"""
    
    def __init__(self):
        self.tools = STUDENT_TOOLS
        self.llm = llm
        self.memory = MemorySaver()
        self.agent = create_react_agent(
            self.llm,
            tools=self.tools,
            prompt=SYSTEM_PROMPT,
            checkpointer=self.memory
        )
    
    async def _handle_fallback(self, message: str, attachment_path: str = None) -> Optional[Dict[str, Any]]:
        """
        A rule-based fallback parser that executes common commands if the Gemini API is unavailable.
        Returns a response dictionary if matched and executed, otherwise None.
        """
        from models.student import Student, StudentStatus, normalize_degree
        from services.email_service import email_service
        from config import settings
        import os
        
        msg = message.strip().lower()
        
        # 1. REQUEST FEE VOUCHER UPLOAD (Checked first to intercept voucher requests before general emails)
        # Check if the message contains "voucher" or "vouche"
        if "voucher" in msg or "vouche" in msg:
            # Try to extract target name/email
            # Pattern A: ... to [name] to upload voucher ...
            voucher_match = re.search(r'(?:to|from|ask)\s+([a-zA-Z0-9_ ]+?)\s+(?:to|for|upload|voucher|vouche)', msg, re.IGNORECASE)
            # Pattern B: ... voucher/upload from/to/of [name]
            if not voucher_match:
                voucher_match = re.search(r'(?:voucher|vouche|upload)\s+(?:from|to|for|of)\s+([a-zA-Z0-9_ ]+)', msg, re.IGNORECASE)
            # Pattern C: request voucher [name]
            if not voucher_match:
                voucher_match = re.search(r'voucher\s+([a-zA-Z0-9_ ]+)', msg, re.IGNORECASE)
                
            if voucher_match:
                target = voucher_match.group(1).strip().strip("'\"")
                # Clean up if matched "the student" or similar
                if target.startswith("the student "):
                    target = target[12:]
                elif target.startswith("student "):
                    target = target[8:]
                elif target.startswith("the "):
                    target = target[4:]
                    
                # Find the student
                student = await _find_student_by_target(target)
                            
                if not student:
                    return {
                        "response": f"I couldn't find a student matching '{target}' to request a fee voucher from.",
                        "action_taken": None
                    }
                    
                upload_url = f"{settings.FRONTEND_URL}/upload-voucher/{student.student_id}"
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
                    await email_service.send_email(
                        to_emails=[student.email],
                        subject=subject,
                        body=body,
                        html=True
                    )
                    return {
                        "response": f"✅ Successfully sent a fee voucher upload request email to {student.full_name} ({student.email}).",
                        "action_taken": {"action": "request_voucher"}
                    }
                except Exception as e:
                    return {
                        "response": f"Failed to send voucher request to {student.full_name}: {str(e)}",
                        "action_taken": None
                    }

        # 2. SEND EMAIL
        # Pattern: "send mail to [recipient]" or "send email to [recipient]" with optional subject/body
        email_match = re.search(r'send\s+(?:a\s+)?(?:mail|email)\s+to\s+([^\s]+(?:@[^\s]+)?)(?:\s+with\s+subject\s+(.+?)\s+and\s+body\s+(.+))?', msg, re.IGNORECASE)
        if not email_match:
            email_match = re.search(r'send\s+(?:a\s+)?(?:mail|email)\s+to\s+([^\s]+(?:@[^\s]+)?)', msg, re.IGNORECASE)
            
        if email_match:
            target = email_match.group(1).strip().strip("'\"")
            
            # Default subject/body if not specified
            subject = "Notification from Department Administration"
            body = "Hello, this is an automated notification from the Department Administration System."
            
            if len(email_match.groups()) >= 3 and email_match.group(2) and email_match.group(3):
                subject = email_match.group(2).strip().strip("'\"")
                body = email_match.group(3).strip().strip("'\"")
                
            # Find the student
            student = await _find_student_by_target(target)
            
            if not student:
                return {
                    "response": f"I tried to send an email, but I couldn't find a student matching '{target}' in the database.",
                    "action_taken": None
                }
                
            if not student.email:
                return {
                    "response": f"Student '{student.full_name}' was found, but they do not have a registered email address.",
                    "action_taken": None
                }
                
            # Handle attachment
            attachments = None
            if attachment_path:
                try:
                    if os.path.exists(attachment_path):
                        filename = os.path.basename(attachment_path)
                        with open(attachment_path, "rb") as f:
                            content = f.read()
                        attachments = [(filename, content)]
                except Exception as e:
                    print(f"Fallback reading attachment failed: {e}")
                    
            # Send the email
            try:
                await email_service.send_email(
                    to_emails=[student.email],
                    subject=subject,
                    body=body,
                    attachments=attachments
                )
                return {
                    "response": f"✉️ Email sent successfully to {student.full_name} ({student.email})!\n\n**Subject:** {subject}\n**Body:** {body}",
                    "action_taken": {"action": "send_email"}
                }
            except Exception as e:
                return {
                    "response": f"Failed to send email to {student.full_name}: {str(e)}",
                    "action_taken": None
                }

        # 3. UPDATE STUDENT CONTACT NUMBER OR OTHER FIELDS
        # Property list matching contact info
        prop_phone = r'(?:phone|mobile|number|contact|contact_number|mobile_number|mobile\s+number|mobile\s+no|phone\s+number|contact\s+number|mob|phone\s+no)'
        
        # Pattern A: update/change mobile of [name/id] to [val]
        update_match = re.search(rf'(?:update|change)\s+(?:the\s+)?{prop_phone}\s+of\s+([a-zA-Z0-9_ ]+?)\s+to\s+([0-9\-\+\(\) ]+)', msg, re.IGNORECASE)
        # Pattern B: update/change [name/id]\'s mobile to [val]
        if not update_match:
            update_match = re.search(rf'(?:update|change)\s+(?:student\s+)?([a-zA-Z0-9_ ]+?)\'s\s+{prop_phone}\s+to\s+([0-9\-\+\(\) ]+)', msg, re.IGNORECASE)
        # Pattern C: update/change [name/id] mobile to [val]
        if not update_match:
            update_match = re.search(rf'(?:update|change)\s+(?:student\s+)?([a-zA-Z0-9_ ]+?)\s+{prop_phone}\s+to\s+([0-9\-\+\(\) ]+)', msg, re.IGNORECASE)
            
        if update_match:
            target = update_match.group(1).strip().strip("'\"")
            new_number = update_match.group(2).strip()
            
            # Find the student
            student = await _find_student_by_target(target)
            
            if not student:
                return {
                    "response": f"I couldn't find a student matching '{target}' to update contact number.",
                    "action_taken": None
                }
                
            student.contact_number = new_number
            student.updated_at = datetime.datetime.utcnow()
            await student.save()
            
            return {
                "response": f"📱 Successfully updated the contact number for {student.full_name} (ID: {student.student_id}) to: {new_number}",
                "action_taken": {"action": "update_student"}
            }

        # Update GPA
        # Pattern A: update/change GPA of [name/id] to [val]
        gpa_match = re.search(r'(?:update|change)\s+(?:the\s+)?gpa\s+of\s+([a-zA-Z0-9_ ]+?)\s+to\s+([0-9\.]+)', msg, re.IGNORECASE)
        # Pattern B: update/change [name/id]\'s GPA to [val]
        if not gpa_match:
            gpa_match = re.search(r'(?:update|change)\s+(?:student\s+)?([a-zA-Z0-9_ ]+?)\'s\s+gpa\s+to\s+([0-9\.]+)', msg, re.IGNORECASE)
        # Pattern C: update/change [name/id] GPA to [val]
        if not gpa_match:
            gpa_match = re.search(r'(?:update|change)\s+(?:student\s+)?([a-zA-Z0-9_ ]+?)\s+gpa\s+to\s+([0-9\.]+)', msg, re.IGNORECASE)
            
        if gpa_match:
            target = gpa_match.group(1).strip().strip("'\"")
            new_gpa = float(gpa_match.group(2).strip())
            
            student = await _find_student_by_target(target)
            
            if not student:
                return {
                    "response": f"I couldn't find a student matching '{target}' to update GPA.",
                    "action_taken": None
                }
                
            student.gpa = new_gpa
            student.updated_at = datetime.datetime.utcnow()
            await student.save()
            return {
                "response": f"📊 Successfully updated the GPA for {student.full_name} (ID: {student.student_id}) to: {new_gpa}",
                "action_taken": {"action": "update_student"}
            }

        # Update Status
        # Pattern A: update/change status of [name/id] to [val]
        status_match = re.search(r'(?:update|change)\s+(?:the\s+)?status\s+of\s+([a-zA-Z0-9_ ]+?)\s+to\s+(active|inactive|graduated)', msg, re.IGNORECASE)
        # Pattern B: update/change [name/id]\'s status to [val]
        if not status_match:
            status_match = re.search(r'(?:update|change)\s+(?:student\s+)?([a-zA-Z0-9_ ]+?)\'s\s+status\s+to\s+(active|inactive|graduated)', msg, re.IGNORECASE)
        # Pattern C: update/change [name/id] status to [val]
        if not status_match:
            status_match = re.search(r'(?:update|change)\s+(?:student\s+)?([a-zA-Z0-9_ ]+?)\s+status\s+to\s+(active|inactive|graduated)', msg, re.IGNORECASE)
            
        if status_match:
            target = status_match.group(1).strip().strip("'\"")
            new_status = status_match.group(2).strip().lower()
            
            student = await _find_student_by_target(target)
            
            if not student:
                return {
                    "response": f"I couldn't find a student matching '{target}' to update status.",
                    "action_taken": None
                }
                
            student.status = StudentStatus(new_status)
            student.updated_at = datetime.datetime.utcnow()
            await student.save()
            return {
                "response": f"🎓 Successfully updated the status for {student.full_name} (ID: {student.student_id}) to: {new_status}",
                "action_taken": {"action": "update_student"}
            }

        # 4. SHOW DETAILS OF A STUDENT
        # Pattern: "show details of [student_id]" or "show details of [name]"
        show_match = re.search(r'(?:show\s+details\s+of|view\s+student|get\s+details\s+for)\s+([a-zA-Z0-9\-\.\@ ]+)', msg, re.IGNORECASE)
        if show_match:
            target = show_match.group(1).strip().strip("'\"")
            student = await _find_student_by_target(target)
                        
            if not student:
                return {
                    "response": f"I couldn't find a student matching '{target}' to show details.",
                    "action_taken": None
                }
                
            details = f"""
### Student Details for {student.full_name}:
- **Student ID:** {student.student_id}
- **Email:** {student.email}
- **Department:** {student.department}
- **Year:** {student.year}
- **Status:** {student.status}
- **GPA:** {student.gpa if student.gpa else 'N/A'}
- **Contact Number:** {student.contact_number if student.contact_number else 'N/A'}
- **Enrollment Date:** {student.enrollment_date.strftime('%Y-%m-%d')}
"""
            return {
                "response": details,
                "action_taken": {"action": "search_students"}
            }
            
        # 5. LIST ALL STUDENTS
        if re.search(r'(?:show|list|get|display)\s+(?:all\s+)?students', msg, re.IGNORECASE) or msg.strip() in ["list students", "show students", "all students"]:
            students = await Student.find().limit(20).to_list()
            if not students:
                return {
                    "response": "No students found in the database.",
                    "action_taken": None
                }
            result = f"**Found {len(students)} student(s):**\n\n"
            for s in students:
                result += f"- **{s.full_name}** (ID: `{s.student_id}`) — {s.department}, Year {s.year}, Status: {s.status}\n"
            return {
                "response": result,
                "action_taken": {"action": "search_students"}
            }

        # 6. GET STATISTICS
        if re.search(r'(?:show|get|display)?\s*(?:statistics|stats|overview|summary)', msg, re.IGNORECASE):
            from models.student import Student, StudentStatus
            total = await Student.find().count()
            active = await Student.find(Student.status == StudentStatus.ACTIVE).count()
            all_with_gpa = await Student.find(Student.gpa != None).to_list()
            avg_gpa = sum(s.gpa for s in all_with_gpa if s.gpa) / len(all_with_gpa) if all_with_gpa else 0
            return {
                "response": f"""📊 **Department Statistics:**

- **Total Students:** {total}
- **Active Students:** {active}
- **Average GPA:** {avg_gpa:.2f}""",
                "action_taken": None
            }

        # 7. DELETE STUDENT
        delete_match = re.search(r'(?:delete|remove)\s+(?:student\s+)?([a-zA-Z0-9_ ]+?)(?:\s+from\s+(?:the\s+)?(?:system|database|records?))?$', msg, re.IGNORECASE)
        if delete_match:
            target = delete_match.group(1).strip().strip("'\"")
            student = await _find_student_by_target(target)
            if not student:
                return {
                    "response": f"I couldn't find a student matching '{target}' to delete.",
                    "action_taken": None
                }
            name = student.full_name
            sid = student.student_id
            await student.delete()
            return {
                "response": f"🗑️ Successfully deleted student record for **{name}** (ID: `{sid}`).",
                "action_taken": {"action": "delete_student"}
            }

        # 8. ADD/CREATE STUDENT
        # First try to find "name: [First] [Last]" or "name [First] [Last]" or "named [First] [Last]"
        name_match = re.search(r'name\s*[:\-]?\s*([a-zA-Z]+)\s+([a-zA-Z]+)', msg, re.IGNORECASE)
        if not name_match:
            # If no explicit name label, try to match the two words after "add student", "create student", etc.
            name_match = re.search(r'(?:add|create)\s+(?:a\s+)?(?:new\s+)?student\s+(?:named\s+)?([a-zA-Z]+)\s+([a-zA-Z]+)', msg, re.IGNORECASE)
            
        if name_match:
            first_name = name_match.group(1).strip().capitalize()
            last_name = name_match.group(2).strip().capitalize()
            
            # Extract email
            email_match = re.search(r'(?:email|mail)\s*[:\-]?\s*([^\s,]+@[^\s,]+)', msg, re.IGNORECASE)
            # Extract student ID
            id_match = re.search(r'(?:id|student\s+id)\s*[:\-]?\s*([a-zA-Z0-9\-]+)', msg, re.IGNORECASE)
            # Extract department
            dept_match = re.search(r'(?:department|dept|degree|program)\s*(?:of)?\s*[:\-]?\s*([a-zA-Z\s\(\)]+?)(?:,|$|\s+with|\s+year|\s+email|\s+id|\s+gpa|\s+contact|\s+phone)', msg, re.IGNORECASE)
            # Extract year
            year_match = re.search(r'year\s*[:\-]?\s*(\d)', msg, re.IGNORECASE)
            # Extract gpa
            gpa_match = re.search(r'gpa\s*[:\-]?\s*([0-9\.]+)', msg, re.IGNORECASE)
            # Extract contact number
            contact_match = re.search(r'(?:contact|phone|mobile)(?:\s+number|\s+no)?\s*[:\-]?\s*([0-9\-\+\(\) ]+)', msg, re.IGNORECASE)
            
            email = email_match.group(1).strip() if email_match else None
            student_id = id_match.group(1).strip().upper() if id_match else None
            department = normalize_degree(dept_match.group(1).strip()) if dept_match else None
            year = int(year_match.group(1).strip()) if year_match else None
            gpa = float(gpa_match.group(1).strip()) if gpa_match else None
            contact = contact_match.group(1).strip() if contact_match else None
            
            # Validate required fields
            missing = []
            if not student_id:
                missing.append("student ID (e.g. ID CS001)")
            if not email:
                missing.append("email (e.g. email john@example.com)")
            if not department:
                missing.append("degree program (e.g. degree BS Computer Science (CS))")
            if not year:
                missing.append("year (e.g. year 2)")
                
            if missing:
                return {
                    "response": f"I detected you want to add a student named {first_name} {last_name}, but I need the following missing details:\n" + "\n".join(f"- {m}" for m in missing) + "\n\nPlease provide them in your message, e.g.: `add student John Doe with ID CS001, email john@example.com, degree BS Computer Science (CS), year 2`.",
                    "action_taken": None
                }
            
            # Check duplicate ID
            existing = await Student.find_one(Student.student_id == student_id)
            if existing:
                return {
                    "response": f"Error: Student with ID {student_id} already exists.",
                    "action_taken": None
                }
            
            # Check duplicate Email
            existing_email = await Student.find_one(Student.email == email)
            if existing_email:
                return {
                    "response": f"Error: Email {email} is already registered.",
                    "action_taken": None
                }
                
            # Create student
            student = Student(
                student_id=student_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                department=department,
                year=year,
                gpa=gpa,
                contact_number=contact
            )
            await student.insert()
            
            return {
                "response": f"👤 Successfully created student record for **{first_name} {last_name}** (ID: `{student_id}`)!",
                "action_taken": {"action": "create_student"}
            }

        return None

    async def process_message(
        self,
        message: str,
        conversation_id: Any = None,
        attachment_path: str = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Process a natural language message and execute appropriate actions.
        Automatically retries on Gemini rate-limit (429) errors with backoff.
        
        Args:
            message: User's message
            conversation_id: Conversation ID for context
            attachment_path: Path to an uploaded file
            max_retries: Number of retry attempts on quota errors
        
        Returns:
            Dictionary with response and action details
        """
        
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        config = {"configurable": {"thread_id": conversation_id}}
        
        # Try fallback rule-based parser first (highly robust, works even without Gemini quota)
        fallback_res = await self._handle_fallback(message, attachment_path)
        if fallback_res:
            print(f"[AI Agent] Fallback parser matched and executed message: '{message}'")
            fallback_res["conversation_id"] = conversation_id
            return fallback_res
            
        # Add attachment info to message if present
        full_message = message
        if attachment_path:
            full_message += f"\n\n[USER UPLOADED FILE: {attachment_path}]"
            full_message += "\n(You can use this path in the send_email_tool if the user wants to send this file as an attachment)"
        
        print(f"[AI Agent] Received message: '{message}' (conversation_id: {conversation_id})")
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                print(f"[AI Agent] Invoking Gemini model (attempt {attempt + 1})...")
                # Run agent
                result = await self.agent.ainvoke(
                    {"messages": [("human", full_message)]},
                    config=config
                )
                print(f"[AI Agent] Model invoked successfully!")
                
                content = result["messages"][-1].content
                if isinstance(content, list):
                    response = " ".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
                else:
                    response = str(content)
                
                # Determine action taken
                action_taken = None
                response_lower = response.lower()
                if "successfully created" in response_lower:
                    action_taken = {"action": "create_student"}
                elif "successfully updated" in response_lower:
                    action_taken = {"action": "update_student"}
                elif "successfully deleted" in response_lower:
                    action_taken = {"action": "delete_student"}
                elif "found" in response_lower and "student" in response_lower:
                    action_taken = {"action": "search_students"}
                
                return {
                    "response": response,
                    "conversation_id": conversation_id,
                    "action_taken": action_taken
                }
                
            except Exception as e:
                last_error = e
                # Print key details and error for debugging
                key_to_show = "None"
                if hasattr(self.llm, "google_api_key") and self.llm.google_api_key:
                    k = self.llm.google_api_key
                    k_str = k.get_secret_value() if hasattr(k, "get_secret_value") else str(k)
                    if len(k_str) > 10:
                        key_to_show = f"{k_str[:6]}...{k_str[-6:]}"
                    else:
                        key_to_show = "SHORT_KEY"
                print(f"[AI Agent] Attempt {attempt + 1} failed. API Key used: {key_to_show}. Error: {str(e)}")
                
                if _is_quota_error(e):
                    # If the project is permanently blocked (limit is 0), don't sleep or retry at all
                    if "limit: 0" in str(e).lower() or "limit: 0" in repr(e).lower():
                        print(f"[AI Agent] Quota limit is 0 (blocked/disabled). Returning early with warning.")
                        return {
                            "response": (
                                f"⚠️ The AI assistant is temporarily unavailable due to Gemini API quota limits.\n\n"
                                f"However, these commands work **without** Gemini and will succeed immediately:\n\n"
                                f"👤 **Add student:** `add student [first] [last] with ID [id], email [email], department [dept], year [year]`\n"
                                f"📧 **Email:** `send mail to [name]`\n"
                                f"📋 **Voucher:** `send mail to [name] to upload voucher`\n"
                                f"📱 **Update contact:** `update mobile no of [name] to [number]`\n"
                                f"📊 **Update GPA:** `update gpa of [name] to [value]`\n"
                                f"🎓 **Update status:** `update status of [name] to active/graduated`\n"
                                f"👤 **View student:** `show details of [name]`\n"
                                f"📃 **List students:** `list all students`\n"
                                f"📈 **Statistics:** `show statistics`\n"
                                f"🗑️ **Delete student:** `delete student [name or ID]`"
                            ),
                            "conversation_id": conversation_id,
                            "action_taken": None
                        }
                        
                    retry_delay = _parse_retry_delay(str(e))
                    
                    if attempt < max_retries:
                        # Wait and retry
                        wait_time = min(retry_delay, 5)  # cap at 5s to avoid web timeouts!
                        print(f"[AI Agent] Quota error detected. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # All retries exhausted — return friendly message with supported commands
                        return {
                            "response": (
                                f"⚠️ The AI assistant is temporarily unavailable due to Gemini API quota limits.\n\n"
                                f"However, these commands work **without** Gemini and will succeed immediately:\n\n"
                                f"👤 **Add student:** `add student [first] [last] with ID [id], email [email], department [dept], year [year]`\n"
                                f"📧 **Email:** `send mail to [name]`\n"
                                f"📋 **Voucher:** `send mail to [name] to upload voucher`\n"
                                f"📱 **Update contact:** `update mobile no of [name] to [number]`\n"
                                f"📊 **Update GPA:** `update gpa of [name] to [value]`\n"
                                f"🎓 **Update status:** `update status of [name] to active/graduated`\n"
                                f"👤 **View student:** `show details of [name]`\n"
                                f"📃 **List students:** `list all students`\n"
                                f"📈 **Statistics:** `show statistics`\n"
                                f"🗑️ **Delete student:** `delete student [name or ID]`"
                            ),
                            "conversation_id": conversation_id,
                            "action_taken": None
                        }
                else:
                    # Non-quota error — don't retry
                    return {
                        "response": f"I encountered an error: {str(e)}. Please try rephrasing your request.",
                        "conversation_id": conversation_id,
                        "action_taken": None
                    }
        
        # Fallback (should not be reached)
        return {
            "response": f"Sorry, something went wrong: {str(last_error)}",
            "conversation_id": conversation_id,
            "action_taken": None
        }


# Global agent instance
student_agent = StudentManagementAgent()
