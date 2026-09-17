from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    origin = Column(String(100), nullable=False, index=True)
    destination = Column(String(100), nullable=False, index=True)
    distance_km = Column(Float, nullable=False)
    estimated_duration_hours = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    buses = relationship("Bus", back_populates="route")
