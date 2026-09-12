import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "crime_network.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_db():
    conn = get_conn()
    try:
        yield conn
    finally:
        conn.close()

def rows_to_dicts(rows):
    return [dict(r) for r in rows]