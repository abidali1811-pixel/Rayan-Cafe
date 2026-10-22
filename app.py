from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from pathlib import Path
from uuid import uuid4

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

from chatbot import answer_question
from config import Config
from db import SessionLocal, create_tables, init_engine
from models import AdminUser, Booking, GalleryImage, MenuItem

cfg = Config()


def create_app(config: Config | None = None) -> Flask:
    config = config or cfg
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
    app.config["UPLOAD_DIR"] = config.UPLOAD_DIR
    app.config["CAFE"] = config

    Path(config.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    init_engine(config.sqlalchemy_url())

    def cafe_context():
        return {
            "cafe": config,
            "logged_in": bool(session.get("admin_user_id")),
            "admin_username": session.get("admin_username", ""),
        }

    app.context_processor(cafe_context)

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("admin_user_id"):
                return redirect(url_for("admin_login", next=request.path))
            return view(*args, **kwargs)

        return wrapped

    def grouped_menu(db):
        items = db.scalars(
            select(MenuItem).order_by(MenuItem.category, MenuItem.sort_order, MenuItem.name)
        ).all()
        groups = {}
        for item in items:
            groups.setdefault(item.category, []).append(item)
        return groups

    @app.teardown_appcontext
    def shutdown_session(_exc=None):
        SessionLocal.remove()

    @app.get("/favicon.ico")
    def favicon():
        return redirect(url_for("static", filename="favicon.svg"))

    @app.get("/")
    def home():
        db = SessionLocal()
        highlights = db.scalars(select(MenuItem).order_by(MenuItem.sort_order).limit(6)).all()
        photos = db.scalars(select(GalleryImage).order_by(GalleryImage.id.desc()).limit(3)).all()
        return render_template("index.html", highlights=highlights, photos=photos)

    @app.get("/menu")
    def menu():
        db = SessionLocal()
        return render_template("menu.html", groups=grouped_menu(db))

    @app.get("/gallery")
    def gallery():
        db = SessionLocal()
        images = db.scalars(select(GalleryImage).order_by(GalleryImage.id.desc())).all()
        return render_template("gallery.html", images=images)

    @app.route("/booking", methods=["GET", "POST"])
    def booking():
        if request.method == "POST":
            error = _save_booking(request.form)
            if error:
                flash(error, "error")
                return render_template("booking.html", form=request.form), 400
            flash("Your table request is in. We’ll confirm by phone or email.", "success")
            return redirect(url_for("booking"))
        return render_template("booking.html", form={})

    @app.get("/api/availability")
    def check_availability():
        try:
            booking_date = datetime.strptime(request.args.get("date", ""), "%Y-%m-%d").date()
            booking_time = datetime.strptime(request.args.get("time", ""), "%H:%M").time()
            party_size = int(request.args.get("party_size", ""))
            if datetime.combine(booking_date, booking_time) < datetime.now() or not 1 <= party_size <= 12:
                raise ValueError
        except ValueError:
            return jsonify(available=None, message="Choose a future date, time, and party size from 1 to 12."), 400

        db = SessionLocal()
        existing = db.scalars(
            select(Booking).where(
                Booking.booking_date == booking_date,
                Booking.booking_time == booking_time,
                Booking.status.in_(("pending", "confirmed")),
            )
        ).first()
        if existing:
            return jsonify(available=False, message="That time already has a booking request. Please try another time.")
        return jsonify(available=True, message="No booking is listed for that time. You can send a request; we’ll confirm by phone or email.")

    @app.get("/contact")
    def contact():
        return render_template("contact.html")

    @app.post("/api/chat")
    def chat():
        payload = request.get_json(silent=True) or {}
        question = str(payload.get("message") or payload.get("question") or "")
        db = SessionLocal()
        items = db.scalars(select(MenuItem).order_by(MenuItem.category, MenuItem.sort_order)).all()
        reply = answer_question(
            question,
            items,
            api_key=config.AI_API_KEY,
            api_base=config.AI_API_BASE,
            model=config.AI_MODEL,
            provider=config.CHAT_PROVIDER,
            gemini_api_key=config.GEMINI_API_KEY,
            gemini_model=config.GEMINI_MODEL,
            cafe_name=config.CAFE_NAME,
            hours=config.CAFE_HOURS,
            address=config.CAFE_ADDRESS,
        )
        return jsonify({"reply": reply})

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            db = SessionLocal()
            user = db.scalar(select(AdminUser).where(AdminUser.username == username))
            if user and check_password_hash(user.password_hash, password):
                session.clear()
                session["admin_user_id"] = user.id
                session["admin_username"] = user.username
                return redirect(request.args.get("next") or url_for("admin_dashboard"))
            flash("Those credentials do not match.", "error")
        return render_template("admin/login.html")

    @app.post("/admin/logout")
    def admin_logout():
        session.clear()
        return redirect(url_for("home"))

    @app.route("/admin/accounts", methods=["GET", "POST"])
    @login_required
    def admin_accounts():
        db = SessionLocal()
        current_user = db.get(AdminUser, session.get("admin_user_id"))
        if current_user is None:
            session.clear()
            return redirect(url_for("admin_login"))

        if request.method == "POST":
            action = request.form.get("action")
            if action == "change_password":
                current_password = request.form.get("current_password", "")
                new_password = request.form.get("new_password", "")
                confirm_password = request.form.get("confirm_password", "")
                if not check_password_hash(current_user.password_hash, current_password):
                    flash("Current password is incorrect.", "error")
                elif len(new_password) < 12:
                    flash("Choose a password with at least 12 characters.", "error")
                elif new_password != confirm_password:
                    flash("The new passwords do not match.", "error")
                else:
                    current_user.password_hash = generate_password_hash(new_password)
                    db.commit()
                    flash("Password changed.", "success")
            elif action == "create_user":
                username = request.form.get("username", "").strip()
                password = request.form.get("password", "")
                confirm_password = request.form.get("confirm_password", "")
                if not username or len(username) > 80:
                    flash("Enter a username up to 80 characters long.", "error")
                elif len(password) < 12:
                    flash("Choose a password with at least 12 characters.", "error")
                elif password != confirm_password:
                    flash("The passwords do not match.", "error")
                elif db.scalar(select(AdminUser.id).where(AdminUser.username == username)):
                    flash("That username is already in use.", "error")
                else:
                    db.add(AdminUser(username=username, password_hash=generate_password_hash(password)))
                    try:
                        db.commit()
                        flash("Admin user created.", "success")
                    except IntegrityError:
                        db.rollback()
                        flash("That username is already in use.", "error")
            return redirect(url_for("admin_accounts"))

        users = db.scalars(select(AdminUser).order_by(AdminUser.username)).all()
        return render_template("admin/accounts.html", users=users)

    @app.get("/admin")
    @login_required
    def admin_dashboard():
        db = SessionLocal()
        bookings = db.scalars(select(Booking).order_by(Booking.created_at.desc()).limit(8)).all()
        menu_count = db.scalar(select(func.count()).select_from(MenuItem)) or 0
        photo_count = db.scalar(select(func.count()).select_from(GalleryImage)) or 0
        pending = db.scalar(
            select(func.count()).select_from(Booking).where(Booking.status == "pending")
        ) or 0
        return render_template(
            "admin/dashboard.html",
            bookings=bookings,
            menu_count=menu_count,
            photo_count=photo_count,
            pending=pending,
        )

    @app.route("/admin/menu", methods=["GET", "POST"])
    @login_required
    def admin_menu():
        db = SessionLocal()
        if request.method == "POST":
            action = request.form.get("action")
            if action == "create":
                item = MenuItem(
                    category=request.form.get("category", "").strip() or "Other",
                    name=request.form.get("name", "").strip(),
                    description=request.form.get("description", "").strip(),
                    price=_parse_price(request.form.get("price")),
                    sort_order=int(request.form.get("sort_order") or 0),
                )
                if not item.name or item.price is None:
                    flash("Name and a valid price are required.", "error")
                else:
                    db.add(item)
                    db.commit()
                    flash("Menu item added.", "success")
            elif action == "update":
                item = db.get(MenuItem, int(request.form["id"]))
                if item:
                    item.category = request.form.get("category", "").strip() or item.category
                    item.name = request.form.get("name", "").strip() or item.name
                    item.description = request.form.get("description", "").strip()
                    price = _parse_price(request.form.get("price"))
                    if price is not None:
                        item.price = price
                    item.sort_order = int(request.form.get("sort_order") or item.sort_order)
                    db.commit()
                    flash("Menu item updated.", "success")
            elif action == "delete":
                item = db.get(MenuItem, int(request.form["id"]))
                if item:
                    db.delete(item)
                    db.commit()
                    flash("Menu item removed.", "success")
            return redirect(url_for("admin_menu"))
        return render_template("admin/menu.html", groups=grouped_menu(db))

    @app.route("/admin/gallery", methods=["GET", "POST"])
    @login_required
    def admin_gallery():
        db = SessionLocal()
        upload_dir = Path(app.config["UPLOAD_DIR"])
        if request.method == "POST":
            action = request.form.get("action")
            if action == "upload":
                file = request.files.get("image")
                caption = request.form.get("caption", "").strip()
                saved = _save_upload(file, upload_dir, config.ALLOWED_IMAGE_EXTENSIONS)
                if not saved:
                    flash("Please choose a JPG, PNG, WebP, or GIF image.", "error")
                else:
                    db.add(GalleryImage(filename=saved, caption=caption))
                    db.commit()
                    flash("Image added to the gallery.", "success")
            elif action == "replace":
                image = db.get(GalleryImage, int(request.form["id"]))
                file = request.files.get("image")
                if image and file and file.filename:
                    saved = _save_upload(file, upload_dir, config.ALLOWED_IMAGE_EXTENSIONS)
                    if saved:
                        _delete_file(upload_dir / image.filename)
                        image.filename = saved
                        image.caption = request.form.get("caption", image.caption).strip() or image.caption
                        db.commit()
                        flash("Image replaced.", "success")
                    else:
                        flash("That file type is not allowed.", "error")
            elif action == "delete":
                image = db.get(GalleryImage, int(request.form["id"]))
                if image:
                    _delete_file(upload_dir / image.filename)
                    db.delete(image)
                    db.commit()
                    flash("Image removed.", "success")
            elif action == "caption":
                image = db.get(GalleryImage, int(request.form["id"]))
                if image:
                    image.caption = request.form.get("caption", "").strip()
                    db.commit()
                    flash("Caption updated.", "success")
            return redirect(url_for("admin_gallery"))
        images = db.scalars(select(GalleryImage).order_by(GalleryImage.id.desc())).all()
        return render_template("admin/gallery.html", images=images)

    @app.route("/admin/bookings", methods=["GET", "POST"])
    @login_required
    def admin_bookings():
        db = SessionLocal()
        if request.method == "POST":
            booking = db.get(Booking, int(request.form["id"]))
            if booking:
                status = request.form.get("status", booking.status)
                if status in {"pending", "confirmed", "cancelled"}:
                    booking.status = status
                booking.notes = request.form.get("notes", booking.notes)
                db.commit()
                flash("Booking updated.", "success")
            return redirect(url_for("admin_bookings"))
        bookings = db.scalars(select(Booking).order_by(Booking.created_at.desc())).all()
        return render_template("admin/bookings.html", bookings=bookings)

    return app


def _parse_price(raw) -> Decimal | None:
    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, AttributeError):
        return None
    if value < 0:
        return None
    return value.quantize(Decimal("0.01"))


def _save_booking(form) -> str | None:
    name = (form.get("name") or "").strip()
    contact = (form.get("contact") or "").strip()
    party_raw = form.get("party_size") or ""
    date_raw = form.get("date") or ""
    time_raw = form.get("time") or ""

    if not name or not contact:
        return "Name and contact are required."
    try:
        party_size = int(party_raw)
        if party_size < 1 or party_size > 12:
            raise ValueError
    except ValueError:
        return "Party size must be between 1 and 12."
    try:
        booking_date = datetime.strptime(date_raw, "%Y-%m-%d").date()
        booking_time = datetime.strptime(time_raw, "%H:%M").time()
    except ValueError:
        return "Please choose a valid date and time."

    if datetime.combine(booking_date, booking_time) < datetime.now():
        return "Please choose a future date and time."

    db = SessionLocal()
    existing = db.scalars(
        select(Booking).where(
            Booking.booking_date == booking_date,
            Booking.booking_time == booking_time,
            Booking.status.in_(("pending", "confirmed")),
        )
    ).first()
    if existing:
        return "That time already has a booking request. Please choose another time."
    db.add(
        Booking(
            name=name,
            contact=contact,
            booking_date=booking_date,
            booking_time=booking_time,
            party_size=party_size,
            status="pending",
        )
    )
    db.commit()
    return None


def _save_upload(file, upload_dir: Path, allowed: set[str]) -> str | None:
    if not file or not file.filename:
        return None
    name = secure_filename(file.filename)
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in allowed:
        return None
    filename = f"{uuid4().hex}.{ext}"
    file.save(upload_dir / filename)
    return filename


def _delete_file(path: Path):
    try:
        if path.is_file():
            path.unlink()
    except OSError:
        pass


if __name__ == "__main__":
    application = create_app()
    create_tables()
    application.run(debug=cfg.DEBUG, host="127.0.0.1", port=5000)
