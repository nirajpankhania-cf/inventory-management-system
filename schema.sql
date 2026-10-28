CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    email TEXT
) STRICT;


CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    reorder_level INTEGER NOT NULL DEFAULT 0 CHECK (reorder_level >= 0)
) STRICT;

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY,
    sold_at TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS sale_items (
    sale_id INTEGER NOT NULL REFERENCES sales(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0),
    PRIMARY KEY (sale_id, product_id)
) STRICT;

CREATE TABLE IF NOT EXISTS stock_movements(
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    change INTEGER NOT NULL CHECK (change <> 0),
    reason TEXT NOT NULL CHECK (reason IN ('restock', 'adjustment', 'sale')),
    moved_at TEXT NOT NULL
) STRICT;

CREATE INDEX IF NOT EXISTS idx_stock_movements_product_id ON stock_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_product_id ON sale_items(product_id);
CREATE INDEX IF NOT EXISTS idx_products_supplier_id ON products(supplier_id);
