import random
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from ws_manager import manager

router = APIRouter(prefix="/transactions", tags=["transactions"])

class SimulateTransaction(BaseModel):
    case_id: Optional[str] = None
    suspect_a_id: Optional[str] = None
    suspect_b_id: Optional[str] = None
    amount: Optional[float] = None

def fake_account_for(suspect_id: str) -> str:
    return f"ACC{abs(hash(suspect_id)) % 10**8:08d}"

@router.post("/simulate")
async def simulate_transaction(body: SimulateTransaction, conn=Depends(get_db)):
    if body.suspect_a_id and body.suspect_b_id:
        a = conn.execute("SELECT * FROM suspects WHERE suspect_id = ?", (body.suspect_a_id,)).fetchone()
        b = conn.execute("SELECT * FROM suspects WHERE suspect_id = ?", (body.suspect_b_id,)).fetchone()
        if not a or not b:
            raise HTTPException(status_code=404, detail="Suspect not found")
        case_id = a["case_id"]
    else:
        case_id = body.case_id
        if not case_id:
            case_id = conn.execute("SELECT case_id FROM cases ORDER BY RANDOM() LIMIT 1").fetchone()["case_id"]
        pair = conn.execute(
            "SELECT suspect_id, name FROM suspects WHERE case_id = ? ORDER BY RANDOM() LIMIT 2", (case_id,)
        ).fetchall()
        if len(pair) < 2:
            raise HTTPException(status_code=400, detail="This case needs at least 2 suspects to simulate a transaction")
        a, b = pair[0], pair[1]

    amount = body.amount if body.amount is not None else round(random.uniform(500, 75000), 2)
    txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    ts = datetime.now(timezone.utc).isoformat()
    acct_a, acct_b = fake_account_for(a["suspect_id"]), fake_account_for(b["suspect_id"])

    conn.execute(
        "INSERT INTO transactions (txn_id, suspect_id, account_no, counterparty_acct, amount, timestamp) VALUES (?,?,?,?,?,?)",
        (txn_id, a["suspect_id"], acct_a, acct_b, amount, ts),
    )

    already_linked = conn.execute(
        "SELECT 1 FROM connections WHERE case_id = ? AND relation_type = 'shared_transaction' AND "
        "((suspect_a_id = ? AND suspect_b_id = ?) OR (suspect_a_id = ? AND suspect_b_id = ?))",
        (case_id, a["suspect_id"], b["suspect_id"], b["suspect_id"], a["suspect_id"]),
    ).fetchone()

    if not already_linked:
        conn.execute(
            "INSERT INTO connections (connection_id, case_id, suspect_a_id, suspect_b_id, relation_type, evidence_ref) "
            "VALUES (?,?,?,?,?,?)",
            (f"CONN-{uuid.uuid4().hex[:8].upper()}", case_id, a["suspect_id"], b["suspect_id"], "shared_transaction", txn_id),
        )
    conn.commit()

    payload = {"txn_id": txn_id, "from_suspect": a["name"], "to_suspect": b["name"], "amount": amount, "timestamp": ts}
    await manager.broadcast({"type": "transaction", "transaction": payload})
    if not already_linked:
        await manager.broadcast({
            "type": "graph_update", "action": "add_edge", "case_id": case_id,
            "edge": {"source": a["suspect_id"], "target": b["suspect_id"], "relation": "shared_transaction"},
        })

    return payload