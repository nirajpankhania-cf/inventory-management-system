"""Sample rows for the hardware store. Used by seed_db.py and by the test fixture."""

# (id, name, email)
SUPPLIERS = [
    (1, "Stanley Tools", "sales@stanley.example"),
    (2, "Draper", None),
    (3, "Dulux Paints", "orders@dulux.example"),
    (4, "Screwfix Supply", "trade@screwfix.example"),
]

# (id, sku, name, category, supplier_id, unit_price_cents, quantity, reorder_level)
PRODUCTS = [
    (1, "HAM-001", "Claw Hammer", "Tools", 1, 1299, 25, 5),
    (2, "SCR-002", "Screwdriver Set", "Tools", 1, 1899, 8, 4),
    (3, "TAP-003", "Tape Measure 5m", "Tools", 2, 799, 3, 5),
    (4, "WRE-004", "Adjustable Wrench", "Tools", 2, 1550, 0, 2),
    (5, "PNT-005", "White Emulsion 5L", "Paint", 3, 2499, 12, 3),
    (6, "PNT-006", "Gloss Black 1L", "Paint", 3, 1199, 6, 3),
    (7, "BRU-007", "Paint Brush Set", "Paint", 3, 899, 15, 5),
    (8, "SCW-008", "Wood Screws 200pk", "Fixings", 4, 549, 40, 10),
    (9, "NAL-009", "Nails 500g", "Fixings", 4, 349, 10, 10),
    (10, "PLG-010", "Wall Plugs 100pk", "Fixings", 4, 299, 50, 10),
    (11, "DRL-011", "Cordless Drill", "Power Tools", 2, 7999, 4, 2),
    (12, "SAW-012", "Hand Saw", "Tools", 1, 1499, 7, 3),
]

# (id, sold_at)
SALES = [
    (1, "2026-10-01T09:30:00"),
    (2, "2026-10-03T11:15:00"),
    (3, "2026-10-07T14:00:00"),
    (4, "2026-10-10T10:45:00"),
    (5, "2026-10-14T16:20:00"),
]

# (sale_id, product_id, quantity, unit_price_cents)
# The hammer sold at 1199 in sale 1 and 1299 in sale 5: the price went up in between.
SALE_ITEMS = [
    (1, 1, 1, 1199),
    (1, 8, 2, 549),
    (1, 10, 1, 299),
    (2, 5, 2, 2499),
    (2, 7, 1, 899),
    (3, 11, 1, 7999),
    (3, 8, 1, 549),
    (3, 2, 1, 1899),
    (4, 3, 2, 799),
    (4, 9, 1, 349),
    (5, 6, 1, 1199),
    (5, 1, 2, 1299),
]


def load_sample_data(connection):
    """Insert the sample rows. Assumes the tables exist and are empty."""
    connection.executemany(
        "INSERT INTO suppliers (id, name, email) VALUES (?, ?, ?)",
        SUPPLIERS,
    )
    connection.executemany(
        "INSERT INTO products "
        "(id, sku, name, category, supplier_id, unit_price_cents, quantity, reorder_level) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        PRODUCTS,
    )
    connection.executemany(
        "INSERT INTO sales (id, sold_at) VALUES (?, ?)",
        SALES,
    )
    connection.executemany(
        "INSERT INTO sale_items (sale_id, product_id, quantity, unit_price_cents) "
        "VALUES (?, ?, ?, ?)",
        SALE_ITEMS,
    )
    connection.commit()
