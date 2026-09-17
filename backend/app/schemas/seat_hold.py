from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SeatHoldRequest(BaseModel):
    bus_id: int
    journey_date: str = Field(..., description="Journey date YYYY-MM-DD")
    seat_ids: List[int] = Field(..., min_length=1, description="List of seat IDs to hold")


class SeatHoldReleaseRequest(BaseModel):
    hold_token: str
    seat_ids: Optional[List[int]] = None


class HeldSeatInfo(BaseModel):
    seat_id: int
    seat_number: str
    price: float


class SeatHoldResponse(BaseModel):
    hold_token: str
    bus_id: int
    journey_date: str
    held_seats: List[HeldSeatInfo]
    expires_at: datetime
    duration_minutes: int
    message: str
