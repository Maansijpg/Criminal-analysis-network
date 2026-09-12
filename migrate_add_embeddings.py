import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "crime_network.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cols = [r[1] for r in cur.execute("PRAGMA table_info(suspects)").fetchall()]
    if "face_embedding" not in cols:
        cur.execute("ALTER TABLE suspects ADD COLUMN face_embedding TEXT")
        conn.commit()
        print("Added face_embedding column to suspects table.")
    else:
        print("face_embedding column already exists.")
    conn.close()

if __name__ == "__main__":
    main()