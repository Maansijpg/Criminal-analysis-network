import sys
import time
import warnings
import itertools
warnings.filterwarnings("ignore")

import cv2
import requests
import face_recognition
from pathlib import Path
from database import get_conn
from face_utils import load_known_embeddings, find_best_match

API_URL = "http://localhost:8000/sightings/"
FRAME_SKIP = 15
CONFIDENCE_THRESHOLD = 0.55
COOLDOWN_SECONDS = 10

GREEN, RED, DIM, BOLD, RESET = "\033[92m", "\033[91m", "\033[2m", "\033[1m", "\033[0m"

def get_or_create_camera(conn, location_hint):
    n = conn.execute("SELECT COUNT(*) AS n FROM cameras").fetchone()["n"]
    camera_id = f"CAM-{n + 1:03d}"
    conn.execute(
        "INSERT OR IGNORE INTO cameras (camera_id, location_name, lat, lon) VALUES (?,?,?,?)",
        (camera_id, location_hint, 12.9716, 77.5946),
    )
    conn.commit()
    return camera_id

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 watch.py <video_path_or_0> [\"Camera location\"]")
        sys.exit(1)

    source = sys.argv[1]
    default_name = "Live Camera" if source == "0" else Path(source).stem.replace("_", " ").title()
    location_hint = sys.argv[2] if len(sys.argv) > 2 else default_name
    source = 0 if source == "0" else source

    conn = get_conn()
    camera_id = get_or_create_camera(conn, location_hint)
    known = load_known_embeddings(conn)

    print(f"\n{BOLD}📹  Watching: {location_hint}  ({camera_id}){RESET}")
    print(f"{DIM}   {len(known)} enrolled face(s) loaded. Press 'q' in the video window to stop.{RESET}\n")

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"{RED}Could not open video source: {source}{RESET}")
        sys.exit(1)

    frame_count, last_reported = 0, {}
    spinner = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_count += 1

        if frame_count % FRAME_SKIP != 0:
            print(f"\r{DIM}{next(spinner)} scanning...{RESET}", end="", flush=True)
        else:
            small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb_small)
            encodings = face_recognition.face_encodings(rgb_small, locations)

            for encoding in encodings:
                match, confidence = find_best_match(encoding, known, tolerance=CONFIDENCE_THRESHOLD)
                if not match:
                    continue
                now = time.time()
                if now - last_reported.get(match["suspect_id"], 0) < COOLDOWN_SECONDS:
                    continue
                last_reported[match["suspect_id"]] = now
                try:
                    resp = requests.post(API_URL, json={"suspect_id": match["suspect_id"], "camera_id": camera_id, "confidence": confidence})
                    data = resp.json()
                    if data.get("alert"):
                        print(f"\r{GREEN}{BOLD}🚨 ALERT — {match['name']} spotted at {location_hint} ({int(confidence*100)}% match){RESET}          ")
                    else:
                        print(f"\r{DIM}   sighting — {match['name']} ({int(confidence*100)}% match, below alert threshold){RESET}          ")
                except requests.RequestException:
                    print(f"\r{RED}Could not reach backend — is uvicorn running?{RESET}")

        cv2.imshow(f"{location_hint}  (press q to stop)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n{BOLD}Done watching {location_hint}.{RESET}\n")

if __name__ == "__main__":
    main()