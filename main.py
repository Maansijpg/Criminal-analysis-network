from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from ws_manager import manager
from routers import auth_routes, cases, suspects, graph, sightings, alerts, transactions

app = FastAPI(title="Criminal Network Analysis - Demo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(cases.router)
app.include_router(suspects.router)
app.include_router(graph.router)
app.include_router(sightings.router)
app.include_router(alerts.router)
app.include_router(transactions.router)

@app.get("/")
def root():
    return {"status": "ok", "service": "crime-network-demo-api"}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)