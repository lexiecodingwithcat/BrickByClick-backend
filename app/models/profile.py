from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, func
from app.database import Base


# Profile model
class Profile(Base):
    __tablename__ = "profiles"

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        primary_key=True,
        index=True,
    )
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone_number = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(Integer, ForeignKey("cities.id"), nullable=True)
    province = Column(Integer, ForeignKey("provinces.id"), nullable=True)
    postal_code = Column(String(10), nullable=True)
    country = Column(Integer, ForeignKey("countries.id"), nullable=True, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
