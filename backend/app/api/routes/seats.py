from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_optional_current_user
from app.models.user import User
from app.schemas.seat_hold import SeatHoldRequest, SeatHoldReleaseRequest, SeatHoldResponse
from app.services.seat_hold_service import hold_seats, release_hold

router = APIRouter(prefix="/seats", tags=["Seat Management & Holds"])


@router.post("/hold", response_model=SeatHoldResponse)
def hold_bus_seats(
    payload: SeatHoldRequest,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Temporarily hold one or more seats for 10 minutes to prevent double booking.
    Safe with transactional isolation.
    """
    user_id = current_user.id if current_user else None
    return hold_seats(
        db=db,
        bus_id=payload.bus_id,
        seat_ids=payload.seat_ids,
        journey_date=payload.journey_date,
        user_id=user_id,
    )


@router.delete("/hold")
def release_bus_seats(
    payload: SeatHoldReleaseRequest,
    db: Session = Depends(get_db),
):
    """Release temporarily held seats so other customers can book them."""
    success = release_hold(db, payload.hold_token, payload.seat_ids)
    return {
        "success": success,
        "message": "Seat hold released successfully." if success else "No active hold found."
    }
