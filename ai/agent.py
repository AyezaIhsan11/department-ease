from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from ai.langchain_setup import llm, SYSTEM_PROMPT
from ai.tools import STUDENT_TOOLS
from typing import Dict, Any
import uuid
import asyncio
import re


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
                    retry_delay = _parse_retry_delay(str(e))
                    
                    if attempt < max_retries:
                        # Wait and retry
                        wait_time = min(retry_delay, 45)  # cap at 45s per attempt
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
