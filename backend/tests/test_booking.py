def get_auth_token(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "demo@snehithtravels.com", "password": "DemoPassword123!"},
    )
    return res.json()["access_token"]


def test_create_and_manage_booking(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Search bus
    bus_res = client.get("/api/buses/search?from=Hyderabad&to=Vijayawada&journey_date=2026-11-05")
    bus = bus_res.json()[0]
    bus_id = bus["bus_id"]

    # Get seats
    seats_res = client.get(f"/api/buses/{bus_id}/seats?journey_date=2026-11-05")
    avail = [s for s in seats_res.json()["seats"] if s["status"] == "available"]
    seat1 = avail[0]

    # Create Booking
    booking_payload = {
        "bus_id": bus_id,
        "journey_date": "2026-11-05",
        "boarding_point": bus["boarding_points"][0],
        "dropping_point": bus["dropping_points"][0],
        "passengers": [
            {
                "seat_id": seat1["id"],
                "name": "Kiran Varma",
                "age": 29,
                "gender": "M",
            }
        ],
    }

    create_res = client.post("/api/bookings", json=booking_payload, headers=headers)
    assert create_res.status_code == 201
    booking_data = create_res.json()
    assert booking_data["status"] == "PENDING_PAYMENT"
    assert booking_data["booking_reference"].startswith("ST-")
    booking_id = booking_data["id"]

    # Get single booking
    detail_res = client.get(f"/api/bookings/{booking_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["booking_reference"] == booking_data["booking_reference"]
    assert len(detail_res.json()["passengers"]) == 1

    # List bookings
    list_res = client.get("/api/bookings", headers=headers)
    assert list_res.status_code == 200
    assert any(b["id"] == booking_id for b in list_res.json())

    # Cancel booking
    cancel_res = client.post(f"/api/bookings/{booking_id}/cancel", headers=headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"
