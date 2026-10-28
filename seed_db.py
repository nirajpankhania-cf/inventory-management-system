from pathlib import Path

import inventory_db
import sample_data

FOLDER = Path(__file__).parent
TABLES = ["suppliers", "products", "sales", "sale_items", "stock_movements"]

def main():
    connection = inventory_db.connect()

    #create tables if they dont exist.
    connection.executescript((FOLDER/ "schema.sql").read_text(encoding="utf-8"))

    # only load sample data into empty database
    existing = connection.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
    if existing > 0:
        print("database already seeded, leaving data as is")
    else:
        sample_data.load_sample_data(connection)

    # report the row count for each table
    for table in TABLES:
        count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}")

    connection.close()

if __name__ == "__main__":
    main()
