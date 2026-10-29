import sqlite3
from pathlib import Path

import pytest

import inventory_db

SCHEMA = Path(__file__).parent.parent / "schema.sql"

def test_sample_data_has_expected_row_counts(connection):
    assert connection.execute("SELECT COUNT(*) FROM suppliers")

def test_foreign_keys_are_on(connection):
    assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1

def test_schema_can_be_run_again_without_losing_data(connection):
    connection.executescript(SCHEMA.read_text(encoding="utf-8"))
    assert connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 12

def test_movement_with_invalid_reason_is_refused(connection):
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO stock_movements (product_id, change, reason, moved_at) "
            "VALUES (?, ?, ?, ?)",
            (1, 5, "theft", "2026-10-28T10:00:00"),
        )

def test_add_product_returns_new_id(connection):
    new_id = inventory_db.add_product(connection, "LAD-013", "Step Ladder", "Tools", 2, 4999, 5, 1)
    assert new_id == 13
    assert inventory_db.get_product(connection, new_id)["name"] == "Step Ladder"

@pytest.mark.parametrize(
    "sku, supplier_id, price, quantity",
    [
        ("HAM-001", 1, 1299, 5), #duplicate sku
        ("NEW-009", 99, 199, 5), #unknown supplier
        ("NEW-099", 1, -1, 5), #negative price
        ("NEW-099", 1, 1299, -1), #negative quantity
    ]
)

def test_add_product_refuses_bad_data(connection, sku, supplier_id, price, quantity):
    with pytest.raises(sqlite3.IntegrityError):
        inventory_db.add_product(connection, sku, "Thing", "Tools", supplier_id, price, quantity)

def test_get_product_returns_none_when_missing(connection):
    assert inventory_db.get_product(connection, 999) is None

def test_update_price_changes_price(connection):
    assert inventory_db.update_price(connection, 1, 1399) is True
    assert inventory_db.get_product(connection, 1)["unit_price_cents"] == 1399

def test_update_price_for_missing_product_returns_false(connection):
    assert inventory_db.update_price(connection, 999, 1399) is False

def test_update_price_rejects_negative(connection):
    with pytest.raises(sqlite3.IntegrityError):
        inventory_db.update_price(connection, 1, -1)

def test_sold_product_cannot_be_deleted(connection):
    with pytest.raises(sqlite3.IntegrityError):
        inventory_db.delete_product(connection, 1)

def test_never_sold_product_can_be_deleted(connection):
    assert inventory_db.delete_product(connection, 4) is True
    assert inventory_db.get_product(connection, 4) is None
