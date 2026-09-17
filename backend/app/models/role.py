from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.session import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)  # "admin", "customer"
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role")
