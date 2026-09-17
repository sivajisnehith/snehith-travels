from typing import List, Optional
from pydantic import BaseModel, Field


class RouteResponse(BaseModel):
    id: int
    origin: str
    destination: str
    distance_km: float
    estimated_duration_hours: float

    model_config = {"from_attributes": True}


class SeatResponse(BaseModel):
    id: int
    seat_number: str
    row: int
    column: int
    seat_type: str  # "sleeper", "seater"
    window: bool
    aisle: bool
    upper_lower: str  # "lower", "upper", "seater"
    front_rear: str   # "front", "middle", "rear"
    price: float
    status: str       # "available", "held", "booked"

    model_config = {"from_attributes": True}


class BusResponse(BaseModel):
    bus_id: int
    operator: str
    bus_name: str
    bus_type: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    duration: str
    starting_price: float
    available_seats: int
    total_seats: int
    amenities: List[str]
    rating: float
    boarding_points: List[str]
    dropping_points: List[str]

    model_config = {"from_attributes": True}


class BusDetailResponse(BusResponse):
    journey_date: Optional[str] = None
    seats: List[SeatResponse] = []


class BusSeatsResponse(BaseModel):
    bus_id: int
    bus_name: str
    bus_type: str
    journey_date: str
    total_seats: int
    available_seats: int
    seats: List[SeatResponse]


class BusCreate(BaseModel):
    origin: str
    destination: str
    operator: str = Field(default="Snehith Travels", min_length=2)
    bus_name: str = Field(..., min_length=2)
    bus_type: str = Field(default="AC Sleeper")
    is_ac: bool = True
    is_sleeper: bool = True
    departure_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    arrival_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    duration: Optional[str] = None
    starting_price: float = Field(..., gt=0)
    rating: float = Field(default=4.6, ge=1.0, le=5.0)
    amenities: List[str] = Field(default_factory=lambda: ["AC", "Charging Port", "Water Bottle"])
    boarding_points: List[str] = Field(default_factory=lambda: ["Main Stand", "City Center"])
    dropping_points: List[str] = Field(default_factory=lambda: ["Central Bus Station", "Ring Road"])
