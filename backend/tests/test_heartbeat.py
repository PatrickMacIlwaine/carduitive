"""
Tests for the WebSocket heartbeat / periodic connection status broadcast.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.websocket import LobbyConnectionManager


def make_mock_ws():
    """Create a mock WebSocket that tracks sent messages. Set ws._open = False to simulate disconnect."""
    ws = MagicMock()
    ws._sent = []
    ws._open = True

    async def send_text(msg):
        if not ws._open:
            raise Exception("WebSocket disconnected")
        ws._sent.append(msg)

    ws.send_text = AsyncMock(side_effect=send_text)
    ws.accept = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_heartbeat_broadcasts_connection_update():
    """Heartbeat should broadcast connection_update to all active lobbies."""
    mgr = LobbyConnectionManager()
    ws1 = make_mock_ws()
    ws2 = make_mock_ws()

    await mgr.connect(ws1, "LOBBY1", "p1")
    await mgr.connect(ws2, "LOBBY1", "p2")

    # Clear messages from connect broadcasts
    ws1._sent.clear()
    ws2._sent.clear()

    # Manually call broadcast_connection_update (what heartbeat calls)
    await mgr.broadcast_connection_update("LOBBY1")

    # Both clients should receive a connection_update
    assert len(ws1._sent) == 1
    assert len(ws2._sent) == 1

    msg1 = json.loads(ws1._sent[0])
    assert msg1["type"] == "connection_update"
    assert set(msg1["connected_players"]) == {"p1", "p2"}


@pytest.mark.asyncio
async def test_heartbeat_detects_dead_connections():
    """Heartbeat broadcast should detect and clean up dead WebSocket connections."""
    mgr = LobbyConnectionManager()
    ws_alive = make_mock_ws()
    ws_dead = make_mock_ws()

    await mgr.connect(ws_alive, "LOBBY1", "p1")
    await mgr.connect(ws_dead, "LOBBY1", "p2")

    assert mgr.is_player_connected("LOBBY1", "p2") is True

    # Simulate ws_dead going away (browser close, network loss)
    ws_dead._open = False
    ws_alive._sent.clear()

    # Broadcasting should fail for ws_dead and clean it up
    await mgr.broadcast_connection_update("LOBBY1")

    # p2 should be removed from connected players
    assert mgr.is_player_connected("LOBBY1", "p2") is False
    assert mgr.is_player_connected("LOBBY1", "p1") is True

    # The alive client should eventually receive an update with only p1
    # (first the failed broadcast, then the cleanup re-broadcast)
    last_msg = json.loads(ws_alive._sent[-1])
    assert last_msg["type"] == "connection_update"
    assert last_msg["connected_players"] == ["p1"]


@pytest.mark.asyncio
async def test_heartbeat_skips_empty_lobbies():
    """Heartbeat should not fail when a lobby has no connections."""
    mgr = LobbyConnectionManager()
    # No lobbies — heartbeat iteration should be a no-op
    lobby_codes = list(mgr.lobby_connections.keys())
    assert lobby_codes == []
    # Calling broadcast_connection_update on a nonexistent lobby should be safe
    await mgr.broadcast_connection_update("NONEXISTENT")


@pytest.mark.asyncio
async def test_heartbeat_multiple_lobbies():
    """Heartbeat should broadcast to all active lobbies independently."""
    mgr = LobbyConnectionManager()
    ws1 = make_mock_ws()
    ws2 = make_mock_ws()

    await mgr.connect(ws1, "LOBBY_A", "p1")
    await mgr.connect(ws2, "LOBBY_B", "p2")

    ws1._sent.clear()
    ws2._sent.clear()

    # Simulate what heartbeat does: iterate all lobbies
    lobby_codes = list(mgr.lobby_connections.keys())
    for code in lobby_codes:
        await mgr.broadcast_connection_update(code)

    # Each client gets an update for their lobby only
    assert len(ws1._sent) == 1
    assert len(ws2._sent) == 1

    msg1 = json.loads(ws1._sent[0])
    assert msg1["connected_players"] == ["p1"]

    msg2 = json.loads(ws2._sent[0])
    assert msg2["connected_players"] == ["p2"]


@pytest.mark.asyncio
async def test_heartbeat_cleans_up_fully_dead_lobby():
    """If all connections in a lobby are dead, heartbeat should clean up the lobby entirely."""
    mgr = LobbyConnectionManager()
    ws_dead = make_mock_ws()

    await mgr.connect(ws_dead, "LOBBY1", "p1")

    assert "LOBBY1" in mgr.lobby_connections

    # Simulate connection dying
    ws_dead._open = False

    # Broadcasting will fail for the dead connection and clean it up
    await mgr.broadcast_connection_update("LOBBY1")

    # Lobby should be fully cleaned up
    assert "LOBBY1" not in mgr.lobby_connections
    assert mgr.is_player_connected("LOBBY1", "p1") is False


@pytest.mark.asyncio
async def test_heartbeat_loop_runs_and_cancels():
    """The heartbeat coroutine should run periodically and cancel cleanly."""
    mgr = LobbyConnectionManager()
    ws = make_mock_ws()

    await mgr.connect(ws, "LOBBY1", "p1")
    ws._sent.clear()

    # Run heartbeat with a very short interval
    task = asyncio.create_task(mgr.heartbeat(interval=0.05))

    # Wait enough for at least 2 heartbeats
    await asyncio.sleep(0.15)
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass

    # Should have received multiple connection_update messages
    updates = [json.loads(m) for m in ws._sent if json.loads(m)["type"] == "connection_update"]
    assert len(updates) >= 2, f"Expected at least 2 heartbeat broadcasts, got {len(updates)}"
