from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class PaymentCreate(BaseModel):
    booking_id: int
    payment_method: str = Field(default="RAZORPAY_PAYMENT_LINK", description="Payment provider/method")


class PaymentResponse(BaseModel):
    id: int
    payment_id: Optional[int] = None
    booking_id: int
    booking_reference: str
    amount: float
    currency: str = "INR"
    payment_url: Optional[str] = None
    provider: str = "razorpay"
    provider_payment_link_id: Optional[str] = None
    provider_payment_id: Optional[str] = None
    payment_method: str = "RAZORPAY_PAYMENT_LINK"
    transaction_reference: str
    status: str  # PENDING, PAID, FAILED, EXPIRED, CANCELLED
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @model_validator(mode="after")
    def populate_payment_id(self):
        if self.payment_id is None:
            self.payment_id = self.id
        return self

    model_config = {"from_attributes": True}


class MockPaymentUpdate(BaseModel):
    status: str
    message: str
    booking_reference: str
    booking_status: str


class PaymentDeliveryRequest(BaseModel):
    booking_id: Optional[int] = Field(None, description="Booking ID to deliver payment link for (optional if payment_id provided)")
    payment_id: Optional[int] = Field(None, description="Payment ID to deliver payment link for (optional if booking_id provided)")
    channel: str = Field(default="WHATSAPP", description="Delivery channel: 'WHATSAPP' (Meta Cloud API) or 'TELEGRAM'")
    destination: str = Field(..., description="Recipient phone number (e.g. 10-digit Indian mobile 9876543210 or 919876543210)")


class PaymentDeliveryResponse(BaseModel):
    delivery_status: str = Field(..., description="Status: 'SENT', 'NOT_CONFIGURED', or 'FAILED'")
    channel: str = Field(..., description="Messaging channel utilized ('WHATSAPP' or 'TELEGRAM')")
    destination: str = Field(..., description="Normalized destination phone number")
    payment_url: str = Field(..., description="Hosted Razorpay or portal payment URL sent to recipient")
    booking_reference: str = Field(..., description="Unique booking reservation reference")
    amount: float = Field(..., description="Total payable amount in INR")
    message: str = Field(..., description="Human and AI-readable confirmation or status detail")
    message_id: Optional[str] = Field(None, description="Meta WhatsApp message ID (wamid) if available")


class WebhookResponse(BaseModel):
    status: str
    message: str
    payment_id: Optional[int] = None
    booking_reference: Optional[str] = None
