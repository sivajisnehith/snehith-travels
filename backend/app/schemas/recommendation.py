from typing import List, Optional
from pydantic import BaseModel, Field


class SeatPreferenceQuery(BaseModel):
    journey_date: str = Field(..., description="Journey date in YYYY-MM-DD format")
    cheapest: bool = False
    window: bool = False
    aisle: bool = False
    lower: bool = False
    upper: bool = False
    front: bool = False
    rear: bool = False
    sleeper: bool = False
    seater: bool = False
    maximum_budget: Optional[float] = None
    limit: int = Field(default=5, ge=1, le=20)


class RankedSeat(BaseModel):
    seat_id: int
    seat_number: str
    score: int
    reasons: List[str]
    price: float
    seat_type: str
    upper_lower: str
    window: bool
    aisle: bool
    front_rear: str


class SeatRecommendationResponse(BaseModel):
    bus_id: int
    journey_date: str
    recommended_seats: List[RankedSeat]
