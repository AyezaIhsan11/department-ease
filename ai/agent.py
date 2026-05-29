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
        from models.student import Student, StudentStatus
        from services.email_service import email_service
        from config import settings
        import os
        
        msg = message.strip().lower()
        
        # 1. SEND EMAIL
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
            student = None
            if "@" in target:
                student = await Student.find_one(Student.email == target)
            else:
                # Try finding by student_id
                student = await Student.find_one(Student.student_id == target.upper())
                if not student:
                    # Search by first name or last name
                    students = await Student.find({
                        "$or": [
                            {"first_name": {"$regex": target, "$options": "i"}},
                            {"last_name": {"$regex": target, "$options": "i"}}
                        ]
                    }).to_list()
                    if students:
                        student = students[0]
            
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

        # 2. REQUEST FEE VOUCHER UPLOAD
        # Pattern: "request voucher from [recipient]" or "ask [recipient] to upload voucher"
        voucher_match = re.search(r'(?:request\s+voucher\s+from|ask\s+([^\s]+)\s+to\s+upload\s+voucher|send\s+voucher\s+request\s+to)\s+([^\s]+(?:@[^\s]+)?)', msg, re.IGNORECASE)
        if not voucher_match:
            # Try simpler: "request voucher [recipient]"
            voucher_match = re.search(r'request\s+voucher\s+([^\s]+(?:@[^\s]+)?)', msg, re.IGNORECASE)
            
        if voucher_match:
            target = (voucher_match.group(2) or voucher_match.group(1) or voucher_match.group(0).split()[-1]).strip().strip("'\"")
            
            # Find the student
            student = None
            if "@" in target:
                student = await Student.find_one(Student.email == target)
            else:
                student = await Student.find_one(Student.student_id == target.upper())
                if not student:
                    students = await Student.find({
                        "$or": [
                            {"first_name": {"$regex": target, "$options": "i"}},
                            {"last_name": {"$regex": target, "$options": "i"}}
                        ]
                    }).to_list()
                    if students:
                        student = students[0]
                        
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
            student = None
            if "@" in target:
                student = await Student.find_one(Student.email == target)
            else:
                student = await Student.find_one(Student.student_id == target.upper())
                if not student:
                    students = await Student.find({
                        "$or": [
                            {"first_name": {"$regex": target, "$options": "i"}},
                            {"last_name": {"$regex": target, "$options": "i"}}
                        ]
                    }).to_list()
                    if students:
                        student = students[0]
            
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
            
            student = None
            if "@" in target:
                student = await Student.find_one(Student.email == target)
            else:
                student = await Student.find_one(Student.student_id == target.upper())
                if not student:
                    students = await Student.find({
                        "$or": [
                            {"first_name": {"$regex": target, "$options": "i"}},
                            {"last_name": {"$regex": target, "$options": "i"}}
                        ]
                    }).to_list()
                    if students:
                        student = students[0]
            
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
            
            student = None
            if "@" in target:
                student = await Student.find_one(Student.email == target)
            else:
                student = await Student.find_one(Student.student_id == target.upper())
                if not student:
                    students = await Student.find({
                        "$or": [
                            {"first_name": {"$regex": target, "$options": "i"}},
                            {"last_name": {"$regex": target, "$options": "i"}}
                        ]
                    }).to_list()
                    if students:
                        student = students[0]
            
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
            student = None
            if "@" in target:
                student = await Student.find_one(Student.email == target)
            else:
                student = await Student.find_one(Student.student_id == target.upper())
                if not student:
                    students = await Student.find({
                        "$or": [
                            {"first_name": {"$regex": target, "$options": "i"}},
                            {"last_name": {"$regex": target, "$options": "i"}}
                        ]
                    }).to_list()
                    if students:
                        student = students[0]
                        
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
                        print(f"[AI Agent] Quota limit is 0 (blocked/disabled). Skipping retries.")
                        break
                        
                    retry_delay = _parse_retry_delay(str(e))
                    
                    if attempt < max_retries:
                        # Wait and retry
                        wait_time = min(retry_delay, 5)  # cap at 5s to avoid web timeouts!
                        print(f"[AI Agent] Quota error detected. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # All retries exhausted — return friendly message
                        return {
                            "response": (
                                f"⚠️ The AI assistant is temporarily unavailable because the daily request quota "
                                f"for the Gemini API has been exceeded (free tier limit).\n\n"
                                f"**Please try again in about {retry_delay} seconds**, or wait a few minutes "
                                f"for the quota to reset.\n\n"
                                f"💡 *Tip: If this happens frequently, the Gemini API key can be upgraded to a "
                                f"paid plan at https://ai.google.dev for unlimited requests.*"
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
