from pathlib import Path

import pytest

from app import create_app
from config import Config
from db import SessionLocal, create_tables
from models import MenuItem
from seed_data import MENU_SEED


@pytest.fixture()
def app(tmp_path):
    cfg = Config()
    cfg.SECRET_KEY = "test-secret"
    cfg.DB_ENGINE = "sqlite"
    cfg.DATABASE_URL = f"sqlite:///{tmp_path / 'test.db'}"
    cfg.ADMIN_USERNAME = "owner"
    cfg.ADMIN_PASSWORD = "test-admin-pass"
    cfg.AI_API_KEY = ""
    cfg.UPLOAD_DIR = tmp_path / "uploads"
    cfg.UPLOAD_DIR.mkdir()
    application = create_app(cfg)
    application.config["TESTING"] = True
    create_tables()
    db = SessionLocal()
    for row in MENU_SEED:
        db.add(MenuItem(**row))
    db.commit()
    SessionLocal.remove()
    yield application
    SessionLocal.remove()


@pytest.fixture()
def client(app):
    return app.test_client()
