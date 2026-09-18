import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Path, Header, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_optional_current_user, get_current_user
from app.models.user import User
from app.models.payment import Payment
from app.models.seat_hold import SeatHold
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    WebhookResponse,
    PaymentDeliveryRequest,
    PaymentDeliveryResponse,
    MockPaymentUpdate,
)
from app.services.payment_service import (
    create_payment_link,
    get_payment,
    process_razorpay_webhook,
)
from app.services.delivery_service import delivery_service

router = APIRouter(prefix="/payments", tags=["Payments & WhatsApp Dispatch"])


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=201,
    summary="Initiate Razorpay Payment",
    description="Creates a Payment record and Razorpay Order / Payment Link for a pending booking without requiring authentication.",
)
def initiate_payment(
    payment_in: PaymentCreate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a payment for a booking and generate a Razorpay checkout session or payment URL.
    Returns the hosted payment URL and local payment ID.
    Backend verifies booking, payable status, and amount.
    Unauthenticated guest access is permitted for all payment links.
    """
    return create_payment_link(db, payment_in.booking_id, user_id=None, is_admin=True)


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Check Payment Status",
    description="Returns the authoritative local payment status (PENDING, PAID, FAILED, EXPIRED, CANCELLED).",
)
def check_payment_status(
    payment_id: int = Path(..., description="Local Payment ID"),
    db: Session = Depends(get_db),
):
    """
    Returns the authoritative local payment status. Never trusts client claims.
    """
    return get_payment(db, payment_id)


@router.post(
    "/webhook",
    response_model=WebhookResponse,
    summary="Razorpay Webhook Handler",
    description="Authoritative Razorpay Webhook Endpoint. Verifies HMAC signature and confirms bookings.",
)
@router.post("/webhook/razorpay", response_model=WebhookResponse, include_in_schema=False)
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
):
    """
    Authoritative Razorpay Webhook Endpoint.
    Verifies the HMAC SHA256 signature using RAZORPAY_WEBHOOK_SECRET.
    Idempotently updates Payment to PAID / FAILED, confirms booking and seats.
    """
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        payload = {}

    return process_razorpay_webhook(db, payload, raw_body, x_razorpay_signature)


@router.post(
    "/deliver-link",
    response_model=PaymentDeliveryResponse,
    summary="Deliver Payment Link to Passenger via WhatsApp",
    description="""
    Dispatches a payment link directly to the passenger's WhatsApp number using Meta WhatsApp Cloud API.
    
    **How AI Agents & Admins Use This Endpoint:**
    - Provide either `booking_id` OR `payment_id`.
    - Provide `destination` as an Indian mobile number (e.g. `9876543210` or `+919876543210`).
    - The backend formats the destination, verifies or creates the payment link, and sends the message via Meta WhatsApp Graph API.
    """,
    response_description="Detailed delivery status, destination, and payment URL dispatched.",
)
def deliver_payment_link(
    delivery_in: PaymentDeliveryRequest,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Dedicated endpoint for Saarthi AI & Admin UI to dispatch payment links via
    Meta WhatsApp Cloud API or Telegram.
    """
    payment = None
    if delivery_in.payment_id:
        payment = get_payment(db, delivery_in.payment_id)
    elif delivery_in.booking_id:
        user_id = current_user.id if current_user else None
        is_admin = bool(current_user and current_user.role and current_user.role.name == "admin")
        payment = create_payment_link(db, delivery_in.booking_id, user_id=user_id, is_admin=is_admin)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'booking_id' or 'payment_id' must be provided.",
        )

    if not payment.payment_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No payment URL available for this payment.",
        )

    res = delivery_service.send_payment_link(
        channel=delivery_in.channel,
        destination=delivery_in.destination,
        payment_url=payment.payment_url,
        booking_reference=payment.booking_reference,
        amount=payment.amount,
    )
    return PaymentDeliveryResponse(**res)


@router.post(
    "/{payment_id}/mock-success",
    response_model=MockPaymentUpdate,
    summary="Simulate Payment Success (Sandbox)",
    description="Instantly marks a pending payment as successful, confirms booking, and releases seat holds for sandbox testing.",
)
def mock_payment_success(
    payment_id: int = Path(..., description="Payment ID to mark as paid"),
    db: Session = Depends(get_db),
):
    """Simulate a successful payment for instant sandbox testing."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID {payment_id} not found."
        )

    now = datetime.now(timezone.utc)
    payment.status = "PAID"
    payment.provider_payment_id = f"pay_mock_{uuid.uuid4().hex[:10]}"
    payment.updated_at = now

    booking = payment.booking
    if booking:
        booking.status = "CONFIRMED"
        booking.updated_at = now

        holds = (
            db.query(SeatHold)
            .filter(
                SeatHold.bus_id == booking.bus_id,
                SeatHold.journey_date == booking.journey_date,
                SeatHold.status == "ACTIVE",
            )
            .all()
        )
        booked_seat_ids = {bs.seat_id for bs in booking.booking_seats}
        for h in holds:
            if h.seat_id in booked_seat_ids:
                h.status = "CONVERTED"

    db.commit()
    db.refresh(payment)

    return MockPaymentUpdate(
        status=payment.status,
        message="Payment marked as successful via sandbox simulation.",
        booking_reference=booking.booking_reference if booking else "N/A",
        booking_status=booking.status if booking else "N/A",
    )


@router.post(
    "/{payment_id}/mock-failure",
    response_model=MockPaymentUpdate,
    summary="Simulate Payment Failure (Sandbox)",
    description="Marks a payment as failed for sandbox verification.",
)
def mock_payment_failure(
    payment_id: int = Path(..., description="Payment ID"),
    db: Session = Depends(get_db),
):
    """Simulate a failed payment for sandbox verification."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID {payment_id} not found."
        )

    now = datetime.now(timezone.utc)
    payment.status = "FAILED"
    payment.updated_at = now
    db.commit()
    db.refresh(payment)

    booking = payment.booking
    return MockPaymentUpdate(
        status="FAILED",
        message="Payment marked as failed via sandbox simulation.",
        booking_reference=booking.booking_reference if booking else "N/A",
        booking_status=booking.status if booking else "N/A",
    )
