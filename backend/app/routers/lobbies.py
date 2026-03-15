from fastapi import APIRouter, HTTPException, Cookie, Response, Request
from pydantic import BaseModel
from typing import Optional, List
import json

from app.lobby_manager import lobby_manager
from app.websocket import lobby_manager_ws

router = APIRouter(prefix="/api/lobbies", tags=["lobbies"])


class CreateLobbyRequest(BaseModel):
    code: str
    player_name: str


class JoinLobbyRequest(BaseModel):
    player_name: str


class ChatMessageRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: str
    player_name: str
    player_id: str
    message: str
    timestamp: str
    type: str


class LobbyResponse(BaseModel):
    code: str
    status: str
    player_count: int
    players: list
    you: Optional[dict] = None
    messages: Optional[List[ChatMessageResponse]] = None


@router.post("", response_model=LobbyResponse)
async def create_lobby(
    request: CreateLobbyRequest,
    response: Response
):
    """Create a new lobby."""
    # Check if lobby already exists
    if lobby_manager.lobby_exists(request.code):
        raise HTTPException(status_code=400, detail="Lobby already exists")
    
    # Create lobby
    lobby = lobby_manager.create_lobby(request.code)
    
    # Add first player (host)
    player = lobby_manager.join_lobby(request.code, request.player_name)
    
    # Set session cookie
    response.set_cookie(
        key=f"lobby_{request.code}",
        value=player.session_id,
        httponly=True,
        max_age=3600 * 24,  # 24 hours
        samesite="lax"
    )
    
    lobby_dict = lobby.to_dict()
    lobby_dict["you"] = {
        "id": player.id,
        "name": player.name,
        "is_host": player.is_host,
        "session_id": player.session_id,
    }
    
    return lobby_dict


@router.get("/{code}", response_model=LobbyResponse)
async def get_lobby(
    code: str,
    request: Request
):
    """Get lobby details."""
    lobby = lobby_manager.get_lobby(code)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")
    
    # Get session cookie dynamically
    cookie_name = f"lobby_{code}"
    lobby_session = request.cookies.get(cookie_name)
    
    lobby_dict = lobby.to_dict()
    
    # If user has a session, identify them
    if lobby_session:
        player = lobby.get_player_by_session(lobby_session)
        if player:
            lobby_dict["you"] = {
                "id": player.id,
                "name": player.name,
                "is_host": player.is_host,
                "session_id": player.session_id,
            }
    
    return lobby_dict


@router.post("/{code}/join", response_model=LobbyResponse)
async def join_lobby(
    code: str,
    request: JoinLobbyRequest,
    response: Response,
    http_request: Request
):
    """Join an existing lobby."""
    lobby = lobby_manager.get_lobby(code)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")
    
    if lobby.status != "waiting":
        raise HTTPException(status_code=400, detail="Game already in progress")
    
    # Get session cookie dynamically
    cookie_name = f"lobby_{code}"
    lobby_session = http_request.cookies.get(cookie_name)
    
    # Check for existing session (re-join case)
    if lobby_session:
        player = lobby_manager.get_player_by_session(code, lobby_session)
        if player:
            # Player exists with this session - allow re-join
            lobby_dict = lobby.to_dict()
            lobby_dict["you"] = {
                "id": player.id,
                "name": player.name,
                "is_host": player.is_host,
                "session_id": player.session_id,
            }
            # Include recent messages
            recent_messages = lobby.get_messages(50)
            lobby_dict["messages"] = [
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
            return lobby_dict
    
    # Check if name is taken by another player
    if lobby_manager.is_name_taken(code, request.player_name):
        raise HTTPException(status_code=409, detail=f"Name '{request.player_name}' is already taken")
    
    # Add player
    player = lobby_manager.join_lobby(code, request.player_name)
    if not player:
        raise HTTPException(status_code=400, detail="Failed to join lobby")
    
    # Add system message about player joining
    lobby.add_message("System", "system", f"{player.name} joined the lobby", "system")
    
    # Broadcast updated lobby state to all connected WebSocket clients
    import asyncio
    asyncio.create_task(
        lobby_manager_ws.broadcast_to_lobby(
            json.dumps({
                "type": "lobby_update",
                "data": lobby.to_dict()
            }),
            code
        )
    )
    
    # Set session cookie
    response.set_cookie(
        key=f"lobby_{code}",
        value=player.session_id,
        httponly=True,
        max_age=3600 * 24,
        samesite="lax"
    )
    
    lobby_dict = lobby.to_dict()
    lobby_dict["you"] = {
        "id": player.id,
        "name": player.name,
        "is_host": player.is_host,
        "session_id": player.session_id,
    }
    # Include recent messages for the joining player
    recent_messages = lobby.get_messages(50)
    lobby_dict["messages"] = [
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
    
    return lobby_dict


@router.get("/{code}/messages", response_model=List[ChatMessageResponse])
async def get_messages(
    code: str,
    http_request: Request,
    limit: int = 50
):
    """Get chat messages for a lobby."""
    # Get session cookie dynamically
    cookie_name = f"lobby_{code}"
    lobby_session = http_request.cookies.get(cookie_name)
    
    lobby = lobby_manager.get_lobby(code)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")
    
    messages = lobby.get_messages(limit)
    return [
        {
            "id": msg.id,
            "player_name": msg.player_name,
            "player_id": msg.player_id,
            "message": msg.message,
            "timestamp": msg.timestamp.isoformat(),
            "type": msg.type
        }
        for msg in messages
    ]


@router.post("/{code}/messages", response_model=ChatMessageResponse)
async def send_message(
    code: str,
    request: ChatMessageRequest,
    http_request: Request
):
    """Send a chat message to the lobby."""
    # Get session cookie dynamically
    cookie_name = f"lobby_{code}"
    lobby_session = http_request.cookies.get(cookie_name)
    
    lobby = lobby_manager.get_lobby(code)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")
    
    if not lobby_session:
        raise HTTPException(status_code=403, detail="Not authenticated")
    
    player = lobby.get_player_by_session(lobby_session)
    if not player:
        raise HTTPException(status_code=403, detail="Player not found in lobby")
    
    # Add message to lobby
    msg = lobby.add_message(player.name, player.id, request.message, "chat")
    
    return {
        "id": msg.id,
        "player_name": msg.player_name,
        "player_id": msg.player_id,
        "message": msg.message,
        "timestamp": msg.timestamp.isoformat(),
        "type": msg.type
    }


@router.post("/{code}/leave")
async def leave_lobby(
    code: str,
    http_request: Request
):
    """Leave a lobby."""
    # Get session cookie dynamically
    cookie_name = f"lobby_{code}"
    lobby_session = http_request.cookies.get(cookie_name)
    
    lobby = lobby_manager.get_lobby(code)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")
    
    if lobby_session:
        player = lobby.get_player_by_session(lobby_session)
        if player:
            # Add system message about player leaving
            lobby.add_message("System", "system", f"{player.name} left the lobby", "system")
            lobby_manager.leave_lobby(code, player.id)
            
            # Broadcast updated lobby state to all connected WebSocket clients
            import asyncio
            asyncio.create_task(
                lobby_manager_ws.broadcast_to_lobby(
                    json.dumps({
                        "type": "lobby_update",
                        "data": lobby.to_dict()
                    }),
                    code
                )
            )
    
    return {"message": "Left lobby successfully"}


@router.delete("/{code}")
async def delete_lobby(
    code: str,
    http_request: Request
):
    """Delete a lobby (host only)."""
    # Get session cookie dynamically
    cookie_name = f"lobby_{code}"
    lobby_session = http_request.cookies.get(cookie_name)
    
    lobby = lobby_manager.get_lobby(code)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")
    
    # Verify host
    if lobby_session:
        player = lobby.get_player_by_session(lobby_session)
        if not player or not player.is_host:
            raise HTTPException(status_code=403, detail="Only host can delete lobby")
    else:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    lobby_manager.delete_lobby(code)
    return {"message": "Lobby deleted successfully"}
