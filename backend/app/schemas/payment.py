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
    payment_id: int
    channel: str = Field(..., description="WHATSAPP or TELEGRAM")
    destination: str = Field(..., description="Phone number with country code or handle")


class PaymentDeliveryResponse(BaseModel):
    delivery_status: str  # SENT, NOT_CONFIGURED, FAILED
    channel: str
    destination: str
    payment_url: str
    booking_reference: str
    amount: float
    message: str


class WebhookResponse(BaseModel):
    status: str
    message: str
    payment_id: Optional[int] = None
    booking_reference: Optional[str] = None
