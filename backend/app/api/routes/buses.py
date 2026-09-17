from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_admin
from app.models.route import Route
from app.models.user import User
from app.schemas.bus import BusResponse, BusDetailResponse, BusSeatsResponse, RouteResponse, BusCreate
from app.schemas.recommendation import SeatPreferenceQuery, SeatRecommendationResponse
from app.services.bus_service import (
    search_buses,
    get_bus_by_id,
    get_bus_seats,
    create_bus,
    delete_bus,
    get_all_buses_admin,
)
from app.services.recommendation_service import recommend_seats

router = APIRouter(prefix="/buses", tags=["Buses & Routes"])


@router.get("/routes", response_model=List[RouteResponse])
def get_routes(db: Session = Depends(get_db)):
    """List all available bus routes."""
    routes = db.query(Route).filter(Route.is_active == True).all()
    return routes


@router.get("/search", response_model=List[BusResponse])
def search_bus_services(
    from_city: str = Query(..., alias="from", description="Origin city, e.g. Hyderabad"),
    to_city: str = Query(..., alias="to", description="Destination city, e.g. Vijayawada"),
    journey_date: str = Query(..., description="Date of journey YYYY-MM-DD"),
    passengers: int = Query(default=1, ge=1, le=10, description="Number of passengers"),
    bus_type: Optional[str] = Query(None, description="AC Sleeper, Non-AC Sleeper, AC Seater, etc."),
    is_ac: Optional[bool] = Query(None, description="Filter for AC or Non-AC buses"),
    seat_type: Optional[str] = Query(None, description="'sleeper' or 'seater'"),
    price_min: Optional[float] = Query(None, description="Minimum price filter"),
    price_max: Optional[float] = Query(None, description="Maximum price filter"),
    departure_time: Optional[str] = Query(None, description="'morning', 'afternoon', 'evening', 'night'"),
    sort_by: Optional[str] = Query(None, description="'cheapest', 'earliest_departure', 'shortest_journey'"),
    db: Session = Depends(get_db),
):
    """Search buses with rich filtering and sorting options."""
    return search_buses(
        db=db,
        origin=from_city,
        destination=to_city,
        journey_date=journey_date,
        passengers=passengers,
        bus_type=bus_type,
        is_ac=is_ac,
        seat_type=seat_type,
        price_min=price_min,
        price_max=price_max,
        departure_time=departure_time,
        sort_by=sort_by,
    )


@router.get("/admin/all", response_model=List[BusResponse])
def get_all_buses_for_admin(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin endpoint: List all buses across the entire platform."""
    return get_all_buses_admin(db)


@router.post("/admin/seed-fleet")
def seed_abhibus_fleet_endpoint(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin endpoint: Trigger 1-click extensive AbhiBus-style fleet seeding."""
    from app.db.seed import seed_database
    seed_database(db)
    from app.models.bus import Bus
    count = db.query(Bus).count()
    return {"message": "Extensive fleet seeded successfully!", "total_buses": count}


@router.post("", response_model=BusResponse, status_code=status.HTTP_201_CREATED)
def add_new_bus(
    bus_in: BusCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin endpoint: Deploy a new bus service with custom route, schedule, and automatic seat layout."""
    return create_bus(db, bus_in)


@router.delete("/{bus_id}")
def remove_bus(
    bus_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin endpoint: Remove/decommission a bus from service."""
    delete_bus(db, bus_id)
    return {"message": f"Bus {bus_id} has been decommissioned successfully."}


@router.get("/{bus_id}", response_model=BusDetailResponse)
def get_bus(
    bus_id: int,
    journey_date: Optional[str] = Query(None, description="Optional journey date to include seat availability"),
    db: Session = Depends(get_db),
):
    """Get single bus details including operator, route, timings, and optional seat status."""
    return get_bus_by_id(db, bus_id, journey_date)


@router.get("/{bus_id}/seats", response_model=BusSeatsResponse)
def get_seats(
    bus_id: int,
    journey_date: str = Query(..., description="Date of journey YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """Get all seats for a bus on a specific journey date with dynamic status (available/held/booked)."""
    return get_bus_seats(db, bus_id, journey_date)


@router.post("/{bus_id}/recommend-seats", response_model=SeatRecommendationResponse)
def recommend_seats_for_bus(
    bus_id: int,
    preferences: SeatPreferenceQuery,
    db: Session = Depends(get_db),
):
    """
    Deterministic seat recommendation endpoint for Saarthi AI and smart booking.
    Ranks available seats using a transparent scoring algorithm and provides clear reasons.
    """
    return recommend_seats(db, bus_id, preferences)
