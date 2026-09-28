# database.py
# ------------------------------------------------------------
# This file sets up the connection between our Python code and MySQL.
# Every other file that needs the database imports things from here.
# ------------------------------------------------------------

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Find the .env file in the project root folder (one level above "app").
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Reads values from the .env file.
    DATABASE_URL inside .env becomes settings.database_url here."""

    database_url: str

    # extra="ignore" means: don't crash if .env contains other variables
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")


settings = Settings()

# The engine is the actual connection to MySQL.
# pool_pre_ping=True checks a connection is alive before using it.
engine = create_engine(settings.database_url, pool_pre_ping=True)

# SessionLocal is a factory. Each call creates one database session
# (think of a session as one "conversation" with the database).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class of all our table models (Category, Book, ...).
Base = declarative_base()


def get_db():
    """FastAPI dependency: gives an endpoint a database session
    and always closes it afterwards, even if an error happens."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
