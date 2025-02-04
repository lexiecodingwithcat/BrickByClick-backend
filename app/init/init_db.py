from app.database import SessionLocal
from app.models.country import Country
from app.models.province import Province
from app.models.user import User
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password = os.getenv("ADMIN_PASSWORD")
db = SessionLocal()


# initialize admin user function
def initial_admin():
    try:
        # check if the admin user already exists
        existing = db.query(User).filter(User.email == "test@example.com").first()
        if not existing:
            # create a new admin user
            hashed_password = pwd_context.hash(password)
            admin = User(
                first_name="test",
                last_name="demo",
                email="test@example.com",
                password=hashed_password,
                is_admin=True,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


# initialize default countries function
def initialize_default_countries():
    try:
        # check if Canada and United States already exist
        existing = (
            db.query(Country)
            .filter(Country.name.in_(["Canada", "United States"]))
            .count()
        )
        if existing < 2:
            # add Canada and United States if they don't exist
            db.add_all([Country(name="Canada"), Country(name="United States")])
            db.commit()
    finally:
        db.close()


def initialize_canadian_province():
    try:
        # Get Canada from the Country table
        canada = db.query(Country).filter(Country.name == "Canada").first()
        if not canada:
            raise ValueError("Canada not found in Country table")

        # Canadian provinces data with name and code
        canadian_provinces = [
            {"name": "Ontario", "code": "ON"},
            {"name": "Quebec", "code": "QC"},
            {"name": "British Columbia", "code": "BC"},
            {"name": "Alberta", "code": "AB"},
            {"name": "Manitoba", "code": "MB"},
            {"name": "Saskatchewan", "code": "SK"},
            {"name": "Nova Scotia", "code": "NS"},
            {"name": "New Brunswick", "code": "NB"},
            {"name": "Newfoundland and Labrador", "code": "NL"},
            {"name": "Prince Edward Island", "code": "PE"},
            {"name": "Northwest Territories", "code": "NT"},
            {"name": "Yukon", "code": "YT"},
            {"name": "Nunavut", "code": "NU"},
        ]

        # Add provinces to the Province table
        for province_data in canadian_provinces:
            # Check if the province already exists
            existing = (
                db.query(Province)
                .filter(
                    (Province.name == province_data["name"])
                    | (Province.code == province_data["code"])
                )
                .first()
            )

            if not existing:
                new_province = Province(
                    name=province_data["name"],
                    code=province_data["code"],
                    country_id=canada.id,
                )
                db.add(new_province)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error initializing provinces: {str(e)}")
    finally:
        db.close()
