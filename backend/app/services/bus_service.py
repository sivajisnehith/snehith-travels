from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.bus import Bus
from app.models.route import Route
from app.models.seat import Seat
from app.models.seat_hold import SeatHold
from app.models.booking import Booking
from app.models.booking_seat import BookingSeat
from app.schemas.bus import BusResponse, BusDetailResponse, BusSeatsResponse, SeatResponse, BusCreate


def get_seat_statuses_for_journey(
    db: Session,
    bus_id: int,
    journey_date: str,
) -> Dict[int, str]:
    """
    Returns a mapping of seat_id -> status ('available', 'held', 'booked')
    for a given bus on a specific journey date.
    """
    now = datetime.now(timezone.utc)
    
    # 1. Check booked seats
    booked_seat_rows = (
        db.query(BookingSeat.seat_id)
        .join(Booking, Booking.id == BookingSeat.booking_id)
        .filter(
            Booking.bus_id == bus_id,
            Booking.journey_date == journey_date,
            Booking.status.in_(["CONFIRMED", "PAYMENT_SUCCESS", "PENDING_PAYMENT"]),
        )
        .all()
    )
    booked_seat_ids = {row[0] for row in booked_seat_rows}

    # 2. Check actively held seats (not expired)
    held_seat_rows = (
        db.query(SeatHold.seat_id)
        .filter(
            SeatHold.bus_id == bus_id,
            SeatHold.journey_date == journey_date,
            SeatHold.status == "ACTIVE",
            SeatHold.expires_at > now,
        )
        .all()
    )
    held_seat_ids = {row[0] for row in held_seat_rows}

    # 3. Retrieve all seats for this bus
    seats = db.query(Seat).filter(Seat.bus_id == bus_id, Seat.is_active == True).all()
    
    statuses = {}
    for s in seats:
        if s.id in booked_seat_ids:
            statuses[s.id] = "booked"
        elif s.id in held_seat_ids:
            statuses[s.id] = "held"
        else:
            statuses[s.id] = "available"
            
    return statuses


def get_bus_seats(
    db: Session,
    bus_id: int,
    journey_date: str,
) -> BusSeatsResponse:
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bus with ID {bus_id} not found."
        )

    statuses = get_seat_statuses_for_journey(db, bus_id, journey_date)
    seats = (
        db.query(Seat)
        .filter(Seat.bus_id == bus_id, Seat.is_active == True)
        .order_by(Seat.row, Seat.column)
        .all()
    )

    seat_responses = []
    available_count = 0
    for s in seats:
        st = statuses.get(s.id, "available")
        if st == "available":
            available_count += 1
        seat_responses.append(
            SeatResponse(
                id=s.id,
                seat_number=s.seat_number,
                row=s.row,
                column=s.column,
                seat_type=s.seat_type,
                window=s.window,
                aisle=s.aisle,
                upper_lower=s.upper_lower,
                front_rear=s.front_rear,
                price=s.base_price,
                status=st,
            )
        )

    return BusSeatsResponse(
        bus_id=bus.id,
        bus_name=bus.bus_name,
        bus_type=bus.bus_type,
        journey_date=journey_date,
        total_seats=len(seats),
        available_seats=available_count,
        seats=seat_responses,
    )


def search_buses(
    db: Session,
    origin: str,
    destination: str,
    journey_date: str,
    passengers: int = 1,
    bus_type: Optional[str] = None,
    is_ac: Optional[bool] = None,
    seat_type: Optional[str] = None,  # "sleeper" or "seater"
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    departure_time: Optional[str] = None,  # "morning", "afternoon", "evening", "night" or HH:MM
    sort_by: Optional[str] = None,  # "cheapest", "earliest_departure", "shortest_journey"
) -> List[BusResponse]:
    query = (
        db.query(Bus, Route)
        .join(Route, Route.id == Bus.route_id)
        .filter(
            func.lower(Route.origin) == origin.lower().strip(),
            func.lower(Route.destination) == destination.lower().strip(),
            Route.is_active == True,
        )
    )

    if bus_type:
        if bus_type.lower() == "sleeper":
            query = query.filter(Bus.is_sleeper == True)
        elif bus_type.lower() == "seater":
            query = query.filter(Bus.is_sleeper == False)
        else:
            query = query.filter(func.lower(Bus.bus_type).contains(bus_type.lower()))
    if is_ac is not None:
        query = query.filter(Bus.is_ac == is_ac)
    if seat_type:
        if seat_type.lower() == "sleeper":
            query = query.filter(Bus.is_sleeper == True)
        elif seat_type.lower() == "seater":
            query = query.filter(Bus.is_sleeper == False)
    if price_min is not None:
        query = query.filter(Bus.starting_price >= price_min)
    if price_max is not None:
        query = query.filter(Bus.starting_price <= price_max)

    results = query.all()
    matched_buses: List[BusResponse] = []

    for bus, route in results:
        statuses = get_seat_statuses_for_journey(db, bus.id, journey_date)
        available_seats = sum(1 for st in statuses.values() if st == "available")

        # Skip if not enough seats for passengers
        if available_seats < passengers:
            continue

        # Departure time filtering if time-of-day provided
        dep_hour = int(bus.departure_time.split(":")[0])
        if departure_time:
            dt = departure_time.lower().strip()
            if dt == "morning" and not (6 <= dep_hour < 12):
                continue
            elif dt == "afternoon" and not (12 <= dep_hour < 17):
                continue
            elif dt == "evening" and not (17 <= dep_hour < 21):
                continue
            elif dt == "night" and not (dep_hour >= 21 or dep_hour < 6):
                continue

        matched_buses.append(
            BusResponse(
                bus_id=bus.id,
                operator=bus.operator,
                bus_name=bus.bus_name,
                bus_type=bus.bus_type,
                origin=route.origin,
                destination=route.destination,
                departure_time=bus.departure_time,
                arrival_time=bus.arrival_time,
                duration=bus.duration,
                starting_price=bus.starting_price,
                available_seats=available_seats,
                total_seats=bus.total_seats,
                amenities=bus.amenities or [],
                rating=bus.rating,
                boarding_points=bus.boarding_points or [],
                dropping_points=bus.dropping_points or [],
            )
        )

    # Sorting
    if sort_by == "cheapest":
        matched_buses.sort(key=lambda b: b.starting_price)
    elif sort_by == "earliest_departure":
        matched_buses.sort(key=lambda b: b.departure_time)
    elif sort_by == "shortest_journey":
        def parse_duration(d: str) -> int:
            try:
                parts = d.split()
                hours = int(parts[0].replace("h", ""))
                mins = int(parts[1].replace("m", "")) if len(parts) > 1 else 0
                return hours * 60 + mins
            except Exception:
                return 9999
        matched_buses.sort(key=lambda b: parse_duration(b.duration))

    return matched_buses


def get_bus_by_id(db: Session, bus_id: int, journey_date: Optional[str] = None) -> BusDetailResponse:
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bus with ID {bus_id} not found."
        )

    route = db.query(Route).filter(Route.id == bus.route_id).first()
    origin = route.origin if route else ""
    destination = route.destination if route else ""

    seat_list: List[SeatResponse] = []
    available_count = 0

    if journey_date:
        statuses = get_seat_statuses_for_journey(db, bus.id, journey_date)
        seats = (
            db.query(Seat)
            .filter(Seat.bus_id == bus.id, Seat.is_active == True)
            .order_by(Seat.row, Seat.column)
            .all()
        )
        for s in seats:
            st = statuses.get(s.id, "available")
            if st == "available":
                available_count += 1
            seat_list.append(
                SeatResponse(
                    id=s.id,
                    seat_number=s.seat_number,
                    row=s.row,
                    column=s.column,
                    seat_type=s.seat_type,
                    window=s.window,
                    aisle=s.aisle,
                    upper_lower=s.upper_lower,
                    front_rear=s.front_rear,
                    price=s.base_price,
                    status=st,
                )
            )
    else:
        seats = (
            db.query(Seat)
            .filter(Seat.bus_id == bus.id, Seat.is_active == True)
            .order_by(Seat.row, Seat.column)
            .all()
        )
        available_count = len(seats)
        for s in seats:
            seat_list.append(
                SeatResponse(
                    id=s.id,
                    seat_number=s.seat_number,
                    row=s.row,
                    column=s.column,
                    seat_type=s.seat_type,
                    window=s.window,
                    aisle=s.aisle,
                    upper_lower=s.upper_lower,
                    front_rear=s.front_rear,
                    price=s.base_price,
                    status="available",
                )
            )

    return BusDetailResponse(
        bus_id=bus.id,
        operator=bus.operator,
        bus_name=bus.bus_name,
        bus_type=bus.bus_type,
        origin=origin,
        destination=destination,
        departure_time=bus.departure_time,
        arrival_time=bus.arrival_time,
        duration=bus.duration,
        starting_price=bus.starting_price,
        available_seats=available_count,
        total_seats=bus.total_seats,
        amenities=bus.amenities or [],
        rating=bus.rating,
        boarding_points=bus.boarding_points or [],
        dropping_points=bus.dropping_points or [],
        journey_date=journey_date,
        seats=seat_list,
    )


def calculate_duration(dep: str, arr: str) -> str:
    try:
        dh, dm = map(int, dep.split(":"))
        ah, am = map(int, arr.split(":"))
        dep_mins = dh * 60 + dm
        arr_mins = ah * 60 + am
        if arr_mins < dep_mins:
            arr_mins += 24 * 60
        diff = arr_mins - dep_mins
        return f"{diff // 60}h {diff % 60:02d}m"
    except Exception:
        return "6h 00m"


def generate_bus_seats(db: Session, bus: Bus) -> None:
    seats_to_add = []
    if bus.is_sleeper:
        for deck, deck_name in [("L", "lower"), ("U", "upper")]:
            seat_num = 1
            for r in range(1, 6):
                pos = "front" if r <= 2 else ("middle" if r <= 4 else "rear")
                seats_to_add.append(
                    Seat(
                        bus_id=bus.id,
                        seat_number=f"{deck}{seat_num}",
                        row=r,
                        column=1,
                        seat_type="sleeper",
                        window=True,
                        aisle=False,
                        upper_lower=deck_name,
                        front_rear=pos,
                        base_price=bus.starting_price + (100 if deck_name == "lower" else 0) + (50 if pos == "front" else 0),
                        is_active=True,
                    )
                )
                seat_num += 1
                seats_to_add.append(
                    Seat(
                        bus_id=bus.id,
                        seat_number=f"{deck}{seat_num}",
                        row=r,
                        column=3,
                        seat_type="sleeper",
                        window=False,
                        aisle=True,
                        upper_lower=deck_name,
                        front_rear=pos,
                        base_price=bus.starting_price + (50 if deck_name == "lower" else 0),
                        is_active=True,
                    )
                )
                seat_num += 1
                seats_to_add.append(
                    Seat(
                        bus_id=bus.id,
                        seat_number=f"{deck}{seat_num}",
                        row=r,
                        column=4,
                        seat_type="sleeper",
                        window=True,
                        aisle=False,
                        upper_lower=deck_name,
                        front_rear=pos,
                        base_price=bus.starting_price + (100 if deck_name == "lower" else 0) + (50 if pos == "front" else 0),
                        is_active=True,
                    )
                )
                seat_num += 1
    else:
        seat_num = 1
        for r in range(1, 9):
            pos = "front" if r <= 2 else ("middle" if r <= 6 else "rear")
            for col, is_win, is_ais in [(1, True, False), (2, False, True), (3, False, True), (4, True, False)]:
                seats_to_add.append(
                    Seat(
                        bus_id=bus.id,
                        seat_number=f"S{seat_num}",
                        row=r,
                        column=col,
                        seat_type="seater",
                        window=is_win,
                        aisle=is_ais,
                        upper_lower="seater",
                        front_rear=pos,
                        base_price=bus.starting_price + (50 if is_win else 0),
                        is_active=True,
                    )
                )
                seat_num += 1

    db.add_all(seats_to_add)
    db.commit()


def create_bus(db: Session, bus_in: BusCreate) -> BusResponse:
    orig = bus_in.origin.strip()
    dest = bus_in.destination.strip()
    route = db.query(Route).filter(Route.origin.ilike(orig), Route.destination.ilike(dest)).first()
    if not route:
        route = Route(
            origin=orig,
            destination=dest,
            distance_km=350.0,
            estimated_duration_hours=6.0,
            is_active=True,
        )
        db.add(route)
        db.commit()
        db.refresh(route)

    duration = bus_in.duration or calculate_duration(bus_in.departure_time, bus_in.arrival_time)
    total_seats = 30 if bus_in.is_sleeper else 32

    bus = Bus(
        route_id=route.id,
        operator=bus_in.operator,
        bus_name=bus_in.bus_name,
        bus_type=bus_in.bus_type,
        is_ac=bus_in.is_ac,
        is_sleeper=bus_in.is_sleeper,
        departure_time=bus_in.departure_time,
        arrival_time=bus_in.arrival_time,
        duration=duration,
        starting_price=bus_in.starting_price,
        amenities=bus_in.amenities,
        rating=bus_in.rating,
        total_seats=total_seats,
        boarding_points=bus_in.boarding_points,
        dropping_points=bus_in.dropping_points,
    )
    db.add(bus)
    db.commit()
    db.refresh(bus)

    generate_bus_seats(db, bus)

    return BusResponse(
        bus_id=bus.id,
        operator=bus.operator,
        bus_name=bus.bus_name,
        bus_type=bus.bus_type,
        origin=route.origin,
        destination=route.destination,
        departure_time=bus.departure_time,
        arrival_time=bus.arrival_time,
        duration=bus.duration,
        starting_price=bus.starting_price,
        available_seats=total_seats,
        total_seats=total_seats,
        amenities=bus.amenities or [],
        rating=bus.rating,
        boarding_points=bus.boarding_points or [],
        dropping_points=bus.dropping_points or [],
    )


def delete_bus(db: Session, bus_id: int) -> bool:
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bus with ID {bus_id} not found."
        )
    db.delete(bus)
    db.commit()
    return True


def get_all_buses_admin(db: Session) -> List[BusResponse]:
    buses = db.query(Bus).order_by(Bus.id.desc()).all()
    results = []
    for b in buses:
        origin = b.route.origin if b.route else "Unknown"
        destination = b.route.destination if b.route else "Unknown"
        results.append(
            BusResponse(
                bus_id=b.id,
                operator=b.operator,
                bus_name=b.bus_name,
                bus_type=b.bus_type,
                origin=origin,
                destination=destination,
                departure_time=b.departure_time,
                arrival_time=b.arrival_time,
                duration=b.duration,
                starting_price=b.starting_price,
                available_seats=b.total_seats,
                total_seats=b.total_seats,
                amenities=b.amenities or [],
                rating=b.rating,
                boarding_points=b.boarding_points or [],
                dropping_points=b.dropping_points or [],
            )
        )
    return results

