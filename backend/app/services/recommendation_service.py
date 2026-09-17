from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.bus import Bus
from app.models.seat import Seat
from app.schemas.recommendation import (
    SeatPreferenceQuery,
    SeatRecommendationResponse,
    RankedSeat,
)
from app.services.bus_service import get_seat_statuses_for_journey


def recommend_seats(
    db: Session,
    bus_id: int,
    preferences: SeatPreferenceQuery,
) -> SeatRecommendationResponse:
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bus with ID {bus_id} not found."
        )

    statuses = get_seat_statuses_for_journey(db, bus_id, preferences.journey_date)
    seats = db.query(Seat).filter(Seat.bus_id == bus_id, Seat.is_active == True).all()

    # Filter only available seats
    available_seats = [s for s in seats if statuses.get(s.id) == "available"]
    if not available_seats:
        return SeatRecommendationResponse(
            bus_id=bus_id,
            journey_date=preferences.journey_date,
            recommended_seats=[],
        )

    # Calculate min price among available seats
    min_price = min(s.base_price for s in available_seats)

    # Check if any preference was explicitly requested
    has_explicit_pref = any([
        preferences.cheapest,
        preferences.window,
        preferences.aisle,
        preferences.lower,
        preferences.upper,
        preferences.front,
        preferences.rear,
        preferences.sleeper,
        preferences.seater,
        preferences.maximum_budget is not None,
    ])

    scored_seats: List[RankedSeat] = []

    for seat in available_seats:
        # Check budget constraint first
        if preferences.maximum_budget is not None and seat.base_price > preferences.maximum_budget:
            continue

        score = 0
        reasons: List[str] = []

        if has_explicit_pref:
            if preferences.window and seat.window:
                score += 30
                reasons.append("window")
            if preferences.aisle and seat.aisle:
                score += 15
                reasons.append("aisle")
            if preferences.lower and seat.upper_lower == "lower":
                score += 25
                reasons.append("lower berth")
            if preferences.upper and seat.upper_lower == "upper":
                score += 20
                reasons.append("upper berth")
            if preferences.front and seat.front_rear == "front":
                score += 15
                reasons.append("front")
            if preferences.rear and seat.front_rear == "rear":
                score += 10
                reasons.append("rear")
            if preferences.cheapest and seat.base_price <= min_price:
                score += 20
                reasons.append(f"cheapest fare (₹{int(seat.base_price)})")
            if preferences.sleeper and seat.seat_type == "sleeper":
                score += 10
                reasons.append("sleeper berth")
            if preferences.seater and seat.seat_type == "seater":
                score += 10
                reasons.append("seater seat")
            if preferences.maximum_budget is not None and seat.base_price <= preferences.maximum_budget:
                score += 15
                reasons.append("within budget")
        else:
            # Smart default heuristic when no preference is specified
            if seat.window:
                score += 30
                reasons.append("window")
            if seat.upper_lower == "lower":
                score += 25
                reasons.append("lower berth")
            if seat.front_rear == "front":
                score += 15
                reasons.append("front")
            if seat.base_price <= min_price:
                score += 20
                reasons.append(f"cheapest fare (₹{int(seat.base_price)})")
            if seat.seat_type == "sleeper":
                score += 10
                reasons.append("sleeper")

        scored_seats.append(
            RankedSeat(
                seat_id=seat.id,
                seat_number=seat.seat_number,
                score=score,
                reasons=reasons,
                price=seat.base_price,
                seat_type=seat.seat_type,
                upper_lower=seat.upper_lower,
                window=seat.window,
                aisle=seat.aisle,
                front_rear=seat.front_rear,
            )
        )

    # Sort deterministically: highest score first, then lowest price, then seat_number
    scored_seats.sort(key=lambda s: (-s.score, s.price, s.seat_number))

    return SeatRecommendationResponse(
        bus_id=bus_id,
        journey_date=preferences.journey_date,
        recommended_seats=scored_seats[: preferences.limit],
    )
