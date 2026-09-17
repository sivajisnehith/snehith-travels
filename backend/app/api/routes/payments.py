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


