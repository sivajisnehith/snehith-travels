from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class SeatHold(Base):
    __tablename__ = "seat_holds"

    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False, index=True)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False, index=True)
    journey_date = Column(String(10), nullable=False, index=True)  # "YYYY-MM-DD"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    hold_token = Column(String(64), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, RELEASED, CONVERTED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    seat = relationship("Seat", back_populates="holds")

    __table_args__ = (
        Index("ix_active_seat_hold", "seat_id", "journey_date", "status"),
    )
