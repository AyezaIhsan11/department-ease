from fastapi import APIRouter, HTTPException, status, Depends
from models.event import Event
from models.user import User
from schemas.event import EventCreate, EventUpdate, EventResponse
from auth.dependencies import get_current_user
from typing import List, Optional
from datetime import datetime


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
