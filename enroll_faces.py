import sys
import numpy as np
from pathlib import Path
from database import get_conn
from face_utils import encode_face_from_image, embedding_to_json

def enroll_folder(root: Path, conn):
    for suspect_dir in sorted(root.iterdir()):
        if not suspect_dir.is_dir():
            continue
        suspect_id = suspect_dir.name
        row = conn.execute(
            "SELECT name FROM suspects WHERE suspect_id = ?", (suspect_id,)
        ).fetchone()
        if not row:
            print(f"  skip {suspect_id}: no matching suspect in DB")
            continue

        photos = sorted(suspect_dir.glob("*.jpg")) + sorted(suspect_dir.glob("*.jpeg")) + sorted(suspect_dir.glob("*.png"))
        embeddings = []
        for photo in photos:
            enc = encode_face_from_image(str(photo))
            if enc is None:
                print(f"    no face found in {photo.name}, skipping")
                continue
            embeddings.append(enc)

        if not embeddings:
            print(f"  {suspect_id} ({row['name']}): no usable photos, skipped")
            continue

        avg_embedding = np.mean(embeddings, axis=0)
        conn.execute(
            "UPDATE suspects SET face_embedding = ? WHERE suspect_id = ?",
            (embedding_to_json(avg_embedding), suspect_id),
        )
        print(f"  {suspect_id} ({row['name']}): enrolled from {len(embeddings)} photo(s)")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 enroll_faces.py <folder_of_suspect_photos>")
        sys.exit(1)
    conn = get_conn()
    enroll_folder(Path(sys.argv[1]), conn)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()