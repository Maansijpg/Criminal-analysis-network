from pathlib import Path
from database import get_conn
from face_utils import load_known_embeddings
from camera_watcher import watch_video

FOOTAGE_DIR = Path("cctv_footage")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv")

CAMERA_LOCATIONS = ["Main entrance", "Parking lot", "Back gate", "Hallway", "Reception"]

def register_cameras(conn, count):
    for i in range(count):
        camera_id = f"CAM-{i+1:03d}"
        location = CAMERA_LOCATIONS[i] if i < len(CAMERA_LOCATIONS) else f"Camera {i+1}"
        conn.execute(
            "INSERT OR IGNORE INTO cameras (camera_id, location_name, lat, lon) VALUES (?,?,?,?)",
            (camera_id, location, 12.9716, 77.5946),
        )
    conn.commit()

def main():
    videos = sorted(p for p in FOOTAGE_DIR.iterdir() if p.suffix.lower() in VIDEO_EXTENSIONS)
    if not videos:
        print(f"No video files found in {FOOTAGE_DIR}/")
        return

    conn = get_conn()
    register_cameras(conn, len(videos))
    known = load_known_embeddings(conn)
    print(f"Loaded {len(known)} enrolled face(s). Found {len(videos)} video(s).\n")

    for i, video_path in enumerate(videos):
        camera_id = f"CAM-{i+1:03d}"
        print(f"--- Playing {video_path.name} as {camera_id} ---")
        watch_video(str(video_path), camera_id, known)
        print()

    print("All videos processed.")

if __name__ == "__main__":
    main()