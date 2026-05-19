from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
import os
import uuid
from models.user import User
from models.chat_history import ChatHistory
from schemas.chat import ChatResponse
from auth.dependencies import get_current_user
from ai.agent import student_agent
from typing import Optional


router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Ensure chat attachments directory exists
ATTACHMENTS_DIR = "uploads/chat_attachments"
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)


@router.post("", response_model=ChatResponse)
async def process_chat_message(
    message: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user)
):
    """Process a chat message through the AI agent, with optional file attachment"""
    
    attachment_path = None
    if file:
        # Save uploaded file
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        attachment_path = os.path.join(ATTACHMENTS_DIR, unique_filename)
        
        with open(attachment_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    
    try:
        # Process message through AI agent
        result = await student_agent.process_message(
            message=message,
            conversation_id=conversation_id,
            attachment_path=attachment_path
        )
        
        # Save to chat history
        chat_record = ChatHistory(
            user_id=current_user.id,
            conversation_id=result["conversation_id"],
            message=message,
            response=result["response"],
            action_taken=result.get("action_taken")
        )
        
        await chat_record.insert()
        
        return ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"],
            action_taken=result.get("action_taken")
        )
        
    except Exception as e:
        # Clean up file if there was an error
        if attachment_path and os.path.exists(attachment_path):
            os.remove(attachment_path)
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.get("/history/{conversation_id}")
async def get_chat_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get chat history for a conversation"""
    
    history = await ChatHistory.find(
        ChatHistory.conversation_id == conversation_id,
        ChatHistory.user_id == current_user.id
    ).sort("+timestamp").to_list()
    
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "message": h.message,
                "response": h.response,
                "action_taken": h.action_taken,
                "timestamp": h.timestamp
            }
            for h in history
        ]
    }


@router.get("/conversations")
async def list_conversations(
    current_user: User = Depends(get_current_user)
):
    """List all conversations for current user"""
    
    # Get unique conversation IDs
    pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$group": {
            "_id": "$conversation_id",
            "last_message": {"$last": "$message"},
            "last_timestamp": {"$last": "$timestamp"},
            "message_count": {"$sum": 1}
        }},
        {"$sort": {"last_timestamp": -1}}
    ]
    
    # Note: Beanie might not support aggregation directly, so we'll do it manually
    all_chats = await ChatHistory.find(
        ChatHistory.user_id == current_user.id
    ).sort("-timestamp").to_list()
    
    conversations = {}
    for chat in all_chats:
        if chat.conversation_id not in conversations:
            conversations[chat.conversation_id] = {
                "conversation_id": chat.conversation_id,
                "last_message": chat.message,
                "last_timestamp": chat.timestamp,
                "message_count": 1
            }
        else:
            conversations[chat.conversation_id]["message_count"] += 1
    
    return {
        "conversations": list(conversations.values())
    }
