from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False, index=True)
    seat_number = Column(String(10), nullable=False, index=True)
    row = Column(Integer, nullable=False)
    column = Column(Integer, nullable=False)
    seat_type = Column(String(20), nullable=False)  # "sleeper", "seater"
    window = Column(Boolean, default=False, nullable=False)
    aisle = Column(Boolean, default=False, nullable=False)
    upper_lower = Column(String(20), default="seater", nullable=False)  # "lower", "upper", "seater"
    front_rear = Column(String(20), default="middle", nullable=False)   # "front", "middle", "rear"
    base_price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    bus = relationship("Bus", back_populates="seats")
    booking_seats = relationship("BookingSeat", back_populates="seat")
    passengers = relationship("Passenger", back_populates="seat")
    holds = relationship("SeatHold", back_populates="seat", cascade="all, delete-orphan")
