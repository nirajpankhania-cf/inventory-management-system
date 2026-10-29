import os
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(os.environ.get("INVENTORY_DB", Path(__file__).parent / "inventory.db"))

def _log_movement(connection, product_id, change, reason, when):
    """insert one stock movement"""
    connection.execute(
        "INSERT INTO stock_movements (product_id, change, reason, moved_at) "
        "VALUES (?, ?, ?, ?)",
        (product_id, change, reason, when),
    )

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

def search_products(connection, text="", category=None, max_price_cents=None, in_stock_only=False, low_stock_only=False):
    """find products whose name, sku, or name contains text, with optional filters"""
    sql = (
        "SELECT p.id, p.sku, p.name, p.category, s.name AS supplier_name, p.unit_price_cents, p.quantity, p.reorder_level "
        "FROM products p "
        "JOIN suppliers s ON s.id = p.supplier_id "
        "WHERE (p.name LIKE ? OR p.sku LIKE ? OR s.name LIKE ?)"
    )

    pattern = f"%{text}%"
    params = [pattern, pattern, pattern] # match three q marks above
    if category is not None:
        sql += " AND p.category = ?"
        params.append(category)
    if max_price_cents is not None:
        sql += " AND p.unit_price_cents <= ?"
        params.append(max_price_cents)
    if in_stock_only:
        sql += " AND p.quantity > 0"
    if low_stock_only:
        sql += " AND p.quantity <= p.reorder_level"
    sql += " ORDER by p.name"
    return connection.execute(sql, params).fetchall()

"""Reports ============================================"""
def stock_value_by_supplier(connection):
    """each suppliers name and total value of its stock descending"""
    return connection.execute(
        "SELECT s.name AS supplier_name, "
        "SUM(p.unit_price_cents * p.quantity) AS stock_value_cents "
        "FROM suppliers s JOIN products p ON p.supplier_id = s.id "
        "GROUP BY s.id, s.name "
        "ORDER BY stock_value_cents DESC"
    ).fetchall()

def low_stock(connection):
    """return low stock (products below their reorder level) descending"""
    return connection.execute(
        "SELECT sku, name, quantity, reorder_level, reorder_level - quantity AS shortfall "
        "FROM products WHERE quantity <= reorder_level "
        "ORDER BY shortfall DESC, name"
    ).fetchall()

def sales_by_product(connection):
    """each sold product with units and revenue in cents descending"""
    return connection.execute(
        "SELECT p.sku, p.name, SUM(si.quantity) as units_sold, "
        "SUM(si.quantity * si.unit_price_cents) AS revenue_cents "
        "FROM products p JOIN sale_items si ON si.product_id = p.id "
        "GROUP BY p.id, p.sku, p.name "
        "ORDER BY revenue_cents DESC"
    ).fetchall()

def never_sold(connection):
    """products that have no sales"""
    return connection.execute(
        "SELECT p.sku, p.name FROM products p "
        "LEFT JOIN sale_items si ON si.product_id = p.id "
        "WHERE si.product_id is NULL "
        "ORDER BY p.name"
    ).fetchall()

def restock(connection, product_id, amount, when=None):
    """increases a product's stock and logs restock mvement. return new stock level"""
    if amount <= 0:
        raise ValueError('restock amount must be greater than zero')
    when = when or datetime.now().isoformat(timespec="seconds")
    with connection:
        cursor = connection.execute(
            "UPDATE products SET quantity = quantity + ? WHERE id = ?",
            (amount, product_id),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"no product with product id {product_id}")
        _log_movement(connection, product_id, amount, "restock", when)
    return connection.execute(
        "SELECT quantity FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()["quantity"]
