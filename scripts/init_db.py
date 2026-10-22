"""Create tables and load seed menu + gallery captions."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import Config
from db import SessionLocal, create_tables, get_engine, init_engine
from models import GalleryImage, MenuItem
from seed_data import GALLERY_SEED, MENU_SEED
from make_placeholders import ensure_placeholders


def seed(force: bool = False):
    cfg = Config()
    init_engine(cfg.sqlalchemy_url())
    create_tables()
    ensure_placeholders(cfg.UPLOAD_DIR)
    db = SessionLocal()
    try:
        has_menu = db.query(MenuItem).first() is not None
        if not has_menu or force:
            if force:
                db.query(MenuItem).delete()
            for row in MENU_SEED:
                db.add(MenuItem(**row))

        if force:
            db.query(GalleryImage).delete()
        existing_gallery = {row.filename for row in db.query(GalleryImage.filename).all()}
        for row in GALLERY_SEED:
            if row["filename"] not in existing_gallery:
                db.add(GalleryImage(**row))
        db.commit()
        print(f"Ready. Database dialect={get_engine().dialect.name}")
    finally:
        SessionLocal.remove()


if __name__ == "__main__":
    seed(force="--force" in sys.argv)
