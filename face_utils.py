import io
import json
import numpy as np
import face_recognition

def encode_face_from_image(image_path):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    if not encodings:
        return None
    return encodings[0]

def encode_face_from_bytes(image_bytes: bytes):
    image = face_recognition.load_image_file(io.BytesIO(image_bytes))
    encodings = face_recognition.face_encodings(image)
    return encodings[0] if encodings else None

def embedding_to_json(embedding: np.ndarray) -> str:
    return json.dumps(embedding.tolist())

def embedding_from_json(text: str) -> np.ndarray:
    return np.array(json.loads(text))

def load_known_embeddings(conn):
    rows = conn.execute(
        "SELECT suspect_id, name, case_id, face_embedding FROM suspects WHERE face_embedding IS NOT NULL"
    ).fetchall()
    return [
        {"suspect_id": r["suspect_id"], "name": r["name"], "case_id": r["case_id"], "embedding": embedding_from_json(r["face_embedding"])}
        for r in rows
    ]

def find_best_match(embedding, known, tolerance=0.55):
    if not known:
        return None, None
    known_encodings = [k["embedding"] for k in known]
    distances = face_recognition.face_distance(known_encodings, embedding)
    best_index = int(np.argmin(distances))
    best_distance = distances[best_index]
    if best_distance > tolerance:
        return None, None
    confidence = round(max(0.0, 1 - best_distance), 2)
    return known[best_index], confidence