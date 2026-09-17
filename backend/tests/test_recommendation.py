def test_recommend_seats_deterministic(client):
    # Get a sleeper bus
    res = client.get("/api/buses/search?from=Hyderabad&to=Vijayawada&journey_date=2026-10-20&bus_type=Sleeper")
    assert res.status_code == 200
    buses = res.json()
    assert len(buses) > 0
    bus_id = buses[0]["bus_id"]

    # Request window + lower + front preferences
    pref_payload = {
        "journey_date": "2026-10-20",
        "window": True,
        "lower": True,
        "front": True,
        "cheapest": False,
        "limit": 3,
    }
    rec_res = client.post(f"/api/buses/{bus_id}/recommend-seats", json=pref_payload)
    assert rec_res.status_code == 200
    data = rec_res.json()
    recs = data["recommended_seats"]
    assert len(recs) <= 3
    assert len(recs) > 0

    top_seat = recs[0]
    assert "score" in top_seat
    assert "reasons" in top_seat
    assert "seat_number" in top_seat
    assert top_seat["score"] > 0
    # Top seat should fulfill window and lower
    assert "window" in top_seat["reasons"]
    assert "lower berth" in top_seat["reasons"]


def test_recommend_seats_with_budget(client):
    res = client.get("/api/buses/search?from=Hyderabad&to=Bangalore&journey_date=2026-10-20")
    assert res.status_code == 200
    bus_id = res.json()[0]["bus_id"]

    pref_payload = {
        "journey_date": "2026-10-20",
        "maximum_budget": 1500.0,
        "cheapest": True,
        "limit": 5,
    }
    rec_res = client.post(f"/api/buses/{bus_id}/recommend-seats", json=pref_payload)
    assert rec_res.status_code == 200
    data = rec_res.json()
    for item in data["recommended_seats"]:
        assert item["price"] <= 1500.0
