from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from config import settings
from typing import Dict

import os

# Initialize Gemini model with fallback key to avoid startup crashes if not configured
gemini_key = settings.GEMINI_API_KEY or os.environ.get("GOOGLE_API_KEY") or "DUMMY_GEMINI_KEY"

llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    google_api_key=gemini_key,
    temperature=0.3,
    convert_system_message_to_human=True
)

# System prompt for the AI assistant
SYSTEM_PROMPT = """You are an AI assistant for a department administration system. You help administrators manage student records through natural language commands.

You can perform the following operations:
1. Create new student records
2. Search and retrieve student information
3. Update student details
4. Delete student records
5. Generate reports and statistics
6. Send emails to students
7. Request fee voucher uploads from students
8. Create and manage department events

IMPORTANT INSTRUCTIONS:
1. If the user wants to add/create a new student but does not provide all required fields (student_id, first_name, last_name, email, department, year), DO NOT guess the values. Instead, ask the user to provide the specific missing information.
2. If the user asks to add/create a student, DO NOT use the search tool first unless explicitly checking existence.

When users ask you to perform an action, use the appropriate tools available to you. Always confirm actions that modify data.

Be helpful, professional, and precise in your responses. If you're not sure about a command, ask for clarification.
"""
