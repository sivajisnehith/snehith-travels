from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False, index=True)
    operator = Column(String(100), nullable=False, default="Snehith Travels")
    bus_name = Column(String(100), nullable=False)
    bus_type = Column(String(50), nullable=False)  # "AC Sleeper", "Non-AC Sleeper", "AC Seater", "Semi-sleeper"
    is_ac = Column(Boolean, default=True, nullable=False)
    is_sleeper = Column(Boolean, default=False, nullable=False)
    departure_time = Column(String(10), nullable=False)  # "21:30"
    arrival_time = Column(String(10), nullable=False)    # "06:00"
    duration = Column(String(20), nullable=False)        # "8h 30m"
    starting_price = Column(Float, nullable=False)
    amenities = Column(JSON, default=list, nullable=False)  # ["WiFi", "Charging Port", "Blanket", "Water Bottle"]
    rating = Column(Float, default=4.5, nullable=False)
    total_seats = Column(Integer, default=30, nullable=False)
    boarding_points = Column(JSON, default=list, nullable=False)
    dropping_points = Column(JSON, default=list, nullable=False)

    route = relationship("Route", back_populates="buses")
    seats = relationship("Seat", back_populates="bus", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="bus")
