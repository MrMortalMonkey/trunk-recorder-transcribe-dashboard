from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import asyncio

app = FastAPI()

connected_clients = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    print(f"Client connected. Total: {len(connected_clients)}")

    try:
        while True:
            await asyncio.sleep(60)  # keep connection alive
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print(f"Client disconnected. Total: {len(connected_clients)}")

@app.post("/broadcast")
async def broadcast(data: dict):
    print(f"Broadcasting to {len(connected_clients)} clients")

    dead = set()

    for client in connected_clients:
        try:
            await client.send_json(data)
        except:
            dead.add(client)

    for d in dead:
        connected_clients.remove(d)

    return JSONResponse({"status": "sent"})
