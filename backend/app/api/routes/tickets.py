from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_optional_current_user
from app.models.user import User
from app.schemas.ticket import DigitalTicketResponse
from app.services.ticket_service import get_digital_ticket

router = APIRouter(prefix="/tickets", tags=["Digital Tickets"])


@router.get("/{booking_id}", response_model=DigitalTicketResponse)
def get_ticket(
    booking_id: str = Path(..., description="Booking ID or reference code (e.g. ST-8F4K92)"),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve digital ticket including dynamic QR code, passenger details,
    route, timings, and boarding/dropping points.
    """
    user_id = current_user.id if (current_user and current_user.role and current_user.role.name != "admin") else None
    return get_digital_ticket(db, booking_id, user_id=user_id)
