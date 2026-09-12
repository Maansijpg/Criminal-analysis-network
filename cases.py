from fastapi import APIRouter, Depends
from database import get_db, rows_to_dicts

router = APIRouter(prefix="/cases", tags=["cases"])

@router.get("/")
def list_cases(conn=Depends(get_db)):
    rows = conn.execute(
        "SELECT c.*, COUNT(s.suspect_id) AS suspect_count "
        "FROM cases c LEFT JOIN suspects s ON s.case_id = c.case_id "
        "GROUP BY c.case_id ORDER BY c.created_at DESC"
    ).fetchall()
    return rows_to_dicts(rows)

@router.get("/{case_id}")
def get_case(case_id: str, conn=Depends(get_db)):
    row = conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    return dict(row) if row else {}