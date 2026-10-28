# PLAN.md

Inventory system for a hardware store. SQLite database, Python functions in `inventory_db.py`,
menu in `main.py`, schema in `schema.sql`.

Decisions that apply everywhere:

- Money is stored as whole cents. Only the menu formats it to 2 decimals.
- Dates are ISO text strings like `2026-10-28T09:15:00`.
- All tables are STRICT (my SQLite is 3.50.4).
- One `connect()` function turns on foreign keys and sets `row_factory = sqlite3.Row`.

## 1. Tables

### suppliers

One row per supplier. Name isn't repeated on every product.

| Column | Type / constraints |
|---|---|
| id | INTEGER PRIMARY KEY |
| name | TEXT NOT NULL UNIQUE |
| email | TEXT |

### products

One row per thing the store sells.

| Column | Type / constraints |
|---|---|
| id | INTEGER PRIMARY KEY |
| sku | TEXT NOT NULL UNIQUE |
| name | TEXT NOT NULL |
| category | TEXT NOT NULL |
| supplier_id | INTEGER NOT NULL REFERENCES suppliers(id) |
| unit_price_cents | INTEGER NOT NULL CHECK (unit_price_cents >= 0) |
| quantity | INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0) |
| reorder_level | INTEGER NOT NULL DEFAULT 0 CHECK (reorder_level >= 0) |

Low stock = quantity <= reorder_level. The CHECK on quantity stops a sale taking stock
below zero.

### sales

One row per sale. several lines can share one sale and one date.

| Column | Type / constraints |
|---|---|
| id | INTEGER PRIMARY KEY |
| sold_at | TEXT NOT NULL |

### sale_items

Junction table between sales and products. Holds the quantity and the price
charged at the time, because the product price can change later and old sales shouldn't.

| Column | Type / constraints |
|---|---|
| sale_id | INTEGER NOT NULL REFERENCES sales(id) |
| product_id | INTEGER NOT NULL REFERENCES products(id) |
| quantity | INTEGER NOT NULL CHECK (quantity > 0) |
| unit_price_cents | INTEGER NOT NULL CHECK (unit_price_cents >= 0) |
| | PRIMARY KEY (sale_id, product_id) |

The composite primary key means the same product can't appear twice in one sale.

### stock_movements

The log of every stock change, so you can see what changed and why.

| Column | Type / constraints |
|---|---|
| id | INTEGER PRIMARY KEY |
| product_id | INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE |
| change | INTEGER NOT NULL CHECK (change <> 0) |
| reason | TEXT NOT NULL CHECK (reason IN ('restock', 'adjustment', 'sale')) |
| moved_at | TEXT NOT NULL |

### Rules the database enforces

- unique SKUs: UNIQUE on products.sku
- required fields: NOT NULL on everything except suppliers.email
- no negative prices or quantities: the CHECKs above
- valid reason: CHECK (reason IN (...))
- foreign keys: the REFERENCES clauses, and `connect()` runs `PRAGMA foreign_keys = ON` first

### Indexes

SQLite doesn't index foreign keys automatically:

- `idx_products_supplier_id` on products(supplier_id): used by get_product, search, and the stock value report
- `idx_sale_items_product_id` on sale_items(product_id): used by sales by product and never sold

### Running the schema twice

`schema.sql` uses `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS` and no DROP, so
running it again does nothing. `seed_db.py` checks if suppliers already has rows and stops if
it does, with a `--reset` flag to wipe and reload.

## 2. Relationships

```
suppliers (one) ---- (many) products
products  (one) ---- (many) sale_items
sales     (one) ---- (many) sale_items
products  (one) ---- (many) stock_movements
```

## 3. Functions

All take the connection first, none print or use input(). Single-statement functions commit
themselves. Multi-step ones use `with connection:` and nothing inside commits.

| Function | Returns | Fails with |
|---|---|---|
| `connect(path=DB_PATH)` | connection | DB_PATH from env var INVENTORY_DB, default file next to code |
| `add_product(con, sku, name, category, supplier_id, unit_price_cents, quantity=0, reorder_level=0)` | new id | IntegrityError: duplicate SKU, unknown supplier, negative price/qty |
| `get_product(con, product_id)` | Row with supplier_name (JOIN), or None | |
| `update_price(con, product_id, new_price_cents)` | True / False if no such product | IntegrityError if negative |
| `delete_product(con, product_id)` | True / False if no such product | IntegrityError if it has sale_items |
| `search_products(con, text="", category=None, max_price_cents=None, in_stock_only=False, low_stock_only=False)` | list of Rows sorted by name | |
| `stock_value_by_supplier(con)` | supplier_name, stock_value_cents, highest first | |
| `low_stock(con)` | sku, name, quantity, reorder_level, shortfall | |
| `sales_by_product(con)` | sku, name, units_sold, revenue_cents, highest revenue first | |
| `never_sold(con)` | sku, name | |
| `restock(con, product_id, amount, when=None)` | new quantity | ValueError if amount <= 0 or unknown product |
| `adjust_stock(con, product_id, change, when=None)` | new quantity | ValueError if change == 0 or unknown product, IntegrityError if stock would go negative |
| `record_sale(con, items, when=None)` | new sale id | ValueError unknown product / empty list, IntegrityError not enough stock / same product twice |
| `backup_database(source_path, backup_path)` | backup path | uses SQLite's backup API |

Private helper `_log_movement(con, product_id, change, reason, when)` inserts one movement row
and never commits. Only called inside a transaction.

Search: text matches name, SKU or supplier name with LIKE (case-insensitive in SQLite). Each
filter adds a fixed bit of SQL and appends its value to the params list. Wildcards go in the
value.

never_sold uses LEFT JOIN ... WHERE sale_items.product_id IS NULL rather than NOT IN.

`when=None` defaults to `datetime.now().isoformat(timespec="seconds")` so tests can pass a fixed
date.

## 4. Multi-step operations

Each one is a single `with connection:` block. Finishes normally = commit. Any exception =
rollback and the exception carries on to the caller.

### restock

1. If amount <= 0 raise ValueError (before any SQL)
2. `with connection:`
3. UPDATE products SET quantity = quantity + ? WHERE id = ?. rowcount 0 = unknown product, raise ValueError
4. `_log_movement(+amount, 'restock')`
5. return new quantity

Undone on failure: the UPDATE and the movement.

### adjust

1. If change == 0 raise ValueError
2. `with connection:`
3. UPDATE products SET quantity = quantity + ?. The CHECK raises IntegrityError if the result is negative. rowcount 0 = unknown product
4. `_log_movement(change, 'adjustment')`
5. return new quantity

Undone on failure: the UPDATE and the movement.

### record_sale

1. If items is empty raise ValueError
2. `with connection:`
3. INSERT INTO sales, keep lastrowid as sale_id
4. for each (product_id, quantity):
   - SELECT the product's current price. None = unknown product, raise ValueError
   - INSERT INTO sale_items at that price. Composite PK catches the same product twice
   - UPDATE products SET quantity = quantity - ?. CHECK catches not enough stock
   - `_log_movement(-quantity, 'sale')`
5. return sale_id

If anything fails, everything since step 2 is rolled back: the sale row, all lines so far, all
stock changes so far, all movements so far.

## 5. Release plan

| PR | Branch | What's in it |
|---|---|---|
| 1 | feature/database-and-seed | schema.sql, seed_db.py, connect(), test fixture, ci.yml (pytest + ruff) |
| 2 | feature/products-and-search | product functions, search, their tests |
| 3 | feature/reports | four reports, one test each against seed data |
| 4 | feature/stock-and-sales | restock, adjust, record_sale, tests incl. failed sale |
| 5 | feature/menu-and-container | main.py, backup, Dockerfile, .dockerignore, docker-build CI job, README, CHANGELOG |
| 6 | feature/low-stock-banner | banner on startup using len(low_stock()), CHANGELOG entry |

Tag v1.0.0 after PR 5 and v1.1.0 after PR 6.
