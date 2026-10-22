from __future__ import annotations

from decimal import Decimal

import httpx

from models import MenuItem

UNRELATED_REPLY = (
    "I can only help with Rayan Cafe — our coffee, tea, breakfast, hours, "
    "and how to book a table. For a reservation, use the booking form on this site."
)

BOOKING_REPLY = (
    "I cannot book a table from chat. Please use the Booking page to choose a "
    "date, time, and party size (1–12 people). The availability check only "
    "checks for another request at that exact time; it is not a confirmation. "
    "We will confirm your request by phone or email. For parties over 12, "
    "please contact the café using the Contact page."
)


def format_price(value) -> str:
    return f"₹{Decimal(str(value)):,.0f}"


def menu_rate_list(items: list[MenuItem]) -> str:
    lines = []
    current = None
    for item in sorted(items, key=lambda i: (i.category, i.sort_order, i.name)):
        if item.category != current:
            current = item.category
            lines.append(f"\n[{current}]")
        lines.append(f"- {item.name}: {format_price(item.price)}")
    return "\n".join(lines).strip()


def build_system_prompt(items: list[MenuItem], cafe_name: str, hours: str, address: str) -> str:
    rates = menu_rate_list(items) or "(the menu is currently empty)"
    return (
        f"You are the café assistant for {cafe_name}.\n"
        "Answer only questions about this café: menu items, exact prices, hours, "
        "location, and how to request a table.\n"
        "You must quote prices exactly as listed below. Never invent, round, "
        "or estimate a price. All listed prices are in Indian rupees (INR). "
        "When asked the price of a listed item, answer with its exact listed price. "
        "If asked for menu prices generally, show the official rate list. "
        "If an item is not on the list, say it is not on the menu.\n"
        "If the question is unrelated to the café, politely decline.\n"
        "If the guest wants to reserve a table, tell them to use the booking form "
        "on the website. Party size is limited to 1–12 people. Guests select a "
        "date and time, then may check whether another pending or confirmed "
        "request exists at that exact time. The check does not measure table "
        "capacity and does not confirm a booking. Staff confirm requests by phone "
        "or email. Parties over 12 should contact the café through the Contact page. "
        "Never claim that you checked live availability or booked a table.\n"
        f"Hours: {hours}\n"
        f"Address: {address}\n"
        f"Official rate list:\n{rates}"
    )


def lookup_price(items: list[MenuItem], name: str) -> str | None:
    needle = name.strip().lower()
    for item in items:
        if item.name.lower() == needle:
            return format_price(item.price)
    return None


def answer_question(
    question: str,
    items: list[MenuItem],
    *,
    api_key: str,
    api_base: str,
    model: str,
    cafe_name: str,
    hours: str,
    address: str,
    provider: str = "openai",
    gemini_api_key: str = "",
    gemini_model: str = "gemini-3.6-flash",
) -> str:
    question = (question or "").strip()
    if not question:
        return "Ask me about our coffee, tea, breakfast, or prices."

    price_reply = _price_question_reply(question, items)
    if price_reply:
        return price_reply

    provider = (provider or "openai").strip().lower()
    if provider == "gemini":
        if not gemini_api_key:
            return _offline_answer(question, items)
    elif not api_key:
        return _offline_answer(question, items)

    prompt = build_system_prompt(items, cafe_name, hours, address)
    try:
        with httpx.Client(timeout=20.0) as client:
            if provider == "gemini":
                url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{gemini_model}:generateContent"
                )
                payload = {
                    "system_instruction": {"parts": [{"text": prompt}]},
                    "contents": [{"parts": [{"text": question}]}],
                    "generationConfig": {"temperature": 0.2},
                }
                headers = {
                    "x-goog-api-key": gemini_api_key,
                    "Content-Type": "application/json",
                }
            else:
                url = f"{api_base}/chat/completions"
                payload = {
                    "model": model,
                    "temperature": 0.2,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": question},
                    ],
                }
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        if provider == "gemini":
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(part.get("text", "") for part in parts).strip() or _offline_answer(question, items)
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return _offline_answer(question, items)


def _offline_answer(question: str, items: list[MenuItem]) -> str:
    """Used when the AI API is missing or unavailable; still grounded in DB prices."""
    q = question.lower()

    unrelated_markers = (
        "stock", "crypto", "python", "code", "weather", "politics",
        "homework", "recipe for lasagna",
    )
    if any(marker in q for marker in unrelated_markers) and not any(
        item.name.lower() in q for item in items
    ):
        return UNRELATED_REPLY

    if any(word in q for word in ("book", "reserv", "table", "party")):
        return BOOKING_REPLY

    matches = [item for item in items if item.name.lower() in q]
    if not matches and "price" in q:
        matches = [
            item
            for item in items
            if any(token in item.name.lower() for token in q.split() if len(token) > 3)
        ]

    if matches:
        bits = [f"{item.name} is {format_price(item.price)}" for item in matches]
        return "Our current prices: " + "; ".join(bits) + "."

    if any(word in q for word in ("menu", "price", "cost", "how much", "coffee", "tea", "breakfast")):
        return "Here is our current rate list:\n" + menu_rate_list(items)

    return UNRELATED_REPLY


def _price_question_reply(question: str, items: list[MenuItem]) -> str | None:
    """Answer price questions from saved menu values, without model estimation."""
    q = question.lower()
    matches = [item for item in items if item.name.lower() in q]
    if not matches and any(word in q for word in ("book", "reserv", "table", "party")):
        return None
    asks_price = any(
        term in q
        for term in ("price", "cost", "how much", "rate", "rates", "kitne ka", "kitna", "kitni", "daam", "keemat")
    )
    if not asks_price:
        return None

    if matches:
        return "Our current prices: " + "; ".join(
            f"{item.name}: {format_price(item.price)}" for item in matches
        ) + "."
    return "Here are our current menu prices in INR:\n" + menu_rate_list(items)
