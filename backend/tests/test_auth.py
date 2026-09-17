def test_register_and_login(client):
    # Register new user
    reg_payload = {
        "name": "Ananya Sharma",
        "email": "ananya.sharma@example.com",
        "password": "Password123!",
        "phone": "9988776655",
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == "ananya.sharma@example.com"
    assert user_data["role"] == "customer"

    # Login
    login_payload = {
        "email": "ananya.sharma@example.com",
        "password": "Password123!",
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Profile (/me)
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["name"] == "Ananya Sharma"


def test_login_invalid_password(client):
    login_res = client.post(
        "/api/auth/login",
        json={"email": "demo@snehithtravels.com", "password": "WrongPassword!"},
    )
    assert login_res.status_code == 401


def test_auth_me_unauthorized(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
