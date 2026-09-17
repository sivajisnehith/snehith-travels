from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(20), unique=True, nullable=False, index=True)  # e.g., "ST-8F4K92"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False, index=True)
    journey_date = Column(String(10), nullable=False, index=True)  # "YYYY-MM-DD"
    boarding_point = Column(String(100), nullable=False)
    dropping_point = Column(String(100), nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(
        String(30),
        default="CREATED",
        nullable=False,
        index=True
    )  # CREATED, PENDING_PAYMENT, PAYMENT_SUCCESS, CONFIRMED, CANCELLED, EXPIRED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship("User", back_populates="bookings")
    bus = relationship("Bus", back_populates="bookings")
    booking_seats = relationship("BookingSeat", back_populates="booking", cascade="all, delete-orphan")
    passengers = relationship("Passenger", back_populates="booking", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="booking", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_booking_bus_date", "bus_id", "journey_date", "status"),
    )
