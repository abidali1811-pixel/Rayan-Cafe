"""Create the first database-backed admin account for a fresh installation."""
import sys
from getpass import getpass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select
from werkzeug.security import generate_password_hash

from config import Config
from db import SessionLocal, create_tables, init_engine
from models import AdminUser


def main():
    init_engine(Config().sqlalchemy_url())
    create_tables()
    db = SessionLocal()
    try:
        if db.scalar(select(AdminUser.id).limit(1)):
            print("An admin account already exists.")
            return

        username = input("Admin username: ").strip()
        password = getpass("Password (at least 12 characters): ")
        confirmation = getpass("Confirm password: ")
        if not username or len(username) > 80:
            raise SystemExit("Username must be between 1 and 80 characters.")
        if len(password) < 12:
            raise SystemExit("Password must be at least 12 characters.")
        if password != confirmation:
            raise SystemExit("Passwords do not match.")

        db.add(AdminUser(username=username, password_hash=generate_password_hash(password)))
        db.commit()
        print("Initial admin account created.")
    finally:
        SessionLocal.remove()


if __name__ == "__main__":
    main()
