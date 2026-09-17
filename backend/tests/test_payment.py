import json
import hmac
import hashlib
from unittest.mock import MagicMock, patch
from app.core.config import settings
from app.services.delivery_service import PaymentLinkDeliveryService


def get_auth_token(client, email="demo@snehithtravels.com", password="DemoPassword123!"):
    res = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    return res.json()["access_token"]


def create_test_booking(client, token, journey_date="2026-11-10"):
    headers = {"Authorization": f"Bearer {token}"}
    bus = client.get(f"/api/buses/search?from=Hyderabad&to=Bangalore&journey_date={journey_date}").json()[0]
    seats = client.get(f"/api/buses/{bus['bus_id']}/seats?journey_date={journey_date}").json()["seats"]
    avail = [s for s in seats if s["status"] == "available"]
    seat = avail[0]

    booking = client.post(
        "/api/bookings",
        headers=headers,
        json={
            "bus_id": bus["bus_id"],
            "journey_date": journey_date,
            "boarding_point": bus["boarding_points"][0],
            "dropping_point": bus["dropping_points"][0],
            "passengers": [{"seat_id": seat["id"], "name": "Kavitha", "age": 28, "gender": "F"}],
        },
    ).json()
    return booking, seat, bus


def generate_webhook_signature(payload_bytes: bytes, secret: str = settings.RAZORPAY_WEBHOOK_SECRET) -> str:
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


# 1. Payment creation & 5. Razorpay Payment Link creation mocked
def test_payment_link_creation(client):
    token = get_auth_token(client)
    booking, seat, bus = create_test_booking(client, token, "2026-11-15")

    mock_rzp_response = {
        "id": "plink_test123456789",
        "short_url": "https://rzp.io/i/test_link_123",
        "status": "created",
        "amount": int(booking["total_amount"] * 100),
        "currency": "INR",
    }

    with patch("app.services.payment_service.get_razorpay_client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.payment_link.create.return_value = mock_rzp_response
        mock_client_factory.return_value = mock_client

        # Temporarily enable non-placeholder key
        with patch.object(settings, "RAZORPAY_KEY_ID", "rzp_test_real_key"):
            with patch.object(settings, "RAZORPAY_KEY_SECRET", "real_secret"):
                pay_res = client.post(
                    "/api/payments",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"booking_id": booking["id"]},
                )

                assert pay_res.status_code == 201
                data = pay_res.json()
                assert data["status"] == "PENDING"
                assert data["provider"] == "razorpay"
                assert data["provider_payment_link_id"] == "plink_test123456789"
                assert data["payment_url"] == "https://rzp.io/i/test_link_123"
                assert data["amount"] == booking["total_amount"]
                assert data["currency"] == "INR"

                # Verify SDK called with correct paise amount
                mock_client.payment_link.create.assert_called_once()
                call_args = mock_client.payment_link.create.call_args[0][0]
                assert call_args["amount"] == int(booking["total_amount"] * 100)
                assert call_args["reference_id"] == booking["booking_reference"]


# 2. Invalid booking
def test_payment_invalid_booking(client):
    token = get_auth_token(client)
    res = client.post(
        "/api/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"booking_id": 999999},
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


# 3. Unauthorized booking
def test_payment_unauthorized_booking(client):
    # User 1 registers and books
    client.post(
        "/api/auth/register",
        json={"name": "Owner User", "email": "owner@example.com", "password": "Password123!"},
    )
    token_owner = get_auth_token(client, "owner@example.com", "Password123!")
    booking, _, _ = create_test_booking(client, token_owner, "2026-11-16")

    # User 2 registers and tries to pay for User 1's booking
    client.post(
        "/api/auth/register",
        json={"name": "Hacker User", "email": "hacker@example.com", "password": "Password123!"},
    )
    token_attacker = get_auth_token(client, "hacker@example.com", "Password123!")

    res = client.post(
        "/api/payments",
        headers={"Authorization": f"Bearer {token_attacker}"},
        json={"booking_id": booking["id"]},
    )
    assert res.status_code == 403
    assert "not authorized" in res.json()["detail"].lower()


# 4. Correct backend amount & 6. Payment record persistence
def test_payment_backend_amount_and_persistence(client):
    token = get_auth_token(client)
    booking, seat, bus = create_test_booking(client, token, "2026-11-17")

    # Call /api/payments without any amount field (frontend amount not accepted)
    pay_res = client.post(
        "/api/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"booking_id": booking["id"]},
    )
    assert pay_res.status_code == 201
    payment = pay_res.json()
    assert payment["amount"] == booking["total_amount"]
    assert payment["currency"] == "INR"
    assert payment["booking_reference"] == booking["booking_reference"]
    assert payment["provider_payment_link_id"] is not None

    # Check persistence via GET /api/payments/{id}
    status_res = client.get(f"/api/payments/{payment['id']}")
    assert status_res.status_code == 200
    persisted = status_res.json()
    assert persisted["id"] == payment["id"]
    assert persisted["status"] == "PENDING"
    assert persisted["amount"] == booking["total_amount"]


# 7. Webhook signature validation
def test_webhook_signature_validation(client):
    body = json.dumps({"event": "payment_link.paid"}).encode("utf-8")

    # Invalid signature
    res_bad = client.post(
        "/api/payments/webhook/razorpay",
        content=body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": "invalid_sig_abc123"},
    )
    assert res_bad.status_code == 400
    assert "signature" in res_bad.json()["detail"].lower()

    # Valid signature
    valid_sig = generate_webhook_signature(body)
    res_good = client.post(
        "/api/payments/webhook/razorpay",
        content=body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": valid_sig},
    )
    assert res_good.status_code == 200


# 8. Successful webhook & 11. Payment status & 12. Booking confirmation & 13. Seat confirmation
def test_successful_webhook_and_confirmation(client):
    token = get_auth_token(client)
    booking, seat, bus = create_test_booking(client, token, "2026-11-18")

    # Initiate payment
    pay_res = client.post(
        "/api/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"booking_id": booking["id"]},
    ).json()
    payment_id = pay_res["id"]
    plink_id = pay_res["provider_payment_link_id"]

    # Construct Razorpay payment_link.paid event
    webhook_event = {
        "entity": "event",
        "event": "payment_link.paid",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": plink_id,
                    "reference_id": booking["booking_reference"],
                    "status": "paid",
                    "amount": int(booking["total_amount"] * 100),
                    "notes": {
                        "booking_id": str(booking["id"]),
                        "booking_reference": booking["booking_reference"],
                    },
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_test_rzp_987654",
                    "status": "captured",
                    "amount": int(booking["total_amount"] * 100),
                    "currency": "INR",
                }
            },
        },
    }

    raw_body = json.dumps(webhook_event).encode("utf-8")
    sig = generate_webhook_signature(raw_body)

    hook_res = client.post(
        "/api/payments/webhook/razorpay",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    assert hook_res.status_code == 200
    assert hook_res.json()["status"] == "SUCCESS"

    # 11. Check authoritative payment status endpoint
    payment_status = client.get(f"/api/payments/{payment_id}").json()
    assert payment_status["status"] == "PAID"
    assert payment_status["provider_payment_id"] == "pay_test_rzp_987654"

    # 12. Verify booking confirmation
    booking_status = client.get(
        f"/api/bookings/{booking['id']}",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert booking_status["status"] == "CONFIRMED"

    # 13. Verify seat is confirmed/booked on journey date
    seats_after = client.get(f"/api/buses/{bus['bus_id']}/seats?journey_date=2026-11-18").json()["seats"]
    target_seat = next(s for s in seats_after if s["id"] == seat["id"])
    assert target_seat["status"] == "booked"

    # Verify digital ticket is available
    ticket_res = client.get(f"/api/tickets/{booking['booking_reference']}")
    assert ticket_res.status_code == 200
    assert ticket_res.json()["status"] == "CONFIRMED"


# 9. Failed webhook
def test_failed_webhook(client):
    token = get_auth_token(client)
    booking, _, _ = create_test_booking(client, token, "2026-11-19")

    pay_res = client.post(
        "/api/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"booking_id": booking["id"]},
    ).json()

    webhook_event = {
        "event": "payment.failed",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": pay_res["provider_payment_link_id"],
                    "reference_id": booking["booking_reference"],
                }
            }
        },
    }
    raw_body = json.dumps(webhook_event).encode("utf-8")
    sig = generate_webhook_signature(raw_body)

    hook_res = client.post(
        "/api/payments/webhook/razorpay",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    assert hook_res.status_code == 200
    assert hook_res.json()["status"] == "FAILED"

    # Check local status
    pay_check = client.get(f"/api/payments/{pay_res['id']}").json()
    assert pay_check["status"] == "FAILED"


# 10. Duplicate webhook / Idempotency
def test_webhook_idempotency(client):
    token = get_auth_token(client)
    booking, _, _ = create_test_booking(client, token, "2026-11-21")

    pay_res = client.post(
        "/api/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"booking_id": booking["id"]},
    ).json()

    webhook_event = {
        "event": "payment_link.paid",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": pay_res["provider_payment_link_id"],
                    "reference_id": booking["booking_reference"],
                    "status": "paid",
                }
            },
            "payment": {"entity": {"id": "pay_id_1"}},
        },
    }
    raw_body = json.dumps(webhook_event).encode("utf-8")
    sig = generate_webhook_signature(raw_body)

    # First delivery
    res1 = client.post(
        "/api/payments/webhook/razorpay",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "SUCCESS"

    # Duplicate delivery (same event delivered again by Razorpay)
    res2 = client.post(
        "/api/payments/webhook/razorpay",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "ALREADY_PROCESSED"


# 14. Seat release after expired payment link
def test_seat_release_after_expired_payment(client):
    token = get_auth_token(client)
    booking, seat, bus = create_test_booking(client, token, "2026-11-22")

    pay_res = client.post(
        "/api/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"booking_id": booking["id"]},
    ).json()

    webhook_event = {
        "event": "payment_link.expired",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": pay_res["provider_payment_link_id"],
                    "reference_id": booking["booking_reference"],
                }
            }
        },
    }
    raw_body = json.dumps(webhook_event).encode("utf-8")
    sig = generate_webhook_signature(raw_body)

    res = client.post(
        "/api/payments/webhook/razorpay",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "EXPIRED"

    # Booking should be EXPIRED
    b_check = client.get(
        f"/api/bookings/{booking['id']}",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert b_check["status"] == "EXPIRED"

    # Seat should be back to available
    seats = client.get(f"/api/buses/{bus['bus_id']}/seats?journey_date=2026-11-22").json()["seats"]
    target = next(s for s in seats if s["id"] == seat["id"])
    assert target["status"] == "available"


# 15. Payment Link Delivery Service (Saarthi AI WhatsApp/Telegram abstraction)
def test_payment_link_delivery_service(client):
    token = get_auth_token(client)
    booking, _, _ = create_test_booking(client, token, "2026-11-23")
    pay_res = client.post(
        "/api/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"booking_id": booking["id"]},
    ).json()

    # Deliver via WhatsApp
    wa_res = client.post(
        "/api/payments/deliver-link",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "payment_id": pay_res["id"],
            "channel": "WHATSAPP",
            "destination": "+919876543210",
        },
    )
    assert wa_res.status_code == 200
    wa_data = wa_res.json()
    assert wa_data["channel"] == "WHATSAPP"
    assert wa_data["delivery_status"] in ["NOT_CONFIGURED", "SENT"]
    assert wa_data["payment_url"] == pay_res["payment_url"]

    # Deliver via Telegram
    tg_res = client.post(
        "/api/payments/deliver-link",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "payment_id": pay_res["id"],
            "channel": "TELEGRAM",
            "destination": "@traveler_user",
        },
    )
    assert tg_res.status_code == 200
    assert tg_res.json()["channel"] == "TELEGRAM"
    assert tg_res.json()["delivery_status"] in ["NOT_CONFIGURED", "SENT"]
