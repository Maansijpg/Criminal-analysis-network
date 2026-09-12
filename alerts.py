from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from database import get_db, rows_to_dicts

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/")
def list_alerts(status: Optional[str] = None, conn=Depends(get_db)):
    sql = (
        "SELECT a.*, s.name AS suspect_name, s.case_id, cam.location_name "
        "FROM alerts a "
        "JOIN suspects s ON s.suspect_id = a.suspect_id "
        "LEFT JOIN sightings sg ON sg.sighting_id = a.sighting_id "
        "LEFT JOIN cameras cam ON cam.camera_id = sg.camera_id "
    )
    params = ()
    if status:
        sql += "WHERE a.status = ? "
        params = (status,)
    sql += "ORDER BY a.created_at DESC LIMIT 50"
    return rows_to_dicts(conn.execute(sql, params).fetchall())

@router.patch("/{alert_id}")
def update_alert(alert_id: str, status: str, conn=Depends(get_db)):
    if status not in ("new", "acknowledged", "resolved"):
        raise HTTPException(status_code=400, detail="Invalid status")
    conn.execute("UPDATE alerts SET status = ? WHERE alert_id = ?", (status, alert_id))
    conn.commit()
    return {"alert_id": alert_id, "status": status}