from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from ai.langchain_setup import llm, get_or_create_memory
from ai.tools import STUDENT_TOOLS
from typing import Dict, Any
import uuid


class StudentManagementAgent:
    """AI Agent for student management"""
    
    def __init__(self):
        self.tools = STUDENT_TOOLS
        self.llm = llm
    
    async def process_message(
        self,
        message: str,
        conversation_id: str = None
    ) -> Dict[str, Any]:
        """
        Process a natural language message and execute appropriate actions
        
        Args:
            message: User's message
            conversation_id: Conversation ID for context
        
        Returns:
            Dictionary with response and action details
        """
        
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Get conversation memory
        memory = get_or_create_memory(conversation_id)
        
        # Create prompt template for React agent
        template = """You are an AI assistant for a department administration system. You help administrators manage student records.

You have access to the following tools:
{tools}

Tool Names: {tool_names}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Previous conversation:
{chat_history}

Question: {input}
{agent_scratchpad}"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["input", "chat_history", "agent_scratchpad", "tools", "tool_names"]
        )
        
        # Create agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
        
        try:
            # Get chat history
            chat_history = memory.load_memory_variables({}).get("chat_history", [])
            
            # Run agent
            result = await agent_executor.ainvoke({
                "input": message,
                "chat_history": chat_history
            })
            
            response = result.get("output", "I'm sorry, I couldn't process that request.")
            
            # Save to memory
            memory.save_context(
                {"input": message},
                {"output": response}
            )
            
            # Determine action taken
            action_taken = None
            if "successfully created" in response.lower():
                action_taken = {"action": "create_student"}
            elif "successfully updated" in response.lower():
                action_taken = {"action": "update_student"}
            elif "successfully deleted" in response.lower():
                action_taken = {"action": "delete_student"}
            elif "found" in response.lower() and "student" in response.lower():
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
