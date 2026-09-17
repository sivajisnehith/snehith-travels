def test_bus_search(client):
    # Search Hyderabad -> Vijayawada
    res = client.get("/api/buses/search?from=Hyderabad&to=Vijayawada&journey_date=2026-10-15&passengers=1")
    assert res.status_code == 200
    buses = res.json()
    assert len(buses) >= 1
    bus = buses[0]
    assert bus["origin"] == "Hyderabad"
    assert bus["destination"] == "Vijayawada"
    assert "starting_price" in bus
    assert "available_seats" in bus
    assert "amenities" in bus
    assert "operator" in bus


def test_bus_search_filtering_and_sorting(client):
    # Filter AC Sleeper
    res = client.get(
        "/api/buses/search?from=Hyderabad&to=Vijayawada&journey_date=2026-10-15&bus_type=Sleeper&is_ac=true&sort_by=cheapest"
    )
    assert res.status_code == 200
    buses = res.json()
    assert len(buses) >= 1
    prices = [b["starting_price"] for b in buses]
    assert prices == sorted(prices)


def test_get_bus_and_seats(client):
    # First find a bus ID
    res = client.get("/api/buses/search?from=Hyderabad&to=Bangalore&journey_date=2026-10-15")
    assert res.status_code == 200
    buses = res.json()
    assert len(buses) > 0
    bus_id = buses[0]["bus_id"]

    # Bus details
    bus_res = client.get(f"/api/buses/{bus_id}")
    assert bus_res.status_code == 200
    assert bus_res.json()["bus_id"] == bus_id

    # Seat details
    seats_res = client.get(f"/api/buses/{bus_id}/seats?journey_date=2026-10-15")
    assert seats_res.status_code == 200
    data = seats_res.json()
    assert "seats" in data
    assert len(data["seats"]) > 0
    seat = data["seats"][0]
    assert "seat_number" in seat
    assert "seat_type" in seat
    assert "window" in seat
    assert "aisle" in seat
    assert "upper_lower" in seat
    assert "front_rear" in seat
    assert "status" in seat
