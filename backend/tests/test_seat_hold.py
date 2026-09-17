def test_seat_hold_lifecycle(client):
    # Find bus and seats
    bus_res = client.get("/api/buses/search?from=Hyderabad&to=Vijayawada&journey_date=2026-11-01")
    bus_id = bus_res.json()[0]["bus_id"]
    seats_res = client.get(f"/api/buses/{bus_id}/seats?journey_date=2026-11-01")
    avail_seats = [s for s in seats_res.json()["seats"] if s["status"] == "available"]
    target_seat = avail_seats[0]

    # Hold the seat
    hold_payload = {
        "bus_id": bus_id,
        "journey_date": "2026-11-01",
        "seat_ids": [target_seat["id"]],
    }
    hold_res = client.post("/api/seats/hold", json=hold_payload)
    assert hold_res.status_code == 200
    hold_data = hold_res.json()
    assert "hold_token" in hold_data
    token = hold_data["hold_token"]

    # Seat status should now be "held"
    seats_after = client.get(f"/api/buses/{bus_id}/seats?journey_date=2026-11-01").json()["seats"]
    held_seat = next(s for s in seats_after if s["id"] == target_seat["id"])
    assert held_seat["status"] == "held"

    # Trying to hold the same seat again should return 409 Conflict
    conflict_res = client.post("/api/seats/hold", json=hold_payload)
    assert conflict_res.status_code == 409

    # Release the hold
    rel_res = client.request("DELETE", "/api/seats/hold", json={"hold_token": token})
    assert rel_res.status_code == 200
    assert rel_res.json()["success"] is True

    # Seat status should now be back to "available"
    seats_after_rel = client.get(f"/api/buses/{bus_id}/seats?journey_date=2026-11-01").json()["seats"]
    released_seat = next(s for s in seats_after_rel if s["id"] == target_seat["id"])
    assert released_seat["status"] == "available"
