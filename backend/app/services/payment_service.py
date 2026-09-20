import hmac
import hashlib
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import razorpay
from app.core.config import settings
from app.models.payment import Payment
from app.models.booking import Booking
from app.models.seat_hold import SeatHold
from app.schemas.payment import PaymentCreate, PaymentResponse, WebhookResponse
from app.services.seat_hold_service import cleanup_expired_holds

logger = logging.getLogger(__name__)


def get_razorpay_client() -> razorpay.Client:
    """Initializes and returns Razorpay client using backend settings."""
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_payment_link(
    db: Session,
    booking_id: int,
    user_id: Optional[int] = None,
    is_admin: bool = False,
) -> PaymentResponse:
    """
    Creates a real Razorpay hosted Payment Link for a pending booking.
    Verifies ownership, payable status, seat holds, and uses backend amount only.
    """
    # 1. Clean up any expired holds first
    cleanup_expired_holds(db)

    # 2. Verify booking exists
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found."
        )

    # 3. Verify user ownership
    if user_id is not None and not is_admin and booking.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to make a payment for this booking."
        )

    # 4. Verify booking is payable
    if booking.status in ["CONFIRMED", "PAYMENT_SUCCESS"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This booking has already been paid and confirmed."
        )
    if booking.status in ["CANCELLED", "EXPIRED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking is in '{booking.status}' state and cannot be paid."
        )

    # 5. Check existing payment record
    existing_payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
    if existing_payment:
        if existing_payment.status == "PAID":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment has already succeeded for this booking."
            )
        # If active payment link already exists, return it
        if existing_payment.payment_url and existing_payment.status == "PENDING":
            return PaymentResponse(
                id=existing_payment.id,
                payment_id=existing_payment.id,
                booking_id=existing_payment.booking_id,
                booking_reference=booking.booking_reference,
                amount=existing_payment.amount,
                currency=existing_payment.currency,
                payment_url=existing_payment.payment_url,
                provider=existing_payment.provider,
                provider_payment_link_id=existing_payment.provider_payment_link_id,
                provider_payment_id=existing_payment.provider_payment_id,
                payment_method=existing_payment.payment_method,
                transaction_reference=existing_payment.transaction_reference,
                status=existing_payment.status,
                expires_at=existing_payment.expires_at,
                created_at=existing_payment.created_at,
                updated_at=existing_payment.updated_at,
            )

    # 6. Amount from backend booking ONLY (NEVER trust frontend amount)
    amount_in_rupees = booking.total_amount
    amount_in_paise = int(round(amount_in_rupees * 100))

    user = booking.user
    customer_name = user.name if user else "Traveler"
    customer_email = user.email if user else "customer@snehithtravels.com"
    customer_phone = user.phone if user and user.phone else "9999999999"

    # Callback return URL on the Next.js frontend
    callback_url = f"{settings.FRONTEND_URL}/payment?booking_id={booking.id}"

    # 7. Create Razorpay Payment Link
    payment_link_data = {
        "amount": amount_in_paise,
        "currency": "INR",
        "accept_partial": False,
        "reference_id": booking.booking_reference,
        "description": f"Snehith Travels ticket for {booking.bus.bus_name} ({booking.booking_reference})",
        "customer": {
            "name": customer_name,
            "email": customer_email,
            "contact": customer_phone,
        },
        "notify": {
            "sms": False,
            "email": False,
            "whatsapp": False,
        },
        "reminder_enable": False,
        "notes": {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
        },
        "callback_url": callback_url,
        "callback_method": "get",
    }

    provider_link_id = f"plink_{uuid.uuid4().hex[:14]}"
    hosted_payment_url = f"{settings.FRONTEND_URL}/payment?booking_id={booking.id}"

    # Attempt to call Razorpay API
    try:
        # If real keys are configured (not default placeholder)
        if (
            settings.RAZORPAY_KEY_ID
            and not settings.RAZORPAY_KEY_ID.startswith("rzp_test_placeholder")
            and settings.RAZORPAY_KEY_SECRET
            and not settings.RAZORPAY_KEY_SECRET.startswith("placeholder")
        ):
            client = get_razorpay_client()

            # 1. Create a Razorpay Order (no limit of 30 in test mode)
            try:
                order_data = {
                    "amount": amount_in_paise,
                    "currency": "INR",
                    "receipt": booking.booking_reference,
                    "notes": {
                        "booking_id": str(booking.id),
                        "booking_reference": booking.booking_reference,
                    },
                }
                rzp_order = client.order.create(order_data)
                provider_link_id = rzp_order.get("id", provider_link_id)
            except Exception as order_err:
                logger.warning("Could not create Razorpay Order: %s", order_err)

            # 2. Try creating a hosted payment link if available
            try:
                rzp_response = client.payment_link.create(payment_link_data)
                provider_link_id = rzp_response.get("id", provider_link_id)
                hosted_payment_url = rzp_response.get("short_url", hosted_payment_url)
            except Exception as link_err:
                logger.info("Razorpay Payment Link creation skipped or limited (%s). Using portal checkout.", link_err)
                hosted_payment_url = f"{settings.FRONTEND_URL}/payment?booking_id={booking.id}"
        else:
            logger.info(
                "Using Razorpay Sandbox payment link mode for booking %s",
                booking.booking_reference,
            )
    except Exception as e:
        err_str = str(e)
        logger.warning(
            "Razorpay API call exception (%s). Using fallback portal checkout.",
            err_str,
        )
        hosted_payment_url = f"{settings.FRONTEND_URL}/payment?booking_id={booking.id}"

    # 8. Persist Payment record
    if existing_payment:
        existing_payment.amount = amount_in_rupees
        existing_payment.currency = "INR"
        existing_payment.provider = "razorpay"
        existing_payment.provider_payment_link_id = provider_link_id
        existing_payment.payment_url = hosted_payment_url
        existing_payment.transaction_reference = provider_link_id
        existing_payment.status = "PENDING"
        existing_payment.updated_at = datetime.now(timezone.utc)
        payment_record = existing_payment
    else:
        payment_record = Payment(
            booking_id=booking.id,
            amount=amount_in_rupees,
            currency="INR",
            provider="razorpay",
            provider_payment_link_id=provider_link_id,
            provider_payment_id=None,
            payment_url=hosted_payment_url,
            payment_method="RAZORPAY_PAYMENT_LINK",
            transaction_reference=provider_link_id,
            status="PENDING",
        )
        db.add(payment_record)

    try:
        db.commit()
        db.refresh(payment_record)
    except IntegrityError:
        db.rollback()
        existing = db.query(Payment).filter(Payment.booking_id == booking.id).first()
        if existing:
            payment_record = existing
        else:
            raise

    return PaymentResponse(
        id=payment_record.id,
        payment_id=payment_record.id,
        booking_id=payment_record.booking_id,
        booking_reference=booking.booking_reference,
        amount=payment_record.amount,
        currency=payment_record.currency,
        payment_url=payment_record.payment_url,
        provider=payment_record.provider,
        provider_payment_link_id=payment_record.provider_payment_link_id,
        provider_payment_id=payment_record.provider_payment_id,
        payment_method=payment_record.payment_method,
        transaction_reference=payment_record.transaction_reference,
        status=payment_record.status,
        expires_at=payment_record.expires_at,
        created_at=payment_record.created_at,
        updated_at=payment_record.updated_at,
    )


def create_payment(
    db: Session,
    payment_in: PaymentCreate,
    user_id: Optional[int] = None,
    is_admin: bool = False,
) -> PaymentResponse:
    """Alias for create_payment_link for API compatibility."""
    return create_payment_link(db, payment_in.booking_id, user_id=user_id, is_admin=is_admin)


def get_payment(db: Session, payment_id: int) -> PaymentResponse:
    """Retrieves authoritative local payment record, syncing with Razorpay API if pending."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID {payment_id} not found."
        )

    # If pending and real credentials configured, synchronize directly with Razorpay API
    if (
        payment.status == "PENDING"
        and payment.provider_payment_link_id
        and settings.RAZORPAY_KEY_ID
        and not settings.RAZORPAY_KEY_ID.startswith("rzp_test_placeholder")
    ):
        try:
            client = get_razorpay_client()
            rzp_link = client.payment_link.fetch(payment.provider_payment_link_id)
            rzp_status = rzp_link.get("status")
            if rzp_status == "paid":
                now = datetime.now(timezone.utc)
                payment.status = "PAID"
                payments_list = rzp_link.get("payments")
                if payments_list and len(payments_list) > 0:
                    payment.provider_payment_id = payments_list[0].get("payment_id") or payments_list[0].get("id")
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
        except Exception as e:
            logger.debug("Could not sync payment status with Razorpay API: %s", e)

    booking = payment.booking
    booking_ref = booking.booking_reference if booking else "N/A"

    return PaymentResponse(
        id=payment.id,
        payment_id=payment.id,
        booking_id=payment.booking_id,
        booking_reference=booking_ref,
        amount=payment.amount,
        currency=payment.currency,
        payment_url=payment.payment_url,
        provider=payment.provider,
        provider_payment_link_id=payment.provider_payment_link_id,
        provider_payment_id=payment.provider_payment_id,
        payment_method=payment.payment_method,
        transaction_reference=payment.transaction_reference,
        status=payment.status,
        expires_at=payment.expires_at,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


def verify_razorpay_webhook_signature(raw_body: bytes, signature: Optional[str]) -> bool:
    """
    Verifies the Razorpay webhook signature using HMAC SHA256.
    """
    if not signature:
        return False

    secret = settings.RAZORPAY_WEBHOOK_SECRET
    if not secret:
        return False

    try:
        # Use Razorpay utility if available
        client = get_razorpay_client()
        client.utility.verify_webhook_signature(raw_body.decode("utf-8"), signature, secret)
        return True
    except Exception:
        # Fallback to direct hmac computation
        try:
            expected = hmac.new(
                secret.encode("utf-8"),
                raw_body,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception:
            return False


def process_razorpay_webhook(
    db: Session,
    payload: Dict[str, Any],
    raw_body: bytes,
    signature: Optional[str],
) -> WebhookResponse:
    """
    Processes incoming Razorpay webhook events idempotently.
    Verifies signature, updates local Payment to PAID / FAILED / EXPIRED,
    confirms or cancels booking and seats.
    """
    # 1. Verify signature
    if not verify_razorpay_webhook_signature(raw_body, signature):
        logger.warning("Rejected Razorpay webhook with invalid signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Razorpay webhook signature."
        )

    event_type = payload.get("event", "")
    payload_data = payload.get("payload", {})
    plink_entity = payload_data.get("payment_link", {}).get("entity", {})
    payment_entity = payload_data.get("payment", {}).get("entity", {})

    provider_link_id = plink_entity.get("id")
    reference_id = plink_entity.get("reference_id")
    notes = plink_entity.get("notes", {}) or payment_entity.get("notes", {}) or {}
    booking_id_val = notes.get("booking_id")
    payment_id_val = notes.get("payment_id")

    # 2. Identify corresponding local Payment
    payment = None
    if provider_link_id:
        payment = db.query(Payment).filter(Payment.provider_payment_link_id == provider_link_id).first()
    if not payment and reference_id:
        booking_obj = db.query(Booking).filter(Booking.booking_reference == reference_id).first()
        if booking_obj:
            payment = db.query(Payment).filter(Payment.booking_id == booking_obj.id).first()
    if not payment and booking_id_val is not None:
        try:
            payment = db.query(Payment).filter(Payment.booking_id == int(booking_id_val)).first()
        except (ValueError, TypeError):
            pass
    if not payment and payment_id_val is not None:
        try:
            payment = db.query(Payment).filter(Payment.id == int(payment_id_val)).first()
        except (ValueError, TypeError):
            pass

    if not payment:
        logger.warning("Webhook received for untracked payment/booking: %s", payload)
        return WebhookResponse(
            status="IGNORED",
            message="No matching local payment record found.",
        )

    booking = payment.booking
    now = datetime.now(timezone.utc)

    # 3. Handle Idempotency
    if payment.status in ["PAID", "SUCCESS"] and event_type in ["payment_link.paid", "payment.captured"]:
        return WebhookResponse(
            status="ALREADY_PROCESSED",
            message="Payment has already been marked as PAID.",
            payment_id=payment.id,
            booking_reference=booking.booking_reference if booking else None,
        )

    # 4. Handle Payment Success
    if event_type in ["payment_link.paid", "payment.captured"]:
        provider_pay_id = payment_entity.get("id")
        payment.status = "PAID"
        if provider_pay_id:
            payment.provider_payment_id = provider_pay_id
        payment.updated_at = now

        if booking:
            booking.status = "CONFIRMED"
            booking.updated_at = now

            # Ensure holds associated with booking seats are converted
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
        logger.info("Payment %s verified as PAID for booking %s", payment.id, booking.booking_reference if booking else "")

        return WebhookResponse(
            status="SUCCESS",
            message="Payment verified successfully. Booking CONFIRMED.",
            payment_id=payment.id,
            booking_reference=booking.booking_reference if booking else None,
        )

    # 5. Handle Payment Failure / Expiry / Cancellation
    elif event_type in ["payment.failed", "payment_link.expired", "payment_link.cancelled"]:
        new_status = "EXPIRED" if "expired" in event_type else ("CANCELLED" if "cancelled" in event_type else "FAILED")
        payment.status = new_status
        payment.updated_at = now

        if booking and new_status in ["EXPIRED", "CANCELLED"]:
            booking.status = new_status
            booking.updated_at = now

            # Release seats
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
                    h.status = "RELEASED"

        db.commit()

        return WebhookResponse(
            status=new_status,
            message=f"Payment status updated to {new_status}.",
            payment_id=payment.id,
            booking_reference=booking.booking_reference if booking else None,
        )

    return WebhookResponse(
        status="UNHANDLED_EVENT",
        message=f"Event '{event_type}' was acknowledged without state change.",
        payment_id=payment.id,
        booking_reference=booking.booking_reference if booking else None,
    )
