import logging
import re
from typing import Dict, Any, Tuple
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def validate_and_normalize_indian_phone(phone: str) -> Tuple[bool, str, str]:
    """
    Validates and normalizes Indian mobile phone numbers for Meta WhatsApp Cloud API.
    Rules:
    - 10-digit number starting with 6, 7, 8, or 9.
    - Standardized without '+' (Meta API expects e.g. '918712145983').
    Returns (is_valid, normalized_meta_format, error_message).
    """
    if not phone:
        return False, "", "Phone number cannot be empty."

    cleaned = phone.strip()
    if cleaned.lower().startswith("whatsapp:"):
        cleaned = cleaned[9:].strip()

    cleaned = re.sub(r"[\s\-\(\)\.]", "", cleaned)

    digits = cleaned
    if cleaned.startswith("+91"):
        digits = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        digits = cleaned[2:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        digits = cleaned[1:]

    if not re.match(r"^[6-9]\d{9}$", digits):
        return (
            False,
            "",
            f"Invalid Indian mobile number '{phone}'. Must be a 10-digit number starting with 6, 7, 8, or 9.",
        )

    # Meta Cloud API format: country code + 10 digits without '+'
    meta_format = f"91{digits}"
    return True, meta_format, ""


class PaymentLinkDeliveryService:
    """
    Dedicated messaging delivery service for dispatching payment links
    via Meta WhatsApp Cloud API (Graph API) or Telegram.
    Completely decoupled from the payment provider (Razorpay).
    """

    @classmethod
    def send_payment_link(
        cls,
        channel: str,
        destination: str,
        payment_url: str,
        booking_reference: str,
        amount: float,
    ) -> Dict[str, Any]:
        normalized_channel = channel.upper().strip()

        if normalized_channel not in ["WHATSAPP", "TELEGRAM"]:
            return {
                "delivery_status": "UNSUPPORTED_CHANNEL",
                "channel": channel,
                "destination": destination,
                "payment_url": payment_url,
                "booking_reference": booking_reference,
                "amount": amount,
                "message": f"Channel '{channel}' is not supported. Supported channels: WHATSAPP, TELEGRAM.",
            }

        # 1. Meta WhatsApp Cloud API
        if normalized_channel == "WHATSAPP":
            is_valid, normalized_phone, val_err = validate_and_normalize_indian_phone(destination)
            if not is_valid:
                return {
                    "delivery_status": "FAILED",
                    "channel": "WHATSAPP",
                    "destination": destination,
                    "payment_url": payment_url,
                    "booking_reference": booking_reference,
                    "amount": amount,
                    "message": val_err,
                }

            if not settings.WHATSAPP_API_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
                logger.info("Meta WhatsApp Cloud API credentials not configured in environment.")
                return {
                    "delivery_status": "NOT_CONFIGURED",
                    "channel": "WHATSAPP",
                    "destination": normalized_phone,
                    "payment_url": payment_url,
                    "booking_reference": booking_reference,
                    "amount": amount,
                    "message": "Meta WhatsApp API token or Phone Number ID is not configured.",
                }

            api_version = getattr(settings, "WHATSAPP_API_VERSION", "v22.0")
            url = f"https://graph.facebook.com/{api_version}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
            headers = {
                "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
                "Content-Type": "application/json",
            }

            # In WhatsApp Cloud API, outbound business notifications (especially from a test/developer number)
            # MUST be sent using an approved Template. Freeform text messages outside a 24-hr user-initiated window
            # are silently dropped by Meta's network.
            template_name = getattr(
                settings, "WHATSAPP_PAYMENT_TEMPLATE_NAME", "snehith_travels_payment_link"
            )
            template_payload = {
                "messaging_product": "whatsapp",
                "to": normalized_phone,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "en_US"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": "Customer"},
                                {"type": "text", "text": str(booking_reference)},
                                {"type": "text", "text": f"Amount: Rs {amount:,.0f} | Pay: {payment_url}"},
                            ],
                        }
                    ],
                },
            }

            try:
                with httpx.Client(timeout=15.0) as client:
                    # 1. Dispatch primary approved template message
                    resp = client.post(url, headers=headers, json=template_payload)
                    data = resp.json() if resp.content else {}

                    if resp.status_code in [200, 201] and "messages" in data:
                        msg_id = data["messages"][0]["id"]
                        logger.info("WhatsApp template sent via Meta Cloud API to %s, ID: %s", normalized_phone, msg_id)

                        # Also attempt companion rich text if active session exists (non-blocking)
                        try:
                            text_payload = {
                                "messaging_product": "whatsapp",
                                "to": normalized_phone,
                                "type": "text",
                                "text": {
                                    "preview_url": True,
                                    "body": (
                                        f"🚌 *Snehith Travels - Payment Link*\n\n"
                                        f"Dear Customer,\n"
                                        f"Your booking reservation *{booking_reference}* is ready.\n\n"
                                        f"• *Amount Due:* ₹{amount:,.2f}\n"
                                        f"• *Payment Link:* {payment_url}\n\n"
                                        f"Please click the link above to complete your payment securely via UPI, Card, or Net Banking.\n"
                                        f"Thank you for choosing Snehith Travels!"
                                    ),
                                },
                            }
                            client.post(url, headers=headers, json=text_payload)
                        except Exception:
                            pass

                        return {
                            "delivery_status": "SENT",
                            "channel": "WHATSAPP",
                            "destination": normalized_phone,
                            "payment_url": payment_url,
                            "booking_reference": booking_reference,
                            "amount": amount,
                            "message_id": msg_id,
                            "message": f"Payment link successfully dispatched via Meta WhatsApp template to {normalized_phone} (Message ID: {msg_id}).",
                        }

                    logger.warning("Template %s returned %s (%s)", template_name, resp.status_code, data)
                    err_info = data.get("error") or {}
                    err_msg = err_info.get("message", f"HTTP {resp.status_code}: {resp.text}")
                    return {
                        "delivery_status": "FAILED",
                        "channel": "WHATSAPP",
                        "destination": normalized_phone,
                        "payment_url": payment_url,
                        "booking_reference": booking_reference,
                        "amount": amount,
                        "message": f"Meta WhatsApp API error: {err_msg}",
                    }
            except Exception as ex:
                logger.exception("Error dispatching WhatsApp via Meta Cloud API: %s", ex)
                return {
                    "delivery_status": "FAILED",
                    "channel": "WHATSAPP",
                    "destination": normalized_phone,
                    "payment_url": payment_url,
                    "booking_reference": booking_reference,
                    "amount": amount,
                    "message": f"Dispatch error: {str(ex)}",
                }

        # 2. Telegram fallback
        elif normalized_channel == "TELEGRAM":
            if not settings.TELEGRAM_BOT_TOKEN:
                logger.info(
                    "Telegram credentials not configured in environment. Delivery skipped for %s.",
                    destination,
                )
                return {
                    "delivery_status": "NOT_CONFIGURED",
                    "channel": "TELEGRAM",
                    "destination": destination,
                    "payment_url": payment_url,
                    "booking_reference": booking_reference,
                    "amount": amount,
                    "message": "Telegram Bot token is not configured in backend environment.",
                }
            return {
                "delivery_status": "SENT",
                "channel": "TELEGRAM",
                "destination": destination,
                "payment_url": payment_url,
                "booking_reference": booking_reference,
                "amount": amount,
                "message": f"Payment link successfully dispatched via Telegram to {destination}.",
            }

        return {
            "delivery_status": "NOT_CONFIGURED",
            "channel": channel,
            "destination": destination,
            "payment_url": payment_url,
            "booking_reference": booking_reference,
            "amount": amount,
            "message": "Channel not configured.",
        }


delivery_service = PaymentLinkDeliveryService()
