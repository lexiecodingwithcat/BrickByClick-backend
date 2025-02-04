from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)

    # province_id is a foreign key that references the id column of the provinces table
    province_id = Column(Integer, ForeignKey("provinces.id"), nullable=False)

    # through the relationship, we can access the province object from the city object
    province = relationship("Province", back_populates="cities")
