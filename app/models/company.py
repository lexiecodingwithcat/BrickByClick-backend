from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from app.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key= True, index = True, autoincrement= True)
    name = Column(String(50), nullable= False, unique= True)
    address = Column(String(100), nullable = False)
    postal_code = Column(String(7), nullable = False)
    phone_number = Column(Integer)
    city_id = Column(
        Integer,
        ForeignKey("cities.id"),
        nullable=False,
    )
    province_id = Column(
        Integer,
        ForeignKey("provinces.id"),
        nullable=False,
    )
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )