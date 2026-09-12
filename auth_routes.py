import hashlib
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    police_id: str
    password: str

@router.post("/login")
def login(body: LoginRequest, conn=Depends(get_db)):
    row = conn.execute(
        "SELECT * FROM police_users WHERE police_id = ?", (body.police_id,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Unknown police ID")
    hashed = hashlib.sha256(body.password.encode()).hexdigest()
    if hashed != row["password_hash"]:
        raise HTTPException(status_code=401, detail="Incorrect password")
    return {"police_id": row["police_id"], "name": row["name"], "station": row["station"]}