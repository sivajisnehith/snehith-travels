import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.bus import Bus
from app.models.seat import Seat
from app.models.seat_hold import SeatHold
from app.models.booking import Booking
from app.models.booking_seat import BookingSeat
from app.schemas.seat_hold import SeatHoldResponse, HeldSeatInfo


def cleanup_expired_holds(db: Session) -> int:
    """Marks all expired active holds as RELEASED."""
    now = datetime.now(timezone.utc)
    expired = (
        db.query(SeatHold)
        .filter(SeatHold.status == "ACTIVE", SeatHold.expires_at <= now)
        .all()
    )
    for hold in expired:
        hold.status = "RELEASED"
    if expired:
        db.commit()
    return len(expired)


def hold_seats(
    db: Session,
    bus_id: int,
    seat_ids: List[int],
    journey_date: str,
    user_id: Optional[int] = None,
) -> SeatHoldResponse:
    if not seat_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one seat ID must be provided to hold."
        )

    # First clean up any expired holds
    cleanup_expired_holds(db)
    now = datetime.now(timezone.utc)

    # Verify bus
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bus with ID {bus_id} not found."
        )

    # Verify seats belong to bus
    seats = (
        db.query(Seat)
        .filter(Seat.id.in_(seat_ids), Seat.bus_id == bus_id, Seat.is_active == True)
        .all()
    )
    if len(seats) != len(set(seat_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more requested seats are invalid or do not belong to this bus."
        )

    seat_map = {s.id: s for s in seats}

    # Check for already booked seats for this journey date
    booked_conflicts = (
        db.query(BookingSeat.seat_id)
        .join(Booking, Booking.id == BookingSeat.booking_id)
        .filter(
            Booking.bus_id == bus_id,
            Booking.journey_date == journey_date,
            Booking.status.in_(["CONFIRMED", "PAYMENT_SUCCESS", "PENDING_PAYMENT"]),
            BookingSeat.seat_id.in_(seat_ids),
        )
        .all()
    )
    if booked_conflicts:
        conflict_ids = [r[0] for r in booked_conflicts]
        conflict_numbers = [seat_map[sid].seat_number for sid in conflict_ids if sid in seat_map]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Seat(s) {', '.join(conflict_numbers)} are already booked."
        )

    # Check for active holds by other users
    held_conflicts = (
        db.query(SeatHold)
        .filter(
            SeatHold.bus_id == bus_id,
            SeatHold.journey_date == journey_date,
            SeatHold.seat_id.in_(seat_ids),
            SeatHold.status == "ACTIVE",
            SeatHold.expires_at > now,
        )
        .all()
    )
    if held_conflicts:
        conflict_numbers = [seat_map[h.seat_id].seat_number for h in held_conflicts if h.seat_id in seat_map]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Seat(s) {', '.join(conflict_numbers)} are temporarily held by another customer."
        )

    # Create new hold
    hold_token = f"hold_{uuid.uuid4().hex}"
    expires_at = now + timedelta(minutes=settings.SEAT_HOLD_DURATION_MINUTES)

    held_seat_infos: List[HeldSeatInfo] = []
    for sid in seat_ids:
        s = seat_map[sid]
        new_hold = SeatHold(
            bus_id=bus_id,
            seat_id=sid,
            journey_date=journey_date,
            user_id=user_id,
            hold_token=hold_token,
            expires_at=expires_at,
            status="ACTIVE",
        )
        db.add(new_hold)
        held_seat_infos.append(
            HeldSeatInfo(
                seat_id=s.id,
                seat_number=s.seat_number,
                price=s.base_price,
            )
        )

    db.commit()

    return SeatHoldResponse(
        hold_token=hold_token,
        bus_id=bus_id,
        journey_date=journey_date,
        held_seats=held_seat_infos,
        expires_at=expires_at,
        duration_minutes=settings.SEAT_HOLD_DURATION_MINUTES,
        message=f"Seats held successfully for {settings.SEAT_HOLD_DURATION_MINUTES} minutes.",
    )


def release_hold(
    db: Session,
    hold_token: str,
    seat_ids: Optional[List[int]] = None,
) -> bool:
    query = db.query(SeatHold).filter(
        SeatHold.hold_token == hold_token,
        SeatHold.status == "ACTIVE",
    )
    if seat_ids:
        query = query.filter(SeatHold.seat_id.in_(seat_ids))

    holds = query.all()
    if not holds:
        return False

    for h in holds:
        h.status = "RELEASED"
    db.commit()
    return True
