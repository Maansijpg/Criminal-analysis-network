from fastapi import APIRouter, Depends
from database import get_db

router = APIRouter(prefix="/graph", tags=["graph"])

@router.get("/{case_id}")
def get_graph(case_id: str, conn=Depends(get_db)):
    suspects = conn.execute("SELECT * FROM suspects WHERE case_id = ?", (case_id,)).fetchall()
    connections = conn.execute("SELECT * FROM connections WHERE case_id = ?", (case_id,)).fetchall()
    nodes = [{"id": s["suspect_id"], "name": s["name"], "status": s["status"]} for s in suspects]
    links = [
        {"source": c["suspect_a_id"], "target": c["suspect_b_id"], "relation": c["relation_type"]}
        for c in connections
    ]
    return {"nodes": nodes, "links": links}