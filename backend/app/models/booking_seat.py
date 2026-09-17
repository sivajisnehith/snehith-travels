from sqlalchemy import Column, Integer, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class BookingSeat(Base):
    __tablename__ = "booking_seats"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False, index=True)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False, index=True)
    price_paid = Column(Float, nullable=False)

    booking = relationship("Booking", back_populates="booking_seats")
    seat = relationship("Seat", back_populates="booking_seats")

    __table_args__ = (
        Index("ix_booking_seat_unique", "booking_id", "seat_id", unique=True),
    )
