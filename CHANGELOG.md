# Changelog

## 1.0.0 - 2026-10-29

First release.

- SQLite database with suppliers, products, sales, sale_items and stock_movements tables.
  Constraints are enforced by the database: unique SKUs, required fields, no negative prices
  or quantities, valid movement reasons, foreign keys.
- Seed script with sample data.
- Add, look up, reprice and delete products.
- Search by name, SKU or supplier with category, price, in-stock and low-stock filters.
- Reports: stock value by supplier, low stock, sales by product, never sold.
- Restock, adjust and record a sale, each as a single transaction.
- Terminal menu that handles bad input without crashing.
- Database backup using SQLite's backup API.
- Docker image with the database stored in a volume.
