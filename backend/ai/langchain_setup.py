from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from config import settings
from typing import Dict


# Initialize Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=settings.GEMINI_API_KEY,
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

When users ask you to perform an action, use the appropriate tools available to you. Always confirm actions that modify data.

Be helpful, professional, and precise in your responses. If you're not sure about a command, ask for clarification.
"""


def create_conversation_memory(conversation_id: str) -> ConversationBufferMemory:
    """Create a conversation memory for a specific conversation"""
    
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="output"
    )
    
    return memory


def get_agent_prompt() -> ChatPromptTemplate:
    """Get the prompt template for the agent"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    return prompt


# Store for conversation memories (in production, use Redis or database)
conversation_memories: Dict[str, ConversationBufferMemory] = {}


def get_or_create_memory(conversation_id: str) -> ConversationBufferMemory:
    """Get existing conversation memory or create new one"""
    
    if conversation_id not in conversation_memories:
        conversation_memories[conversation_id] = create_conversation_memory(conversation_id)
    
    return conversation_memories[conversation_id]
