from fastapi import APIRouter, HTTPException, status, Depends
from models.event import Event
from models.user import User
from schemas.event import EventCreate, EventUpdate, EventResponse
from auth.dependencies import get_current_user
from models.student import Student
from services.email_service import email_service
from typing import List, Optional
from datetime import datetime
import asyncio


router = APIRouter(prefix="/api/events", tags=["Events"])


def event_to_response(event: Event) -> EventResponse:
    """Convert Event model to response schema"""
    return EventResponse(
        id=str(event.id),
        title=event.title,
        description=event.description,
        start_date=event.start_date,
        end_date=event.end_date,
        category=event.category,
        created_by=event.created_by,
        created_at=event.created_at,
        updated_at=event.updated_at
    )


async def notify_students_of_event(event: Event):
    """Send an email notification to all students about a new event."""
    try:
        students = await Student.find(Student.email != None).to_list()
        emails = [s.email for s in students if s.email]
        
        if not emails:
            return
            
        subject = f"New Department Event: {event.title}"
        body = f"""
        <h2>{event.title}</h2>
        <p><strong>Category:</strong> {event.category.title() if event.category else 'General'}</p>
        <p><strong>Starts:</strong> {event.start_date.strftime('%Y-%m-%d %H:%M')}</p>
        <p><strong>Ends:</strong> {event.end_date.strftime('%Y-%m-%d %H:%M')}</p>
        <p><strong>Description:</strong></p>
        <p>{event.description}</p>
        <br>
        <p>Best regards,<br>Department Administration Team</p>
        """
        
        # Send one email to all using BCC to protect privacy
        # Wait, the current send_email sends to all in "To".
        # Let's send them in batches or individually so students don't see everyone's email.
        # Sending individually to avoid exposing emails
        for email in emails:
            try:
                await email_service.send_email(
                    to_emails=[email],
                    subject=subject,
                    body=body,
                    html=True
                )
            except Exception as e:
                print(f"Failed to send event notification to {email}: {e}")
                
    except Exception as e:
        print(f"Error in notify_students_of_event: {e}")


@router.get("", response_model=List[EventResponse])
async def list_events(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Get list of events with optional date filtering"""
    
    query = {}
    
    if start_date and end_date:
        query["$or"] = [
            {"start_date": {"$gte": start_date, "$lte": end_date}},
            {"end_date": {"$gte": start_date, "$lte": end_date}}
        ]
    elif start_date:
        query["end_date"] = {"$gte": start_date}
    elif end_date:
        query["start_date"] = {"$lte": end_date}
    
    events = await Event.find(query).sort("+start_date").to_list()
    
    return [event_to_response(e) for e in events]


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a single event by ID"""
    
    from bson import ObjectId
    
    try:
        event = await Event.get(ObjectId(event_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    return event_to_response(event)


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new event"""
    
    if event_data.start_date >= event_data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )
    
    event = Event(
        **event_data.model_dump(),
        created_by=current_user.username
    )
    
    await event.insert()
    
    # Notify all students in the background
    asyncio.create_task(notify_students_of_event(event))
    
    return event_to_response(event)


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update an event"""
    
    from bson import ObjectId
    
    try:
        event = await Event.get(ObjectId(event_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Update fields
    update_data = event_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(event, field, value)
    
    # Validate dates
    if event.start_date >= event.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )
    
    event.updated_at = datetime.utcnow()
    await event.save()
    
    return event_to_response(event)


@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an event"""
    
    from bson import ObjectId
    
    try:
        event = await Event.get(ObjectId(event_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    await event.delete()
    
    return {"message": "Event deleted successfully"}
