import sqlite3
from contextlib import closing
from datetime import date

import inventory_db as db

BACKUP_FOLDER = db.DB_PATH.parent / "backups"


def money(cents):
    """Format whole cents as pounds and pence"""
    return f"{cents / 100:.2f}"


def to_cents(pounds_text):
    """Turn text into whole cent"""
    return round(float(pounds_text) * 100)


def ask_int(prompt):
    """ask user for number and return it"""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a whole number.")


def ask_cents(prompt):
    """price in pounds from user turned into cents"""
    while True:
        try:
            return to_cents(input(prompt))
        except ValueError:
            print("enter a price like 12.99.")


def ask_yes_no(prompt):
    """Return True for yes, False for anything else"""
    return input(prompt).strip().lower() in ("y", "yes")


def print_product(row):
    print(
        f"{row['id']}. {row['sku']} {row['name']} ({row['category']}) "
        f"from {row['supplier_name']}, {money(row['unit_price_cents'])}, "
        f"{row['quantity']} in stock, reorder at {row['reorder_level']}"
    )


def search(connection):
    """search with optional filters"""
    text = input("Search text (blank for all): ").strip()
    category = input("Category (blank for any): ").strip() or None
    price_text = input("Maximum price in pounds (blank for none): ").strip()
    max_price_cents = None
    if price_text:
        try:
            max_price_cents = to_cents(price_text)
        except ValueError:
            print("That is not a price, ignoring the price filter.")
    in_stock_only = ask_yes_no("In stock only? (y/n): ")
    low_stock_only = ask_yes_no("Low stock only? (y/n): ")

    rows = db.search_products(
        connection, text, category, max_price_cents, in_stock_only, low_stock_only
    )
    if not rows:
        print("No products found.")
    for row in rows:
        print_product(row)


def look_up(connection):
    product = db.get_product(connection, ask_int("Product id: "))
    if product is None:
        print("No product with that id.")
    else:
        print_product(product)


def add_product(connection):
    sku = input("SKU: ").strip()
    name = input("Name: ").strip()
    category = input("Category: ").strip()
    supplier_id = ask_int("Supplier id: ")
    price_cents = ask_cents("Price in pounds: ")
    quantity = ask_int("Quantity in stock: ")
    reorder_level = ask_int("Reorder level: ")
    try:
        new_id = db.add_product(
            connection, sku, name, category, supplier_id, price_cents, quantity, reorder_level
        )
    except sqlite3.IntegrityError as e:
        print(f"Could not add product: {e}")
        return
    print(f"Added product {new_id}.")


def restock(connection):
    product_id = ask_int("Product id: ")
    amount = ask_int("Amount to add: ")
    try:
        new_quantity = db.restock(connection, product_id, amount)
    except ValueError as e:
        print(f"Could not restock: {e}")
        return
    print(f"Done. Stock is now {new_quantity}.")


def record_sale(connection):
    """Collect product and quantity pairs until the user enters 0, then record them as one sale."""
    items = []
    while True:
        product_id = ask_int("Product id (0 to finish): ")
        if product_id == 0:
            break
        quantity = ask_int("Quantity: ")
        items.append((product_id, quantity))
    try:
        sale_id = db.record_sale(connection, items)
    except (ValueError, sqlite3.IntegrityError) as e:
        print(f"Sale not recorded: {e}")
        return
    print(f"Recorded sale {sale_id}.")


def stock_value_report(connection):
    for row in db.stock_value_by_supplier(connection):
        print(f"{row['supplier_name']}: {money(row['stock_value_cents'])}")


def low_stock_report(connection):
    rows = db.low_stock(connection)
    if not rows:
        print("Nothing is low on stock.")
    for row in rows:
        print(
            f"{row['sku']} {row['name']}: {row['quantity']} in stock, "
            f"reorder at {row['reorder_level']}, short by {row['shortfall']}"
        )


def sales_report(connection):
    for row in db.sales_by_product(connection):
        print(f"{row['sku']} {row['name']}: {row['units_sold']} sold, {money(row['revenue_cents'])}")


def never_sold_report(connection):
    rows = db.never_sold(connection)
    if not rows:
        print("Every product has sold at least once.")
    for row in rows:
        print(f"{row['sku']} {row['name']}")


def backup(connection):
    path = BACKUP_FOLDER / f"inventory-{date.today().isoformat()}.db"
    db.backup_database(db.DB_PATH, path)
    print(f"Backed up to {path}")


COMMANDS = {
    "1": ("Search products", search),
    "2": ("Look up a product", look_up),
    "3": ("Add a product", add_product),
    "4": ("Restock", restock),
    "5": ("Record a sale", record_sale),
    "6": ("Report: stock value by supplier", stock_value_report),
    "7": ("Report: low stock", low_stock_report),
    "8": ("Report: sales by product", sales_report),
    "9": ("Report: never sold", never_sold_report),
    "b": ("Back up the database", backup),
    "q": ("Quit", None),
}


def main():
    with closing(db.connect()) as connection:
        while True:
            print("\nInventory")
            for key, (label, _) in COMMANDS.items():
                print(f"  {key}) {label}")
            choice = input("Choose: ").strip().lower()
            if choice == "q":
                break
            if choice not in COMMANDS:
                print("I don't understand that option.")
                continue
            COMMANDS[choice][1](connection)


if __name__ == "__main__":
    main()
