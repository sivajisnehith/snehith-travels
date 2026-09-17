def test_double_booking_prevention(client):
    # Register user 1
    u1_reg = client.post(
        "/api/auth/register",
        json={"name": "User One", "email": "user1@example.com", "password": "Password123!"},
    )
    token1 = client.post(
        "/api/auth/login",
        json={"email": "user1@example.com", "password": "Password123!"},
    ).json()["access_token"]

    # Register user 2
    u2_reg = client.post(
        "/api/auth/register",
        json={"name": "User Two", "email": "user2@example.com", "password": "Password123!"},
    )
    token2 = client.post(
        "/api/auth/login",
        json={"email": "user2@example.com", "password": "Password123!"},
    ).json()["access_token"]

    h1 = {"Authorization": f"Bearer {token1}"}
    h2 = {"Authorization": f"Bearer {token2}"}

    # Find bus & seat
    bus = client.get("/api/buses/search?from=Hyderabad&to=Vijayawada&journey_date=2026-11-20").json()[0]
    bus_id = bus["bus_id"]
    seats = client.get(f"/api/buses/{bus_id}/seats?journey_date=2026-11-20").json()["seats"]
    seat_to_compete = [s for s in seats if s["status"] == "available"][0]

    # User 1 successfully holds or books the seat
    b1_res = client.post(
        "/api/bookings",
        headers=h1,
        json={
            "bus_id": bus_id,
            "journey_date": "2026-11-20",
            "boarding_point": bus["boarding_points"][0],
            "dropping_point": bus["dropping_points"][0],
            "passengers": [{"seat_id": seat_to_compete["id"], "name": "User 1", "age": 25, "gender": "M"}],
        },
    )
    assert b1_res.status_code == 201

    # User 2 tries to hold or book the EXACT same seat on the same journey date -> should be rejected with 409
    hold_attempt = client.post(
        "/api/seats/hold",
        headers=h2,
        json={
            "bus_id": bus_id,
            "journey_date": "2026-11-20",
            "seat_ids": [seat_to_compete["id"]],
        },
    )
    assert hold_attempt.status_code == 409

    book_attempt = client.post(
        "/api/bookings",
        headers=h2,
        json={
            "bus_id": bus_id,
            "journey_date": "2026-11-20",
            "boarding_point": bus["boarding_points"][0],
            "dropping_point": bus["dropping_points"][0],
            "passengers": [{"seat_id": seat_to_compete["id"], "name": "User 2", "age": 30, "gender": "F"}],
        },
    )
    assert book_attempt.status_code == 409
