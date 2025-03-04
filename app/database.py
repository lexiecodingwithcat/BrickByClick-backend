from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.settings import settings

# define engine, session and base
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# declarative_base is a factory function that constructs a base class for declarative class definitions
# which enable us to define our database tables as classes (ORM)
Base = declarative_base()

# connect to database


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
