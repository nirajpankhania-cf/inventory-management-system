import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("INVENTORY_DB", Path(__file__).parent / "inventory.db"))

def connect(path=DB_PATH):
    """open a connection with foreign keys on and rows readable by col name."""
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection

def add_product(connection, sku, name, category, supplier_id, unit_price_cents, quantity=0, reorder_level=0):
    """add a product and return its new id."""
    cursor = connection.execute(
        "INSERT INTO products (sku, name, category, supplier_id, unit_price_cents, quantity, reorder_level)"
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (sku, name, category, supplier_id, unit_price_cents, quantity, reorder_level),
    )
    connection.commit()
    return cursor.lastrowid

def get_product(connection, product_id):
    """return one product as a row"""
    return connection.execute(
        "SELECT p.id, p.sku, p.name, p.category, s.name AS supplier_name, p.unit_price_cents, p.quantity, p.reorder_level "
        "FROM products p "
        "JOIN suppliers s ON s.id = p.supplier_id "
        "where p.id = ?",
        (product_id,),
    ).fetchone()

def update_price(connection, product_id, price):
    """set a new price for a product"""
    cursor = connection.execute(
        "UPDATE products SET unit_price_cents = ? where id = ?",
        (price, product_id),
    )
    connection.commit()
    return cursor.rowcount == 1

def delete_product(connection, product_id):
    """delete product"""
    cursor = connection.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )
    connection.commit()
    return cursor.rowcount == 1
