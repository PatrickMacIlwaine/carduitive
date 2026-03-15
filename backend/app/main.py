from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json

from app.database import engine, Base
from app.routers import counter, leaderboard, lobbies
from app.websocket import lobby_manager_ws
from app.lobby_manager import lobby_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="carduitive3 API",
    description="Backend API for carduitive3",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(counter.router)
app.include_router(leaderboard.router)
app.include_router(lobbies.router)


@app.websocket("/ws/lobby/{lobby_code}")
async def websocket_lobby(websocket: WebSocket, lobby_code: str):
    """WebSocket endpoint for lobby real-time communication."""
    # Check if lobby exists
    lobby = lobby_manager.get_lobby(lobby_code)
    if not lobby:
        await websocket.close(code=4000, reason="Lobby not found")
        return
    
    # Connect to lobby room
    await lobby_manager_ws.connect(websocket, lobby_code)
    
    try:
        # Send initial lobby state with chat history
        recent_messages = lobby.get_messages(50)
        await lobby_manager_ws.send_personal_message(
            json.dumps({
                "type": "connected",
                "lobby_code": lobby_code,
                "message": f"Connected to lobby {lobby_code}",
                "data": {
                    "messages": [
                        {
                            "id": msg.id,
                            "player_name": msg.player_name,
                            "player_id": msg.player_id,
                            "message": msg.message,
                            "timestamp": msg.timestamp.isoformat(),
                            "type": msg.type
                        }
                        for msg in recent_messages
                    ]
                }
            }),
            websocket
        )
        
        # Broadcast updated player list to all in lobby
        await lobby_manager_ws.broadcast_lobby_update(
            lobby_code,
            lobby.to_dict()
        )
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type", "chat")
                
                # Handle chat messages
                if msg_type == "chat" or "message" in message:
                    player_name = message.get("player_name", "Unknown")
                    player_id = message.get("player_id", "unknown")
                    msg_text = message.get("message", "")
                    
                    # Store message in lobby
                    stored_msg = lobby.add_message(player_name, player_id, msg_text, "chat")
                    
                    # Broadcast to all connected clients
                    await lobby_manager_ws.broadcast_to_lobby(
                        json.dumps({
                            "type": "chat",
                            "data": {
                                "id": stored_msg.id,
                                "player_name": stored_msg.player_name,
                                "player_id": stored_msg.player_id,
                                "message": stored_msg.message,
                                "timestamp": stored_msg.timestamp.isoformat(),
                                "type": stored_msg.type
                            }
                        }),
                        lobby_code
                    )
                else:
                    # Echo back other message types
                    await lobby_manager_ws.broadcast_to_lobby(
                        json.dumps({
                            "type": msg_type,
                            "data": message
                        }),
                        lobby_code
                    )
            except json.JSONDecodeError:
                await lobby_manager_ws.send_personal_message(
                    json.dumps({"type": "error", "message": "Invalid JSON"}),
                    websocket
                )
                
    except WebSocketDisconnect:
        lobby_manager_ws.disconnect(websocket)
        
        # Broadcast updated lobby state
        lobby = lobby_manager.get_lobby(lobby_code)
        if lobby:
            await lobby_manager_ws.broadcast_lobby_update(
                lobby_code,
                lobby.to_dict()
            )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
