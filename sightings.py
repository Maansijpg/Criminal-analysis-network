import random
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from ws_manager import manager

router = APIRouter(prefix="/sightings", tags=["sightings"])
ALERT_THRESHOLD = 0.50

class NewSighting(BaseModel):
    suspect_id: Optional[str] = None
    camera_id: Optional[str] = None
    confidence: Optional[float] = None

@router.post("/")
async def create_sighting(body: NewSighting, conn=Depends(get_db)):
    suspect_id = body.suspect_id
    if not suspect_id:
        row = conn.execute("SELECT suspect_id FROM suspects ORDER BY RANDOM() LIMIT 1").fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No suspects in DB")
        suspect_id = row["suspect_id"]

    camera_id = body.camera_id
    if not camera_id:
        camera_id = conn.execute("SELECT camera_id FROM cameras ORDER BY RANDOM() LIMIT 1").fetchone()["camera_id"]

    confidence = body.confidence if body.confidence is not None else round(random.uniform(0.55, 0.99), 2)
    sighting_id = f"SGT-{uuid.uuid4().hex[:8].upper()}"
    ts = datetime.now(timezone.utc).isoformat()

    conn.execute(
        "INSERT INTO sightings (sighting_id, suspect_id, camera_id, timestamp, confidence) VALUES (?,?,?,?,?)",
        (sighting_id, suspect_id, camera_id, ts, confidence),
    )
    suspect = conn.execute("SELECT name FROM suspects WHERE suspect_id = ?", (suspect_id,)).fetchone()
    camera = conn.execute("SELECT location_name FROM cameras WHERE camera_id = ?", (camera_id,)).fetchone()

    alert = None
    if confidence >= ALERT_THRESHOLD:
        alert_id = f"ALR-{uuid.uuid4().hex[:8].upper()}"
        conn.execute(
            "INSERT INTO alerts (alert_id, suspect_id, sighting_id, status, created_at) VALUES (?,?,?,?,?)",
            (alert_id, suspect_id, sighting_id, "new", ts),
        )
        alert = {
            "alert_id": alert_id,
            "suspect_id": suspect_id,
            "suspect_name": suspect["name"],
            "camera_location": camera["location_name"],
            "confidence": confidence,
            "timestamp": ts,
        }
    conn.commit()

    sighting_payload = {
        "sighting_id": sighting_id,
        "suspect_id": suspect_id,
        "suspect_name": suspect["name"],
        "camera_location": camera["location_name"],
        "confidence": confidence,
        "timestamp": ts,
    }
    await manager.broadcast({"type": "sighting", "sighting": sighting_payload})
    if alert:
        await manager.broadcast({"type": "alert", "alert": alert})

    return {**sighting_payload, "alert": alert}