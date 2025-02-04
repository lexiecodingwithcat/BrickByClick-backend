from sqlalchemy import Column, Integer, String
from app.database import Base
from sqlalchemy.orm import relationship


class Province(Base):
    __tablename__ = "provinces"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # name is the full name of the province, e.g. Alberta, British Columbia etc.
    name = Column(String(50), nullable=False, unique=True)
    # code is a unique identifier for each province，e.g. AB for Alberta, BC for British Columbia etc.
    code = Column(String(10), nullable=False, unique=True)

    cities = relationship("City", back_populates="province")
