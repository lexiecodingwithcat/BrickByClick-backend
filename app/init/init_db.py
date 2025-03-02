from app.database import SessionLocal
from app.models.country import Country
from app.models.province import Province
from app.models.city import City
from app.models.user import User
from app.models.task import Task
from app.models.company import Company
from passlib.context import CryptContext
from sqlalchemy.exc import SQLAlchemyError
import os
from app.models.user import Role
from sqlalchemy import select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password = os.getenv("ADMIN_PASSWORD")
db = SessionLocal()

def initial_company():
    try:
        existing = db.query(Company).filter(Company.id ==1).first()
        if not existing:
            # create the default company
            company = Company(
                id=1,
                name = 'Raynow Homes',
                address = '14 Ave NW',
                postal_code="T2E 1B7",
                city_id = 1,
                province_id = 2,
                phone_number= '403-891-5668'

            )
            db.add(company)
            db.commit()
    finally:
        db.close()

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
                is_active = True,
                company_id = 1,
                role = Role.ADMIN
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


# initialize Canadian provinces
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


# initialize canadian cities by province
def initialize_canadian_cities():
    try:
        # city data by province
        province_cities = {
            "ON": [
                "Toronto",
                "Ottawa",
                "Mississauga",
                "Hamilton",
                "London",
                "Markham",
                "Vaughan",
                "Kitchener",
                "Brampton",
                "Windsor",
                "Richmond Hill",
                "Oakville",
                "Burlington",
                "Greater Sudbury",
                "Oshawa",
                "Barrie",
            ],
            "QC": [
                "Montreal",
                "Quebec City",
                "Laval",
                "Gatineau",
                "Longueuil",
                "Sherbrooke",
                "Saguenay",
                "Levis",
                "Trois-Rivieres",
                "Terrebonne",
                "Saint-Jean-sur-Richelieu",
                "Repentigny",
                "Brossard",
                "Drummondville",
            ],
            "BC": [
                "Vancouver",
                "Victoria",
                "Surrey",
                "Burnaby",
                "Richmond",
                "Kelowna",
                "Langley",
                "Coquitlam",
                "Abbotsford",
                "Kamloops",
                "Nanaimo",
                "Chilliwack",
                "Prince George",
                "Vernon",
                "Penticton",
                "Campbell River",
                "Courtenay",
            ],
            "AB": [
                "Calgary",
                "Edmonton",
                "Red Deer",
                "Lethbridge",
                "Airdrie",
                "St. Albert",
                "Medicine Hat",
                "Grande Prairie",
                "Fort McMurray",
                "Leduc",
                "Camrose",
                "Spruce Grove",
                "Banff",
                "Jasper",
                "Canmore",
                "Lloydminster",
                "Brooks",
                "Cold Lake",
            ],
            "MB": [
                "Winnipeg",
                "Brandon",
                "Steinbach",
                "Thompson",
                "Portage la Prairie",
                "Selkirk",
                "Winkler",
                "Dauphin",
                "Morden",
                "Flin Flon",
                "Swan River",
                "The Pas",
            ],
            "SK": [
                "Saskatoon",
                "Regina",
                "Prince Albert",
                "Moose Jaw",
                "Swift Current",
                "North Battleford",
                "Yorkton",
                "Estevan",
                "Weyburn",
                "Martensville",
                "Warman",
                "Meadow Lake",
            ],
            "NS": [
                "Halifax",
                "Sydney",
                "Dartmouth",
                "Truro",
                "New Glasgow",
                "Kentville",
                "Amherst",
            ],
            "NB": [
                "Saint John",
                "Moncton",
                "Fredericton",
                "Dieppe",
                "Miramichi",
                "Edmundston",
                "Campbellton",
            ],
            "NL": [
                "St. John's",
                "Conception Bay South",
                "Mount Pearl",
                "Paradise",
                "Corner Brook",
                "Grand Falls-Windsor",
                "Gander",
                "Happy Valley-Goose Bay",
                "Labrador City",
            ],
            "PE": [
                "Charlottetown",
                "Summerside",
                "Stratford",
                "Cornwall",
                "Montague",
                "Kensington",
            ],
            "NT": [
                "Yellowknife",
                "Hay River",
                "Inuvik",
                "Fort Smith",
                "Norman Wells",
                "Behchoko",
            ],
            "YT": [
                "Whitehorse",
                "Dawson City",
                "Watson Lake",
                "Haines Junction",
                "Carmacks",
            ],
            "NU": [
                "Iqaluit",
                "Rankin Inlet",
                "Arviat",
                "Cambridge Bay",
                "Baker Lake",
                "Pond Inlet",
            ],
        }

        for province_code, cities in province_cities.items():
            # Get the province by code
            province = db.query(Province).filter(Province.code == province_code).first()

            if not province:
                print(f"Province with code {province_code} not found, skipping cities")
                continue

            # Add cities to the City table
            for city_name in cities:
                # Check if the city already exists
                existing = (
                    db.query(City)
                    .filter(City.name == city_name, City.province_id == province.id)
                    .first()
                )

                if not existing:
                    new_city = City(name=city_name, province_id=province.id)
                    db.add(new_city)
                    print(f"Added {city_name} to {province.name}")

        db.commit()
        print("Canadian cities initialized successfully")

    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error initializing cities: {str(e)}")
    except Exception as e:
        db.rollback()
        print(f"Unexpected error: {str(e)}")
    finally:
        db.close()


# initialize pre-defined tasks
def initialize_parent_tasks():
    try:
        predefined_tasks = [
    {
        "name": "Site Preparation and Excavation",
        "children": [
            {"name": "Survey and stake out property", "sort_order": 1},
            {"name": "Clear site (remove trees, debris)", "sort_order": 2},
        ]
    },
    {
        "name": "Foundation",
        "children": [
            {"name": "Set up formwork for footings", "sort_order": 1},
            {"name": "Pour concrete footings", "sort_order": 2},
        ]
    },
]
        for parent_data in predefined_tasks:
            exsiting = db.query(Task).filter(Task.name == parent_data["name"]).first()

            if not exsiting:
                parent_task = Task(
            company_id=1,
            name=parent_data["name"],
            sort_order=predefined_tasks.index(parent_data) + 1
        )
                db.add(parent_task)
            db.flush()  
     
            for child_data in parent_data["children"]:
                existing = db.query(Task).filter(Task.name == child_data["name"]).first()
                if not existing:
                    child_task = Task(
                company_id=1,
                parent_id=parent_task.id,  
                name=child_data["name"],
                sort_order=child_data["sort_order"]
            )
                    db.add(child_task)

        db.commit() 
        print("Predefined tasks initialized successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error initializing parent tasks: {str(e)}")
    finally:
        db.close()