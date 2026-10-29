# Inventory Management System

A terminal inventory system

## Run it

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 seed_db.py
python3 main.py
```

In Docker, see deploy

## Configuration

| Setting | What it is | Default |
|---|---|---|
| `INVENTORY_DB` | Path to the SQLite database file | `inventory.db` next to the code. In the container it is `/data/inventory.db`. |

## Run the tests

```
pytest -q
ruff check .
```

There are 40 tests. Each one gets an in-memory database loaded with the sample data.

## Database

Five STRICT tables, defined in `schema.sql`:

## Reports

What the sample data produces.

Stock value by supplier:

| Supplier | Stock value |
|---|---|
| Stanley Tools | 581.60 |
| Dulux Paints | 506.67 |
| Screwfix Supply | 404.00 |
| Draper | 343.93 |

Low stock:

| Product | Stock | Reorder level | Short by |
|---|---|---|---|
| Adjustable Wrench | 0 | 2 | 2 |
| Tape Measure 5m | 3 | 5 | 2 |
| Nails 500g | 10 | 10 | 0 |

Sales by product (top three of ten):

| Product | Units sold | Revenue |
|---|---|---|
| Cordless Drill | 1 | 79.99 |
| White Emulsion 5L | 2 | 49.98 |
| Claw Hammer | 3 | 37.97 |

The hammer sold at 11.99 in sale 1 and 12.99 in sale 5, revenue comes from the price on
each sale line.

Never sold: Adjustable Wrench, Hand Saw.

## What happens when a sale fails halfway

`record_sale` creates the sale, then for each line reads the current price, inserts the
line, reduces stock and logs a movement. All of it runs inside one `with connection:`,
so if a line fails the whole sale is rolled back.

This sale asks for 2 hammers (25 in stock) and 99 tape measures (3 in stock). The first line
succeeds, the second is refused by the `CHECK (quantity >= 0)` constraint on products:

```
Before: {'sales': 5, 'sale_items': 12, 'stock_movements': 0} {'HAM-001': 25, 'TAP-003': 3}
record_sale(connection, [(1, 2), (3, 99)]) raised IntegrityError: CHECK constraint failed: quantity >= 0
After:  {'sales': 5, 'sale_items': 12, 'stock_movements': 0} {'HAM-001': 25, 'TAP-003': 3}
```

No sale row, no lines, no movements, and the hammer is still at 25 even though its line had
already been written before the failure. The test `test_failed_sale_changes_nothing` checks
the same thing.

## Deploy

Build the image, seed the database into a volume, and run the menu:

```
docker build -t inventory:1.0.0 .
docker run --rm -v inventory-data:/data inventory:1.0.0 python seed_db.py
docker run -it --rm -v inventory-data:/data inventory:1.0.0
```

Build output:

```
 inventory-management-system % docker build -t inventory:1.0.0 .
[+] Building 0.4s (11/11) FINISHED                                                                      docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                    0.0s
 => => transferring dockerfile: 244B                                                                                    0.0s
 => [internal] load metadata for docker.io/library/python:3.12-slim                                                     0.3s
 => [internal] load .dockerignore                                                                                       0.0s
 => => transferring context: 129B                                                                                       0.0s
 => [1/6] FROM docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d  0.0s
 => => resolve docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d  0.0s
 => [internal] load build context                                                                                       0.0s
 => => transferring context: 644B                                                                                       0.0s
 => CACHED [2/6] WORKDIR /app                                                                                           0.0s
 => CACHED [3/6] COPY requirements.txt .                                                                                0.0s
 => CACHED [4/6] RUN pip install --no-cache-dir -r requirements.txt                                                     0.0s
 => CACHED [5/6] COPY . .                                                                                               0.0s
 => CACHED [6/6] RUN mkdir -p /data                                                                                     0.0s
 => exporting to image                                                                                                  0.0s
 => => exporting layers                                                                                                 0.0s
 => => exporting manifest sha256:bf840bd850f6e66f97126d814ab98806716a0c2e90cdd5abc635e8de53e51a3f                       0.0s
 => => exporting config sha256:53f4c092eadee800e2a5bcc870c3ced65a0212d928bc0daa2fd477cd69d96f88                         0.0s
 => => exporting attestation manifest sha256:cfacedf5ad92f5934add79632b9d39fbb156ef061b7f48766d41f076ff3615d9           0.0s
 => => exporting manifest list sha256:18f7d9fad8717f0b33803b84b7015d70062dcf5ced3cafc084b398339f7dcd3b                  0.0s
 => => naming to docker.io/library/inventory:1.0.0                                                                      0.0s
 => => unpacking to docker.io/library/inventory:1.0.0                                                                   0.0s
 ```

## Persistence check. One container restocks a product, a new container sees the change:
```
Inventory-management-system % docker run -it --rm -v inventory-data:/data inventory:1.0.0

Inventory
  1) Search products
  2) Look up a product
  3) Add a product
  4) Restock
  5) Record a sale
  6) Report: stock value by supplier
  7) Report: low stock
  8) Report: sales by product
  9) Report: never sold
  b) Back up the database
  q) Quit
Choose: 4
Product id: 3
Amount to add: 1
Done. Stock is now 4.

Inventory
  1) Search products
  2) Look up a product
  3) Add a product
  4) Restock
  5) Record a sale
  6) Report: stock value by supplier
  7) Report: low stock
  8) Report: sales by product
  9) Report: never sold
  b) Back up the database
  q) Quit
Choose: q
(.venv) Niraj.Pankhania@Nirajs-MacBook-Pro inventory-management-system % docker run -it --rm -v inventory-data:/data inventory:1.0.0

Inventory
  1) Search products
  2) Look up a product
  3) Add a product
  4) Restock
  5) Record a sale
  6) Report: stock value by supplier
  7) Report: low stock
  8) Report: sales by product
  9) Report: never sold
  b) Back up the database
  q) Quit
Choose: 2
Product id: 3
3. TAP-003 Tape Measure 5m (Tools) from Draper, 7.99, 4 in stock, reorder at 5
```
## Roll back

Both versions are tagged in Git (`v1.0.0`, `v1.1.0`). To go back to 1.0.0, stop and remove the running container and start the old image with the same volume. The data is in the volume, so it carries over:

```
docker stop inventory
docker rm inventory
docker run -it --name inventory -v inventory-data:/data inventory:1.0.0
```

Rollback output:

```
paste in
```

## Back up and restore

Choose `b` in the menu, or call `backup_database(source_path, backup_path)`.

Backup check: the copy passes `PRAGMA integrity_check` and has the same row counts as the
live database:

```
Inventory
  1) Search products
  2) Look up a product
  3) Add a product
  4) Restock
  5) Record a sale
  6) Report: stock value by supplier
  7) Report: low stock
  8) Report: sales by product
  9) Report: never sold
  b) Back up the database
  q) Quit
Choose: b
Backed up to /data/backups/inventory-2026-10-29.db

Inventory
  1) Search products
  2) Look up a product
  3) Add a product
  4) Restock
  5) Record a sale
  6) Report: stock value by supplier
  7) Report: low stock
  8) Report: sales by product
  9) Report: never sold
  b) Back up the database
  q) Quit
Choose: q
(.venv) Niraj.Pankhania@Nirajs-MacBook-Pro inventory-management-system % docker run --rm -v inventory-data:/data inventory:1.0.0 python -c "import sqlite3; c = sqlite3.connect('/data/backups/inventory-2026-10-29.db'); print(c.execute('PRAGMA integrity_check').fetchone()[0]); print([(t, c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]) for t in ['suppliers', 'products', 'sales', 'sale_items', 'stock_movements']])"

ok
[('suppliers', 4), ('products', 12), ('sales', 5), ('sale_items', 12), ('stock_movements', 1)]
```

To restore: stop the program, copy the backup file over the live database file, start again.

```
docker run --rm -v inventory-data:/data inventory:1.0.0 cp /data/backups/inventory-2026-10-29.db /data/inventory.db
```

## Self-review

- What I would do differently if I rebuilt it from scratch.
- One thing I am unsure about that I would want a reviewer to check.

i dont want to do this again :(

please check my sanity
