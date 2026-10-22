from decimal import Decimal

MENU_SEED = [
    {"category": "Coffee", "name": "Espresso", "description": "A short, concentrated shot.", "price": Decimal("120"), "sort_order": 1},
    {"category": "Coffee", "name": "Americano", "description": "Espresso stretched with hot water.", "price": Decimal("150"), "sort_order": 2},
    {"category": "Coffee", "name": "Cappuccino", "description": "Equal parts espresso, steamed milk, and foam.", "price": Decimal("190"), "sort_order": 3},
    {"category": "Coffee", "name": "Latte", "description": "Espresso with steamed milk.", "price": Decimal("200"), "sort_order": 4},
    {"category": "Coffee", "name": "Mocha", "description": "Espresso, chocolate, and steamed milk.", "price": Decimal("220"), "sort_order": 5},
    {"category": "Tea", "name": "English Breakfast", "description": "Full-bodied black tea.", "price": Decimal("120"), "sort_order": 1},
    {"category": "Tea", "name": "Earl Grey", "description": "Black tea with bergamot.", "price": Decimal("130"), "sort_order": 2},
    {"category": "Tea", "name": "Green Tea", "description": "Light, steamed sencha.", "price": Decimal("140"), "sort_order": 3},
    {"category": "Tea", "name": "Chamomile", "description": "Caffeine-free floral infusion.", "price": Decimal("140"), "sort_order": 4},
    {"category": "Tea", "name": "Chai Latte", "description": "Spiced tea with steamed milk.", "price": Decimal("180"), "sort_order": 5},
    {"category": "Breakfast", "name": "Pancakes", "description": "Stack of three with maple syrup.", "price": Decimal("350"), "sort_order": 1},
    {"category": "Breakfast", "name": "Eggs and Toast", "description": "Two eggs any style, sourdough toast.", "price": Decimal("320"), "sort_order": 2},
    {"category": "Breakfast", "name": "Avocado Toast", "description": "Smashed avocado, chili flake, lemon.", "price": Decimal("380"), "sort_order": 3},
    {"category": "Breakfast", "name": "Granola Bowl", "description": "Yogurt, house granola, seasonal fruit.", "price": Decimal("280"), "sort_order": 4},
    {"category": "Breakfast", "name": "Bacon Breakfast Sandwich", "description": "Egg, cheddar, and bacon on a roll.", "price": Decimal("340"), "sort_order": 5},
]

GALLERY_SEED = [
    {"filename": "counter.jpg", "caption": "The morning counter"},
    {"filename": "pour.jpg", "caption": "A slow pour-over"},
    {"filename": "breakfast.jpg", "caption": "Eggs, toast, and light"},
    {"filename": "seats.jpg", "caption": "Window seats"},
]
