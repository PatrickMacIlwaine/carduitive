from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import json
import asyncio

from app.database import engine, Base
from app.config import get_settings
from app.routers import counter, leaderboard, lobbies, auth
from app.websocket import lobby_manager_ws
from app.lobby_manager import lobby_manager

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    heartbeat_task = asyncio.create_task(lobby_manager_ws.heartbeat(interval=10))
    yield
    heartbeat_task.cancel()


app = FastAPI(
    title="carduitive API",
    description="Backend API for carduitive",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    # Trust proxy headers from Ingress for correct HTTPS redirect URIs
    root_path="" if settings.environment == "development" else "",
)

# Session middleware for OAuth
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=3600 * 24 * 7,  # 7 days
)

# CORS - same-origin in production, allow localhost in dev
cors_origins = [
    "http://localhost:5173",
    "http://localhost:8000",
]
if settings.environment == "production":
    cors_origins = [
        settings.frontend_url,  # https://carduitive.com
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(counter.router)
app.include_router(leaderboard.router)
app.include_router(lobbies.router)
app.include_router(auth.router)


@app.websocket("/ws/lobby/{lobby_code}")
async def websocket_lobby(websocket: WebSocket, lobby_code: str):
    """WebSocket endpoint for lobby real-time communication."""
    # Check if lobby exists
    lobby = lobby_manager.get_lobby(lobby_code)
    if not lobby:
        await websocket.close(code=4000, reason="Lobby not found")
        return
    
    # Get session from cookies to identify player
    cookies = websocket.cookies
    session_cookie_name = f"lobby_{lobby_code}"
    session_id = cookies.get(session_cookie_name)
    
    # Find player by session
    player_id = None
    player_name = "Unknown"
    if session_id:
        player = lobby.get_player_by_session(session_id)
        if player:
            player_id = player.id
            player_name = player.name
    
    # Connect to lobby room with player tracking
    await lobby_manager_ws.connect(websocket, lobby_code, player_id)
    
    try:
        # Send initial lobby state with chat history
        recent_messages = lobby.get_messages(50)
        await lobby_manager_ws.send_personal_message(
            json.dumps({
                "type": "connected",
                "lobby_code": lobby_code,
                "player_id": player_id,
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
                    ],
                    "connected_players": lobby_manager_ws.get_connected_players(lobby_code)
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
                    sender_name = message.get("player_name", player_name)
                    sender_id = message.get("player_id", player_id or "unknown")
                    msg_text = message.get("message", "")
                    
                    # Store message in lobby
                    stored_msg = lobby.add_message(sender_name, sender_id, msg_text, "chat")
                    
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
        
        # Notify game that player disconnected (for auto-play logic)
        if player_id:
            lobby_manager.handle_player_disconnect(lobby_code, player_id)
        
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
