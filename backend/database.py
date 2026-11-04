
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL

# Load the .env file from the same folder
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH, override=True)

# Read credentials
username = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
host = os.getenv("POSTGRES_HOST", "localhost")
port = int(os.getenv("POSTGRES_PORT", "5432"))
database_name = os.getenv("POSTGRES_DB", "ecommerce_analytics")

# Check environment variables
print("Loaded .env:", ENV_PATH.exists())
print("Username:", username)
print("Password loaded:", password is not None)

# Create database URL safely
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=username,
    password=password,
    host=host,
    port=port,
    database=database_name
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

print("Database host:", engine.url.host)
