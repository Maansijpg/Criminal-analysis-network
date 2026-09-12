import sys
import time
import cv2
import requests
import face_recognition
from database import get_conn
from face_utils import load_known_embeddings, find_best_match

API_URL = "http://localhost:8000/sightings/"
FRAME_SKIP = 15
CONFIDENCE_THRESHOLD = 0.55
COOLDOWN_SECONDS = 10

def watch_video(source, camera_id, known):
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Could not open video source: {source}")
        return

    frame_count = 0
    last_reported = {}

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_count += 1
        if frame_count % FRAME_SKIP != 0:
            continue

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
                resp = requests.post(API_URL, json={
                    "suspect_id": match["suspect_id"],
                    "camera_id": camera_id,
                    "confidence": confidence,
                })
                data = resp.json()
                tag = "ALERT" if data.get("alert") else "sighting"
                print(f"  [{camera_id}] [{tag}] {match['name']} detected (confidence {confidence})")
            except requests.RequestException as e:
                print("  Could not reach backend:", e)

        cv2.imshow(f"Camera feed: {camera_id} (press q to skip)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 camera_watcher.py <video_path_or_0> <camera_id>")
        sys.exit(1)
    source = sys.argv[1]
    camera_id = sys.argv[2]
    source = 0 if source == "0" else source

    conn = get_conn()
    known = load_known_embeddings(conn)
    print(f"Loaded {len(known)} enrolled face(s).")
    watch_video(source, camera_id, known)

if __name__ == "__main__":
    main()