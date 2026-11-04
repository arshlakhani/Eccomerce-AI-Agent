from database import engine
from sqlalchemy import text

def main():
    with engine.connect() as connection:
        count = connection.execute(
            text("SELECT COUNT(*) FROM online_retail")
        ).scalar_one()

    print("Database connected successfully!")
    print("Total records:", count)


if __name__ == "__main__":
    main()