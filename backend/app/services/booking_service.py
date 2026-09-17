import random
import string
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.booking import Booking
from app.models.booking_seat import BookingSeat
from app.models.passenger import Passenger
from app.models.bus import Bus
from app.models.route import Route
from app.models.seat import Seat
from app.models.seat_hold import SeatHold
from app.models.payment import Payment
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingDetailResponse,
    PassengerResponse,
    BookingCancelResponse,
)
from app.services.seat_hold_service import cleanup_expired_holds


def generate_booking_reference() -> str:
    chars = string.ascii_uppercase + string.digits
    # Avoid ambiguous characters like O, 0, I, 1 if preferred, or standard uppercase
    safe_chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    suffix = "".join(random.choices(safe_chars, k=6))
    return f"ST-{suffix}"


def create_booking(
    db: Session,
    booking_in: BookingCreate,
    user_id: int,
) -> BookingResponse:
    # 1. Clean up expired holds
    cleanup_expired_holds(db)
    now = datetime.now(timezone.utc)

    # 2. Check bus
    bus = db.query(Bus).filter(Bus.id == booking_in.bus_id).first()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bus with ID {booking_in.bus_id} not found."
        )

    # 3. Validate passengers
    if not booking_in.passengers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one passenger must be provided."
        )

    requested_seat_ids = [p.seat_id for p in booking_in.passengers]
    if len(requested_seat_ids) != len(set(requested_seat_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate seat assignments among passengers."
        )

    for p in booking_in.passengers:
        if not p.name.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passenger name cannot be empty.")
        if p.age < 1 or p.age > 120:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid age for passenger {p.name}.")
        if p.gender not in ["M", "F", "Other"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid gender for passenger {p.name}.")

    # 4. Fetch and validate seats
    seats = (
        db.query(Seat)
        .filter(
            Seat.id.in_(requested_seat_ids),
            Seat.bus_id == booking_in.bus_id,
            Seat.is_active == True,
        )
        .all()
    )
    if len(seats) != len(requested_seat_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more selected seats are invalid for this bus."
        )
    seat_map = {s.id: s for s in seats}

    # 5. Check if seats are already booked
    booked_conflicts = (
        db.query(BookingSeat.seat_id)
        .join(Booking, Booking.id == BookingSeat.booking_id)
        .filter(
            Booking.bus_id == booking_in.bus_id,
            Booking.journey_date == booking_in.journey_date,
            Booking.status.in_(["CONFIRMED", "PAYMENT_SUCCESS", "PENDING_PAYMENT"]),
            BookingSeat.seat_id.in_(requested_seat_ids),
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

    # 6. Check hold tokens
    if booking_in.hold_token:
        holds = (
            db.query(SeatHold)
            .filter(
                SeatHold.hold_token == booking_in.hold_token,
                SeatHold.status == "ACTIVE",
                SeatHold.expires_at > now,
                SeatHold.journey_date == booking_in.journey_date,
            )
            .all()
        )
        held_ids = {h.seat_id for h in holds}
        for sid in requested_seat_ids:
            if sid not in held_ids:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Hold for seat {seat_map[sid].seat_number} has expired or is invalid."
                )
    else:
        # Check that no other active hold exists on these seats
        other_holds = (
            db.query(SeatHold)
            .filter(
                SeatHold.bus_id == booking_in.bus_id,
                SeatHold.journey_date == booking_in.journey_date,
                SeatHold.seat_id.in_(requested_seat_ids),
                SeatHold.status == "ACTIVE",
                SeatHold.expires_at > now,
            )
            .all()
        )
        if other_holds:
            conflict_numbers = [seat_map[h.seat_id].seat_number for h in other_holds if h.seat_id in seat_map]
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Seat(s) {', '.join(conflict_numbers)} are currently held by another customer."
            )

    # 7. Generate reference and calculate total
    booking_ref = generate_booking_reference()
    total_amount = sum(seat_map[sid].base_price for sid in requested_seat_ids)

    # 8. Create booking record
    booking = Booking(
        booking_reference=booking_ref,
        user_id=user_id,
        bus_id=booking_in.bus_id,
        journey_date=booking_in.journey_date,
        boarding_point=booking_in.boarding_point,
        dropping_point=booking_in.dropping_point,
        total_amount=total_amount,
        status="PENDING_PAYMENT",
    )
    db.add(booking)
    db.flush()

    # 9. Add booking seats & passengers
    for p in booking_in.passengers:
        s = seat_map[p.seat_id]
        booking_seat = BookingSeat(
            booking_id=booking.id,
            seat_id=s.id,
            price_paid=s.base_price,
        )
        db.add(booking_seat)

        passenger = Passenger(
            booking_id=booking.id,
            seat_id=s.id,
            name=p.name.strip(),
            age=p.age,
            gender=p.gender,
        )
        db.add(passenger)

    # 10. Mark holds as CONVERTED
    if booking_in.hold_token:
        for h in holds:
            h.status = "CONVERTED"

    db.commit()
    db.refresh(booking)

    seat_numbers = [seat_map[sid].seat_number for sid in requested_seat_ids]

    return BookingResponse(
        id=booking.id,
        booking_reference=booking.booking_reference,
        user_id=booking.user_id,
        bus_id=booking.bus_id,
        journey_date=booking.journey_date,
        boarding_point=booking.boarding_point,
        dropping_point=booking.dropping_point,
        total_amount=booking.total_amount,
        status=booking.status,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        seat_numbers=seat_numbers,
    )


def get_booking_detail(
    db: Session,
    booking_id_or_ref: str,
    user_id: Optional[int] = None,
) -> BookingDetailResponse:
    query = db.query(Booking)
    if booking_id_or_ref.isdigit():
        query = query.filter(Booking.id == int(booking_id_or_ref))
    else:
        query = query.filter(Booking.booking_reference == booking_id_or_ref)

    if user_id is not None:
        query = query.filter(Booking.user_id == user_id)

    booking = query.first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found."
        )

    bus = booking.bus
    route = db.query(Route).filter(Route.id == bus.route_id).first()

    passengers_resp = []
    seat_numbers = []
    for p in booking.passengers:
        s = db.query(Seat).filter(Seat.id == p.seat_id).first()
        seat_no = s.seat_number if s else "N/A"
        seat_numbers.append(seat_no)
        passengers_resp.append(
            PassengerResponse(
                id=p.id,
                seat_id=p.seat_id,
                seat_number=seat_no,
                name=p.name,
                age=p.age,
                gender=p.gender,
            )
        )

    payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()

    return BookingDetailResponse(
        id=booking.id,
        booking_reference=booking.booking_reference,
        user_id=booking.user_id,
        bus_id=booking.bus_id,
        journey_date=booking.journey_date,
        boarding_point=booking.boarding_point,
        dropping_point=booking.dropping_point,
        total_amount=booking.total_amount,
        status=booking.status,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        seat_numbers=seat_numbers,
        bus_name=bus.bus_name,
        operator=bus.operator,
        bus_type=bus.bus_type,
        origin=route.origin if route else "",
        destination=route.destination if route else "",
        departure_time=bus.departure_time,
        arrival_time=bus.arrival_time,
        passengers=passengers_resp,
        payment_status=payment.status if payment else None,
        payment_id=payment.id if payment else None,
    )


def list_user_bookings(db: Session, user_id: int) -> List[BookingDetailResponse]:
    bookings = (
        db.query(Booking)
        .filter(Booking.user_id == user_id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    results = []
    for b in bookings:
        results.append(get_booking_detail(db, str(b.id), user_id=None))
    return results


def list_all_bookings_admin(db: Session) -> List[BookingDetailResponse]:
    """Retrieve all bookings across the entire platform for admin inspection."""
    bookings = (
        db.query(Booking)
        .order_by(Booking.created_at.desc())
        .all()
    )
    results = []
    for b in bookings:
        results.append(get_booking_detail(db, str(b.id), user_id=None))
    return results


def cancel_booking(
    db: Session,
    booking_id: int,
    user_id: Optional[int] = None,
) -> BookingCancelResponse:
    query = db.query(Booking).filter(Booking.id == booking_id)
    if user_id is not None:
        query = query.filter(Booking.user_id == user_id)

    booking = query.first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found."
        )

    if booking.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled."
        )

    booking.status = "CANCELLED"
    booking.updated_at = datetime.now(timezone.utc)
    db.commit()

    return BookingCancelResponse(
        booking_id=booking.id,
        booking_reference=booking.booking_reference,
        status="CANCELLED",
        message="Booking cancelled successfully.",
    )
