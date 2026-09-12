from database import get_conn

conn = get_conn()
conn.execute(
    "INSERT OR IGNORE INTO cameras (camera_id, location_name, lat, lon) VALUES (?,?,?,?)",
    ("CAM-001", "Team webcam - entrance angle", 12.9716, 77.5946),
)
conn.commit()
print("Camera added (or already existed).")