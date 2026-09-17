from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PassengerCreate(BaseModel):
    seat_id: int
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=1, le=120)
    gender: str = Field(..., pattern="^(M|F|Other)$")


class BookingCreate(BaseModel):
    bus_id: int
    journey_date: str = Field(..., description="Journey date in YYYY-MM-DD format")
    boarding_point: str = Field(..., min_length=2)
    dropping_point: str = Field(..., min_length=2)
    passengers: List[PassengerCreate] = Field(..., min_length=1)
    hold_token: Optional[str] = None


class PassengerResponse(BaseModel):
    id: int
    seat_id: int
    seat_number: str
    name: str
    age: int
    gender: str

    model_config = {"from_attributes": True}


class BookingResponse(BaseModel):
    id: int
    booking_reference: str
    user_id: int
    bus_id: int
    journey_date: str
    boarding_point: str
    dropping_point: str
    total_amount: float
    status: str
    created_at: datetime
    updated_at: datetime
    seat_numbers: List[str]

    model_config = {"from_attributes": True}


class BookingDetailResponse(BookingResponse):
    bus_name: str
    operator: str
    bus_type: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    passengers: List[PassengerResponse]
    payment_status: Optional[str] = None
    payment_id: Optional[int] = None


class BookingCancelResponse(BaseModel):
    booking_id: int
    booking_reference: str
    status: str
    message: str
