from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), unique=True, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    provider = Column(String(50), default="razorpay", nullable=False, index=True)
    provider_payment_link_id = Column(String(100), nullable=True, index=True)  # e.g., plink_...
    provider_payment_id = Column(String(100), nullable=True, index=True)       # e.g., pay_...
    payment_url = Column(String(500), nullable=True)                           # hosted payment link URL
    payment_method = Column(String(50), default="RAZORPAY_PAYMENT_LINK", nullable=False)
    transaction_reference = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(
        String(30),
        default="PENDING",
        nullable=False,
        index=True
    )  # PENDING, PAID, FAILED, EXPIRED, CANCELLED (also supports SUCCESS for backward compatibility)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    booking = relationship("Booking", back_populates="payment")
