from sqlalchemy import text

from app.core.database import engine


def test_connection():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database()")
        )
        print("Connected to:", result.scalar())


if __name__ == "__main__":
    test_connection()