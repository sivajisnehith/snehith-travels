import json
from typing import Optional
from fastapi import APIRouter, Depends, Path, Header, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_optional_current_user, get_current_user
from app.models.user import User
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

router = APIRouter(prefix="/payments", tags=["Payments & Razorpay Checkout"])


@router.post("", response_model=PaymentResponse, status_code=201)
def initiate_payment(
    payment_in: PaymentCreate,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a payment for a booking and generate a Razorpay hosted Payment Link.
    Returns the hosted payment URL and local payment ID.
    Backend verifies booking, ownership, payable status, and amount.
    """
    user_id = current_user.id if current_user else None
    is_admin = bool(current_user and current_user.role and current_user.role.name == "admin")
    return create_payment_link(db, payment_in.booking_id, user_id=user_id, is_admin=is_admin)


@router.get("/{payment_id}", response_model=PaymentResponse)
def check_payment_status(
    payment_id: int = Path(..., description="Local Payment ID"),
    db: Session = Depends(get_db),
):
    """
    Returns the authoritative local payment status (PENDING, PAID, FAILED, EXPIRED, CANCELLED).
    Never trusts client claims.
    """
    return get_payment(db, payment_id)


@router.post("/webhook", response_model=WebhookResponse)
@router.post("/webhook/razorpay", response_model=WebhookResponse)
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


@router.post("/deliver-link", response_model=PaymentDeliveryResponse)
def deliver_payment_link(
    delivery_in: PaymentDeliveryRequest,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Dedicated endpoint for Saarthi AI to dispatch payment links via
    WhatsApp or Telegram. Completely decoupled from the payment gateway.
    """
    payment = get_payment(db, delivery_in.payment_id)
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


@router.post("/{payment_id}/mock-success", response_model=MockPaymentUpdate)
def mock_payment_success(
    payment_id: int = Path(..., description="Payment ID"),
    db: Session = Depends(get_db),
):
    """Simulate a successful payment for instant sandbox testing."""
    from datetime import datetime, timezone
    import uuid
    from app.models.payment import Payment
    from app.models.seat_hold import SeatHold

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


@router.post("/{payment_id}/mock-failure", response_model=MockPaymentUpdate)
def mock_payment_failure(
    payment_id: int = Path(..., description="Payment ID"),
    db: Session = Depends(get_db),
):
    """Simulate a failed payment for sandbox verification."""
    from datetime import datetime, timezone
    from app.models.payment import Payment

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
