# Rayan Cafe

A small café website for coffee, tea, and breakfast: public menu, gallery, table booking, contact details, an owner admin area, and a menu-grounded chatbot.

This is an informational site with booking requests. It is not an ordering or payment platform.

## Project structure

```
Rayan-Cafe/
├── app.py                 # Flask app: public pages, admin, chat API
├── wsgi.py                # Production entry (gunicorn)
├── config.py              # Settings loaded from .env
├── db.py                  # SQLAlchemy engine (MySQL / PostgreSQL / sqlite tests)
├── models.py              # Menu, gallery, bookings
├── chatbot.py             # AI assistant grounded in the rate list
├── seed_data.py           # Placeholder café menu and gallery captions
├── requirements.txt
├── .env.example
├── schema/
│   ├── mysql.sql
│   └── postgres.sql
├── scripts/
│   ├── init_db.py         # Create tables + seed
│   └── make_placeholders.py
├── static/css/style.css
├── static/js/chat.js
├── static/uploads/        # Gallery files (paths stored in the database)
├── templates/             # Home, menu, gallery, booking, contact, admin
└── tests/
    ├── test_booking.py
    └── test_chatbot.py
```

## Stack

- Python 3.11+ and Flask
- SQLAlchemy with **MySQL** (`pymysql`) or **PostgreSQL** (`psycopg`)
- Server-rendered HTML, a little CSS/JS
- OpenAI-compatible chat API (optional; offline answers still use database prices)

## Setup

### 1. Create a virtualenv and install dependencies

```bash
cd AI-power-fitness
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Create `.env`

```bash
copy .env.example .env
```

On macOS / Linux: `cp .env.example .env`

Edit `.env` and set at least:

- `FLASK_SECRET_KEY`
- `DB_ENGINE` (`mysql` or `postgres`)
- Database host, name, user, and password (or a full `DATABASE_URL`)
- `CHAT_PROVIDER=gemini`, `GEMINI_API_KEY`, and `GEMINI_MODEL` for Gemini replies; or set `CHAT_PROVIDER=openai` with `AI_API_KEY`, `AI_API_BASE`, and `AI_MODEL` for an OpenAI-compatible API

Admin accounts are stored in the database with hashed passwords. After initializing a fresh database, run `python scripts/create_admin.py` to create the first account. Signed-in admins can change their password and create additional admin users at `/admin/accounts`.

### 3. Create the database schema

**PostgreSQL** (`DB_ENGINE=postgres`, default port `5432`):

```bash
psql -U postgres -c "CREATE USER cafe_user WITH PASSWORD 'change-me';"
psql -U postgres -c "CREATE DATABASE hearth_steam OWNER cafe_user;"
psql -U cafe_user -d hearth_steam -f schema/postgres.sql
```

The `CREATE DATABASE` line is already in `schema/postgres.sql`; skip it if you created the database first, then run the `CREATE TABLE` statements.

**MySQL** (`DB_ENGINE=mysql`, default port `3306`):

```bash
mysql -u root -p < schema/mysql.sql
```

Then grant access to `cafe_user` if needed.

Tables can also be created by SQLAlchemy (step 4) if you prefer not to run the SQL files by hand. The SQL files are the canonical schema for each engine.

### 4. Seed the menu, gallery captions, and placeholder images

```bash
python scripts/init_db.py
```

Re-load the sample menu and gallery rows:

```bash
python scripts/init_db.py --force
```

Seed items include espresso, cappuccino, green tea, pancakes, and eggs and toast. Change them later in **Admin → Menu & prices**.

### 5. Create the first admin account

```bash
python scripts/create_admin.py
```

The script prompts for a username and password without storing either in `.env`.

### 6. Run the site

```bash
python app.py
```

Or:

```bash
flask --app app:create_app run
```

Open http://127.0.0.1:5000

Admin: http://127.0.0.1:5000/admin/login

Production-style:

```bash
gunicorn wsgi:app
```

## Switching engines

Set `DB_ENGINE=mysql` or `DB_ENGINE=postgres`. If `DATABASE_URL` is empty, the app builds a URL from `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`.

Examples:

```
DATABASE_URL=postgresql+psycopg://cafe_user:change-me@localhost:5432/hearth_steam
DATABASE_URL=mysql+pymysql://cafe_user:change-me@localhost:3306/hearth_steam
```

`DB_ENGINE=sqlite` is supported for automated tests only.

## Chatbot

The widget posts to `/api/chat`. Set `CHAT_PROVIDER=gemini` to use Gemini, or `CHAT_PROVIDER=openai` for an OpenAI-compatible API. The server loads the current menu from the database and puts the exact rate list in the model prompt. If the selected AI key is missing or the API fails, a small offline helper still answers with those same prices. Unrelated questions are declined. Reservation questions are pointed at the booking form.

## Tests

```bash
pytest
```

Tests use a temporary SQLite database. They cover booking submission and chatbot price grounding.

## Admin

After login the owner can:

- Add, edit, and remove menu items and prices
- Upload, replace, caption, and delete gallery images (files in `static/uploads`, rows in `gallery_images`)
- View booking requests and set status to pending, confirmed, or cancelled
