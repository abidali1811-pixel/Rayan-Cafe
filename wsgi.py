from app import create_app
from db import create_tables

app = create_app()
create_tables()
