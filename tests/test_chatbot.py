from chatbot import BOOKING_REPLY, UNRELATED_REPLY, answer_question, build_system_prompt, lookup_price
from db import SessionLocal
from models import MenuItem


def _items():
    db = SessionLocal()
    items = db.query(MenuItem).all()
    SessionLocal.remove()
    return items


def test_rate_list_in_system_prompt_matches_database_prices(client):
    items = _items()
    cappuccino = next(i for i in items if i.name == "Cappuccino")
    espresso = next(i for i in items if i.name == "Espresso")
    prompt = build_system_prompt(
        items,
        cafe_name="Hearth & Steam",
        hours="Tue–Fri 7:00–15:00",
        address="48 Willow Lane",
    )
    assert f"- Cappuccino: {cappuccino.price_display()}" in prompt
    assert f"- Espresso: {espresso.price_display()}" in prompt
    assert "$4.50" in prompt
    assert "$3.25" in prompt


def test_lookup_price_is_exact(client):
    items = _items()
    assert lookup_price(items, "cappuccino") == "$4.50"
    assert lookup_price(items, "Green Tea") == "$3.50"
    assert lookup_price(items, "not on menu") is None


def test_offline_chat_quotes_menu_price(client):
    items = _items()
    reply = answer_question(
        "How much is a cappuccino?",
        items,
        api_key="",
        api_base="http://example.invalid",
        model="test",
        cafe_name="Hearth & Steam",
        hours="hours",
        address="address",
    )
    assert "$4.50" in reply
    assert "Cappuccino" in reply


def test_chat_endpoint_returns_grounded_price(client):
    response = client.post("/api/chat", json={"message": "What is the price of espresso?"})
    assert response.status_code == 200
    body = response.get_json()
    assert "$3.25" in body["reply"]


def test_chat_declines_unrelated_questions(client):
    response = client.post("/api/chat", json={"message": "What is the weather and bitcoin price?"})
    assert UNRELATED_REPLY in response.get_json()["reply"]


def test_chat_directs_reservations_to_form(client):
    response = client.post("/api/chat", json={"message": "Can you book a table for four?"})
    assert BOOKING_REPLY in response.get_json()["reply"]
