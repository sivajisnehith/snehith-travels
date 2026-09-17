from typing import List
from pydantic import BaseModel


class TicketPassenger(BaseModel):
    name: str
    age: int
    gender: str
    seat_number: str


class DigitalTicketResponse(BaseModel):
    booking_reference: str
    booking_id: int
    status: str
    bus_name: str
    operator: str
    bus_type: str
    origin: str
    destination: str
    journey_date: str
    departure_time: str
    arrival_time: str
    duration: str
    boarding_point: str
    dropping_point: str
    passengers: List[TicketPassenger]
    seats: List[str]
    total_amount: float
    qr_code: str  # Safe Base64 PNG data URL containing ticket reference
    qr_content: str  # Plain reference text encoded in the QR code
