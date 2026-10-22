import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return default if raw is None or raw == "" else int(raw)


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"}

    CAFE_NAME = os.getenv("CAFE_NAME", "Rayan Cafe")
    CAFE_TAGLINE = os.getenv("CAFE_TAGLINE", "Coffee, tea, and breakfast in the quiet hours.")
    CAFE_ADDRESS = os.getenv("CAFE_ADDRESS", "48 Willow Lane, Mapleford")
    CAFE_PHONE = os.getenv("CAFE_PHONE", "+1 (555) 014-2280")
    CAFE_EMAIL = os.getenv("CAFE_EMAIL", "hello@rayancafe.example")
    CAFE_HOURS = os.getenv(
        "CAFE_HOURS",
        "Tue–Fri 7:00–15:00 · Sat–Sun 8:00–16:00 · Closed Monday",
    )

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "owner")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

    DB_ENGINE = os.getenv("DB_ENGINE", "postgres").strip().lower()
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "hearth_steam")
    DB_USER = os.getenv("DB_USER", "cafe_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

    UPLOAD_DIR = BASE_DIR / "static" / "uploads"
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}

    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_API_BASE = os.getenv("AI_API_BASE", "https://api.openai.com/v1").rstrip("/")
    AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
    CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "openai").strip().lower()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    @property
    def default_db_port(self) -> int:
        if self.DB_ENGINE in {"mysql", "mariadb"}:
            return 3306
        if self.DB_ENGINE in {"postgres", "postgresql"}:
            return 5432
        return 0

    def sqlalchemy_url(self) -> str:
        if self.DATABASE_URL:
            # psycopg 3 is the PostgreSQL driver installed by this project.
            # SQLAlchemy's bare postgresql:// URL otherwise selects psycopg2.
            if self.DATABASE_URL.startswith("postgres://"):
                return "postgresql+psycopg://" + self.DATABASE_URL[len("postgres://"):]
            if self.DATABASE_URL.startswith("postgresql://"):
                return "postgresql+psycopg://" + self.DATABASE_URL[len("postgresql://"):]
            return self.DATABASE_URL

        engine = self.DB_ENGINE
        if engine == "sqlite":
            return f"sqlite:///{BASE_DIR / 'cafe.db'}"

        port = _int("DB_PORT", self.default_db_port)
        password = self.DB_PASSWORD
        user = self.DB_USER
        host = self.DB_HOST
        name = self.DB_NAME

        if engine in {"mysql", "mariadb"}:
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
        if engine in {"postgres", "postgresql"}:
            return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"

        raise RuntimeError(
            "DB_ENGINE must be mysql, postgres, or sqlite. "
            f"Got: {engine!r}"
        )
