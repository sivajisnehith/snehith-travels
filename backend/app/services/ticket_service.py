import io
import base64
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import qrcode
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.route import Route
from app.schemas.ticket import DigitalTicketResponse, TicketPassenger


def generate_ticket_qr_code(booking_reference: str) -> str:
    """Generates a safe base64 data URL PNG QR code containing ONLY the ticket reference."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=2,
    )
    # Safe reference string
    qr.add_data(f"SNEHITH_TRAVELS_TICKET:{booking_reference}")
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64_encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_encoded}"


def get_digital_ticket(
    db: Session,
    booking_id_or_ref: str,
    user_id: Optional[int] = None,
) -> DigitalTicketResponse:
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
            detail="Ticket or booking not found."
        )

    bus = booking.bus
    route = db.query(Route).filter(Route.id == bus.route_id).first()

    ticket_passengers: List[TicketPassenger] = []
    seat_numbers: List[str] = []

    for p in booking.passengers:
        s = db.query(Seat).filter(Seat.id == p.seat_id).first()
        seat_no = s.seat_number if s else "N/A"
        seat_numbers.append(seat_no)
        ticket_passengers.append(
            TicketPassenger(
                name=p.name,
                age=p.age,
                gender=p.gender,
                seat_number=seat_no,
            )
        )

    qr_image = generate_ticket_qr_code(booking.booking_reference)

    return DigitalTicketResponse(
        booking_reference=booking.booking_reference,
        booking_id=booking.id,
        status=booking.status,
        bus_name=bus.bus_name,
        operator=bus.operator,
        bus_type=bus.bus_type,
        origin=route.origin if route else "",
        destination=route.destination if route else "",
        journey_date=booking.journey_date,
        departure_time=bus.departure_time,
        arrival_time=bus.arrival_time,
        duration=bus.duration,
        boarding_point=booking.boarding_point,
        dropping_point=booking.dropping_point,
        passengers=ticket_passengers,
        seats=seat_numbers,
        total_amount=booking.total_amount,
        qr_code=qr_image,
        qr_content=f"SNEHITH_TRAVELS_TICKET:{booking.booking_reference}",
    )
