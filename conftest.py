from pathlib import Path

import pytest

import inventory_db
import sample_data

PROJECT_FOLDER = Path(__file__).parent

@pytest.fixture
def connection():
    """in memory db with the schema and sample data for each test"""
    con = inventory_db.connect(":memory:")
    con.executescript((PROJECT_FOLDER / "schema.sql").read_text(encoding="utf-8"))
    sample_data.load_sample_data(con)
    yield con
    con.close()
