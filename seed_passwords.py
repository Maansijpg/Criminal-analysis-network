import sqlite3
import hashlib
from pathlib import Path

DB_PATH = Path(__file__).parent / "crime_network.db"
DEMO_PASSWORD = "demo123"

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    new_hash = hashlib.sha256(DEMO_PASSWORD.encode()).hexdigest()
    cur.execute("UPDATE police_users SET password_hash = ?", (new_hash,))
    conn.commit()
    print(f"Password reset to '{DEMO_PASSWORD}' for all officers:")
    for row in cur.execute("SELECT police_id, name, station FROM police_users"):
        print(f"  {row[0]}  {row[1]}  ({row[2]})")
    conn.close()

if __name__ == "__main__":
    main()