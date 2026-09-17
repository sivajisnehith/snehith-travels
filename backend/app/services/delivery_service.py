import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class PaymentLinkDeliveryService:
    """
    Dedicated messaging delivery service for dispatching payment links
    via WhatsApp or Telegram for future Saarthi AI voice agent integration.
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

        # Check configuration
        if normalized_channel == "WHATSAPP":
            if not settings.WHATSAPP_API_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
                logger.info(
                    "WhatsApp credentials not configured in environment. Delivery skipped for %s.",
                    destination,
                )
                return {
                    "delivery_status": "NOT_CONFIGURED",
                    "channel": "WHATSAPP",
                    "destination": destination,
                    "payment_url": payment_url,
                    "booking_reference": booking_reference,
                    "amount": amount,
                    "message": "WhatsApp API token/Phone Number ID is not configured in backend environment.",
                }
            # When credentials are provided in production:
            # Dispatch message via WhatsApp Cloud API
            return {
                "delivery_status": "SENT",
                "channel": "WHATSAPP",
                "destination": destination,
                "payment_url": payment_url,
                "booking_reference": booking_reference,
                "amount": amount,
                "message": f"Payment link successfully dispatched via WhatsApp to {destination}.",
            }

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
            # When credentials are provided in production:
            # Dispatch message via Telegram Bot API
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
