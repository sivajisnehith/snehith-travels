from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, get_current_admin, get_optional_current_user
from app.models.user import User
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingDetailResponse,
    BookingCancelResponse,
)
from app.services.booking_service import (
    create_booking,
    get_booking_detail,
    list_user_bookings,
    list_all_bookings_admin,
    cancel_booking,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=BookingResponse, status_code=201)
def make_booking(
    booking_in: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new bus reservation in PENDING_PAYMENT state.
    Converts any temporary seat hold into the booking.
    """
    return create_booking(db, booking_in, current_user.id)


@router.get("/admin/all", response_model=List[BookingDetailResponse])
def get_all_platform_bookings_admin(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin endpoint: Retrieve all bookings across all users and routes."""
    return list_all_bookings_admin(db)


@router.get("", response_model=List[BookingDetailResponse])
def get_user_bookings(
    all: bool = Query(default=False, description="Admins only: set to true to list all platform bookings"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List bookings for the authenticated user, or all bookings if admin with all=True."""
    if all and current_user.role and current_user.role.name == "admin":
        return list_all_bookings_admin(db)
    return list_user_bookings(db, current_user.id)


@router.get("/{booking_id}", response_model=BookingDetailResponse)
def get_single_booking(
    booking_id: str = Path(..., description="Booking ID or Booking Reference, e.g. ST-8F4K92"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Get booking details by ID or reference code without requiring authentication."""
    return get_booking_detail(db, booking_id, user_id=None)


@router.post("/{booking_id}/cancel", response_model=BookingCancelResponse)
def cancel_existing_booking(
    booking_id: int = Path(..., description="Numeric ID of the booking to cancel"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel a booking and free up the seats."""
    user_id = None if (current_user.role and current_user.role.name == "admin") else current_user.id
    return cancel_booking(db, booking_id, user_id=user_id)
