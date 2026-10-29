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
