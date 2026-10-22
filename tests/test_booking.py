from db import SessionLocal
from models import Booking


def test_booking_page_renders(client):
    response = client.get("/booking")
    assert response.status_code == 200
    assert b"Request a table" in response.data


def test_booking_submission_saves_row(client):
    response = client.post(
        "/booking",
        data={
            "name": "Maya Chen",
            "contact": "maya@example.com",
            "date": "2026-11-02",
            "time": "09:30",
            "party_size": "3",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Your table request is in" in response.data

    db = SessionLocal()
    booking = db.query(Booking).one()
    assert booking.name == "Maya Chen"
    assert booking.contact == "maya@example.com"
    assert booking.party_size == 3
    assert booking.status == "pending"
    assert str(booking.booking_date) == "2026-11-02"
    SessionLocal.remove()


def test_booking_rejects_invalid_party_size(client):
    response = client.post(
        "/booking",
        data={
            "name": "Maya Chen",
            "contact": "maya@example.com",
            "date": "2026-11-02",
            "time": "09:30",
            "party_size": "99",
        },
    )
    assert response.status_code == 400
    db = SessionLocal()
    assert db.query(Booking).count() == 0
    SessionLocal.remove()
