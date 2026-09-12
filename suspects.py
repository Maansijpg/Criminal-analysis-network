import random
import io
import uuid
from typing import Optional, List
import numpy as np
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from database import get_db, rows_to_dicts
from ws_manager import manager
import face_recognition
from face_utils import load_known_embeddings, find_best_match, encode_face_from_bytes, embedding_to_json

router = APIRouter(prefix="/suspects", tags=["suspects"])

@router.get("/")
def list_suspects(case_id: Optional[str] = None, conn=Depends(get_db)):
    if case_id:
        rows = conn.execute("SELECT * FROM suspects WHERE case_id = ? ORDER BY name", (case_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM suspects ORDER BY name").fetchall()
    return rows_to_dicts(rows)

@router.get("/{suspect_id}")
def get_suspect(suspect_id: str, conn=Depends(get_db)):
    suspect = conn.execute("SELECT * FROM suspects WHERE suspect_id = ?", (suspect_id,)).fetchone()
    if not suspect:
        raise HTTPException(status_code=404, detail="Suspect not found")
    vehicles = conn.execute("SELECT * FROM vehicles WHERE suspect_id = ?", (suspect_id,)).fetchall()
    calls = conn.execute("SELECT * FROM calls WHERE suspect_id = ? ORDER BY timestamp DESC LIMIT 20", (suspect_id,)).fetchall()
    transactions = conn.execute("SELECT * FROM transactions WHERE suspect_id = ? ORDER BY timestamp DESC LIMIT 20", (suspect_id,)).fetchall()
    sightings = conn.execute(
        "SELECT sg.*, c.location_name FROM sightings sg JOIN cameras c ON c.camera_id = sg.camera_id "
        "WHERE sg.suspect_id = ? ORDER BY sg.timestamp DESC LIMIT 20", (suspect_id,)
    ).fetchall()
    return {
        "suspect": dict(suspect),
        "vehicles": rows_to_dicts(vehicles),
        "calls": rows_to_dicts(calls),
        "transactions": rows_to_dicts(transactions),
        "sightings": rows_to_dicts(sightings),
    }

@router.post("/with-photos")
async def add_suspect_with_photos(
    case_id: str = Form(...),
    name: str = Form(...),
    alias: Optional[str] = Form(None),
    aadhar_ref: str = Form(...),
    dob: Optional[str] = Form(None),
    status: str = Form("under_watch"),
    photos: List[UploadFile] = File(...),
    conn=Depends(get_db),
):
    if not conn.execute("SELECT 1 FROM cases WHERE case_id = ?", (case_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Case not found")

    suspect_id = f"SUS-{uuid.uuid4().hex[:8].upper()}"
    face_id = f"identity_{random.randint(1, 15):03d}"

    embeddings = []
    for photo in photos:
        contents = await photo.read()
        enc = encode_face_from_bytes(contents)
        if enc is not None:
            embeddings.append(enc)

    face_embedding_json = embedding_to_json(np.mean(embeddings, axis=0)) if embeddings else None

    conn.execute(
        "INSERT INTO suspects (suspect_id, case_id, name, alias, face_id, aadhar_ref, dob, status, photo_ref, face_embedding) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (suspect_id, case_id, name, alias, face_id, aadhar_ref, dob, status, f"{face_id}.jpg", face_embedding_json),
    )

    others = conn.execute("SELECT suspect_id FROM suspects WHERE case_id = ? AND suspect_id != ?", (case_id, suspect_id)).fetchall()
    new_edges = []
    for o in others:
        conn.execute(
            "INSERT INTO connections (connection_id, case_id, suspect_a_id, suspect_b_id, relation_type, evidence_ref) VALUES (?,?,?,?,?,?)",
            (f"CONN-{uuid.uuid4().hex[:8].upper()}", case_id, suspect_id, o["suspect_id"], "same_case", case_id),
        )
        new_edges.append({"source": suspect_id, "target": o["suspect_id"], "relation": "same_case"})
    conn.commit()

    await manager.broadcast({"type": "graph_update", "action": "add_node", "case_id": case_id, "node": {"id": suspect_id, "name": name, "status": status}})
    for edge in new_edges:
        await manager.broadcast({"type": "graph_update", "action": "add_edge", "case_id": case_id, "edge": edge})

    return {"suspect_id": suspect_id, "name": name, "enrolled_photos": len(embeddings), "face_ready": face_embedding_json is not None}

@router.delete("/{suspect_id}")
async def delete_suspect(suspect_id: str, conn=Depends(get_db)):
    suspect = conn.execute("SELECT * FROM suspects WHERE suspect_id = ?", (suspect_id,)).fetchone()
    if not suspect:
        raise HTTPException(status_code=404, detail="Suspect not found")
    case_id = suspect["case_id"]
    sighting_ids = [r["sighting_id"] for r in conn.execute("SELECT sighting_id FROM sightings WHERE suspect_id = ?", (suspect_id,)).fetchall()]
    for sid in sighting_ids:
        conn.execute("DELETE FROM alerts WHERE sighting_id = ?", (sid,))
    conn.execute("DELETE FROM alerts WHERE suspect_id = ?", (suspect_id,))
    conn.execute("DELETE FROM sightings WHERE suspect_id = ?", (suspect_id,))
    conn.execute("DELETE FROM transactions WHERE suspect_id = ?", (suspect_id,))
    conn.execute("DELETE FROM calls WHERE suspect_id = ?", (suspect_id,))
    conn.execute("DELETE FROM vehicles WHERE suspect_id = ?", (suspect_id,))
    conn.execute("DELETE FROM connections WHERE suspect_a_id = ? OR suspect_b_id = ?", (suspect_id, suspect_id))
    conn.execute("DELETE FROM suspects WHERE suspect_id = ?", (suspect_id,))
    conn.commit()
    await manager.broadcast({"type": "graph_update", "action": "remove_node", "case_id": case_id, "node": {"id": suspect_id}})
    return {"deleted": suspect_id}

@router.post("/search-photo")
async def search_by_photo(file: UploadFile = File(...), conn=Depends(get_db)):
    contents = await file.read()
    image = face_recognition.load_image_file(io.BytesIO(contents))
    encodings = face_recognition.face_encodings(image)
    if not encodings:
        return {"matched": False, "message": "No face detected in the uploaded photo"}
    known = load_known_embeddings(conn)
    match, confidence = find_best_match(encodings[0], known)
    if not match:
        return {"matched": False, "message": "No matching identity found"}
    suspect = conn.execute("SELECT * FROM suspects WHERE suspect_id = ?", (match["suspect_id"],)).fetchone()
    return {"matched": True, "confidence": confidence, "suspect": dict(suspect)}