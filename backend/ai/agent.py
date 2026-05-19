from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from ai.langchain_setup import llm, SYSTEM_PROMPT
from ai.tools import STUDENT_TOOLS
from typing import Dict, Any
import uuid


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
        attachment_path: str = None
    ) -> Dict[str, Any]:
        """
        Process a natural language message and execute appropriate actions
        
        Args:
            message: User's message
            conversation_id: Conversation ID for context
            attachment_path: Path to an uploaded file
        
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
        
        try:
            # Run agent
            result = await self.agent.ainvoke(
                {"messages": [("human", full_message)]},
                config=config
            )
            
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
            return {
                "response": f"I encountered an error: {str(e)}. Please try rephrasing your request.",
                "conversation_id": conversation_id,
                "action_taken": None
            }


# Global agent instance
student_agent = StudentManagementAgent()
