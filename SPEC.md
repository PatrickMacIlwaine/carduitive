# Carduitive - Technical Specification

## Project Overview

- **Project Name**: Carduitive
- **Type**: Public Web Application - Multiplayer Card Game
- **Core Functionality**: Real-time multiplayer card game with lobbies, leaderboards, and WebSocket support
- **Target Users**: General public users playing in groups/teams

---

## Technology Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.x | UI Framework |
| React Router | 6.x | Client-side routing |
| Vite | 5.x | Build Tool |
| Tailwind CSS | 3.x | Styling |
| TypeScript | 5.x | Type Safety |
| shadcn/ui | Latest | UI Components |
| Lucide React | Latest | Icons |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11 | Runtime |
| FastAPI | 0.109.x | Web Framework |
| SQLAlchemy | 2.x | ORM |
| asyncpg | 0.29.x | PostgreSQL Driver |
| Uvicorn | 0.27.x | ASGI Server |
| Pydantic | 2.x | Data Validation |

### Database
| Technology | Purpose |
|------------|---------|
| PostgreSQL (Cloud SQL) | Primary Database |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| GKE Autopilot | Kubernetes Orchestration |
| Cloud SQL Auth Proxy | Secure DB Connection |
| GitHub Actions | CI/CD |

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Browser 1     │  │   Browser 2     │  │   Browser N     │              │
│  │  (Player: Alice)│  │  (Player: Bob) │  │  (Player: Carol)│              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
│           │                      │                      │                  │
│           ▼                      ▼                      ▼                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      React SPA (Single Page App)                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │  WebSocket   │  │   HTTP API   │  │   UI State   │               │   │
│  │  │  Connection  │  │   Client     │  │   Management │               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP / WebSocket
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            APPLICATION LAYER                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Backend Server                            │   │
│  │                                                                      │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │   │
│  │  │   HTTP Router   │  │  WebSocket      │  │  In-Memory State    │  │   │
│  │  │   (/api/*)      │  │  Handler        │  │  Manager            │  │   │
│  │  │                 │  │  (/ws/lobby/*)  │  │                     │  │   │
│  │  │  - Lobbies      │  │                 │  │  - Lobby Instances  │  │   │
│  │  │  - Leaderboard  │  │  - Broadcast    │  │  - Player Sessions  │  │   │
│  │  │  - Counter      │  │  - Room Mgmt    │  │  - Chat Messages    │  │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ SQL
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    PostgreSQL Database                               │   │
│  │                                                                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │   │
│  │  │   counter   │  │ leaderboard   │  │   players (lobby state)   │  │   │
│  │  │   table     │  │   table      │  │   [IN-MEMORY ONLY]        │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Session Management Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SESSION LIFECYCLE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. CREATE LOBBY                                                 │
│     ┌─────────┐         ┌─────────┐         ┌─────────┐       │
│     │ Client  │ ──────▶ │  POST   │ ──────▶ │ Cookie  │       │
│     │         │         │/lobbies  │         │lobby_ABC│       │
│     │         │         │         │         │=sess_123│       │
│     │         │ ◀────── │  200    │ ◀────── │ (Set)   │       │
│     │         │         │+you data │         │         │       │
│     └─────────┘         └─────────┘         └─────────┘       │
│                                                                  │
│  2. JOIN EXISTING LOBBY                                          │
│     ┌─────────┐         ┌─────────┐         ┌─────────┐       │
│     │ Client  │ ──────▶ │  POST   │ ──────▶ │ Cookie  │       │
│     │         │         │/ABCD/join│         │lobby_ABC│       │
│     │         │         │+name    │         │=sess_456│       │
│     │         │ ◀────── │  200    │ ◀────── │ (Set)   │       │
│     │         │         │+you data │         │         │       │
│     └─────────┘         └─────────┘         └─────────┘       │
│                                                                  │
│  3. RE-JOIN (same browser)                                       │
│     ┌─────────┐         ┌─────────┐                             │
│     │ Client  │ ──────▶ │  POST   │                             │
│     │         │         │/ABCD/join│                             │
│     │  Cookie │ ──────▶ │ (Cookie │ ──────▶ │  Find   │          │
│     │sess_123 │         │sent)    │         │ player  │          │
│     │         │ ◀────── │  200    │ ◀────── │ by sess │          │
│     │         │         │+you data│         │         │          │
│     └─────────┘         └─────────┘                             │
│                                                                  │
│  4. WEBSOCKET CONNECT                                            │
│     ┌─────────┐         ┌─────────┐         ┌─────────┐       │
│     │ Client  │ ──────▶ │   WS    │ ──────▶ │ Cookie  │       │
│     │         │         │Connect  │         │Checked  │       │
│     │         │         │/ABCD    │         │         │       │
│     │         │ ◀────── │  Chat   │ ◀────── │ History │       │
│     │         │         │ History │         │ Loaded  │       │
│     └─────────┘         └─────────┘         └─────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Real-Time Communication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              WEBSOCKET BROADCAST ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SCENARIO: New Player Joins                                     │
│                                                                  │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐  │
│  │  Bob    │     │  Alice  │     │  Carol  │     │ Server  │  │
│  │(Joining)│     │(In Lobby│     │(In Lobby│     │         │  │
│  └────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘  │
│       │               │               │               │        │
│       │  1. POST /join│               │               │        │
│       │ ─────────────▶│               │               │        │
│       │               │               │               │        │
│       │               │               │               │2. Add   │
│       │               │               │               │  Player │
│       │               │               │               │        │
│       │               │3. Broadcast lobby_update        │        │
│       │               │◀──────────────│◀──────────────│        │
│       │               │               │               │        │
│       │               │4. Update player │               │        │
│       │               │   list (3     │               │        │
│       │               │   players)    │               │        │
│       │               │               │               │        │
│       │5. 200 OK      │               │               │        │
│       │◀──────────────│               │               │        │
│       │ +you data     │               │               │        │
│       │               │               │               │        │
│       │6. WS Connect  │               │               │        │
│       │ ─────────────────────────────▶│               │        │
│       │               │               │               │        │
│       │7. Chat History│              │               │        │
│       │◀──────────────│               │               │        │
│       │               │               │               │        │
│                                                                  │
│  KEY PRINCIPLE:                                                  │
│  - HTTP response includes 'you' field ONLY for joining player   │
│  - WebSocket broadcasts do NOT include 'you' field              │
│  - Each client preserves their own 'you' identity               │
│  - All clients receive same player list update                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

#### Frontend State Management

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     LobbyPage.tsx                            ││
│  │                     (Container)                            ││
│  │                                                              ││
│  │  ┌────────────────────────────────────────────────────────┐ ││
│  │  │  useLobby(lobbyCode)                                   │ ││
│  │  │  ─────────────────                                    │ ││
│  │  │  • lobby: Lobby | null                                 │ ││
│  │  │  • messages: ChatMessage[]                             │ ││
│  │  │  • wsConnected: boolean                                │ ││
│  │  │  • loading: boolean                                    │ ││
│  │  │  • error: string | null                                │ ││
│  │  │                                                          │ ││
│  │  │  Methods:                                              │ ││
│  │  │  • joinLobby(name) → HTTP POST + WS connect           │ ││
│  │  │  • createLobby(name) → HTTP POST + WS connect          │ ││
│  │  │  • leaveLobby() → HTTP POST + WS disconnect          │ ││
│  │  │  • sendChatMessage(msg) → WS emit                    │ ││
│  │  │                                                          │ ││
│  │  │  WebSocket Handlers:                                   │ ││
│  │  │  • onLobbyUpdate(data) → Merge players, preserve 'you'│ ││
│  │  │  • onPlayerJoined(name) → Add system message           │ ││
│  │  │  • onChat(data) → Append message (deduplicated)       │ ││
│  │  └────────────────────────────────────────────────────────┘ ││
│  │                                                              ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      ││
│  │  │PlayerList    │  │  LobbyChat   │  │HostControls  │      ││
│  │  │  Component   │  │  Component   │  │  Component   │      ││
│  │  │              │  │              │  │              │      ││
│  │  │ Props:       │  │ Props:       │  │ Props:       │      ││
│  │  │ • players    │  │ • messages   │  │ • isHost     │      ││
│  │  │ • you        │  │ • onSend     │  │ • playerCount│      ││
│  │  │ • count      │  │ • disabled   │  │              │      ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘      ││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                 JoinLobbyForm.tsx                            ││
│  │                    (Conditional)                             ││
│  │                                                              ││
│  │  Shows when: lobby === null || !lobby.you                   ││
│  │                                                              ││
│  │  Props:                                                     ││
│  │  • lobbyCode                                                ││
│  │  • isNewLobby (404 on GET)                                 ││
│  │  • onJoin(name)                                            ││
│  │  • onCreate(name)                                          ││
│  │  • error                                                   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Backend Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   FastAPI Application                      ││
│  │                      (main.py)                             ││
│  │                                                              ││
│  │  ┌────────────────────────────────────────────────────────┐││
│  │  │                 HTTP Router Layer                        │││
│  │  │              (app/routers/lobbies.py)                  │││
│  │  │                                                          │││
│  │  │  POST /api/lobbies                                     │││
│  │  │  ├── Create lobby                                      │││
│  │  │  ├── Add first player (host)                           │││
│  │  │  ├── Set session cookie                                │││
│  │  │  └── Return: lobby + you + messages                   │││
│  │  │                                                          │││
│  │  │  POST /api/lobbies/{code}/join                        │││
│  │  │  ├── Check existing session (re-join)                │││
│  │  │  ├── Check name uniqueness                            │││
│  │  │  ├── Add player to lobby                              │││
│  │  │  ├── Set session cookie                               │││
│  │  │  ├── Broadcast WS: lobby_update                       │││
│  │  │  └── Return: lobby + you + messages                   │││
│  │  │                                                          │││
│  │  │  POST /api/lobbies/{code}/leave                       │││
│  │  │  ├── Remove player                                    │││
│  │  │  ├── Broadcast WS: lobby_update                       │││
│  │  │  └── Return: success                                  │││
│  │  │                                                          │││
│  │  │  GET  /api/lobbies/{code}/messages                    │││
│  │  │  └── Return: chat history                             │││
│  │  └────────────────────────────────────────────────────────┘││
│  │                                                              ││
│  │  ┌────────────────────────────────────────────────────────┐││
│  │  │               WebSocket Handler                        │││
│  │  │              (/ws/lobby/{code})                        │││
│  │  │                                                          │││
│  │  │  on_connect():                                         ││││
│  │  │  ├── Validate lobby exists                            │││
│  │  │  ├── Send: connected + chat history                   │││
│  │  │  └── Broadcast: lobby_update (all players)            │││
│  │  │                                                          │││
│  │  │  on_message():                                        │││
│  │  │  ├── Store chat message                                │││
│  │  │  └── Broadcast: chat (all players)                    │││
│  │  │                                                          │││
│  │  │  on_disconnect():                                      │││
│  │  │  └── Broadcast: lobby_update (updated list)           │││
│  │  └────────────────────────────────────────────────────────┘││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              In-Memory State (app/lobby_manager.py)         ││
│  │                                                              ││
│  │  LobbyManager                                                ││
│  │  ├── _lobbies: Dict[str, Lobby]                            ││
│  │  ├── create_lobby(code)                                    ││
│  │  ├── get_lobby(code)                                       ││
│  │  ├── join_lobby(code, name)                                ││
│  │  ├── leave_lobby(code, player_id)                          ││
│  │  ├── is_name_taken(code, name, exclude_session)            ││
│  │  └── get_player_by_session(code, session_id)               ││
│  │                                                              ││
│  │  Lobby                                                       ││
│  │  ├── code: str                                              ││
│  │  ├── players: List[Player]                                   ││
│  │  ├── messages: List[ChatMessage]                            ││
│  │  ├── status: str                                            ││
│  │  ├── add_player(name, is_host)                             ││
│  │  ├── remove_player(player_id)                                ││
│  │  ├── add_message(...)                                       ││
│  │  ├── get_messages(limit)                                   ││
│  │  └── to_dict()  [NO session_ids, NO you field]            ││
│  │                                                              ││
│  │  Player                                                      ││
│  │  ├── id: str (UUID)                                         ││
│  │  ├── name: str                                              ││
│  │  ├── is_host: bool                                         ││
│  │  ├── session_id: str (UUID, cookie value)                  ││
│  │  └── joined_at: datetime                                    ││
│  │                                                              ││
│  │  ChatMessage                                                ││
│  │  ├── id: str                                                ││
│  │  ├── player_name: str                                      ││
│  │  ├── player_id: str                                        ││
│  │  ├── message: str                                          ││
│  │  ├── timestamp: datetime                                   ││
│  │  └── type: str (chat/system)                               ││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Examples

#### Flow 1: Creating a Lobby

```
┌─────────┐         ┌─────────┐         ┌─────────┐         ┌─────────┐
│ Client  │         │ Vite    │         │ FastAPI │         │ Memory  │
└────┬────┘         └────┬────┘         └────┬────┘         └────┬────┘
     │                   │                   │                   │
     │ 1. POST /lobbies  │                   │                   │
     │ {code, name}      │                   │                   │
     │ ─────────────────▶│                   │                   │
     │                   │ 2. Proxy to       │                   │
     │                   │    localhost:8000 │                   │
     │                   │ ─────────────────▶│                   │
     │                   │                   │ 3. Create lobby   │
     │                   │                   │    instance       │
     │                   │                   │ ────────────────▶│
     │                   │                   │                   │4. Store
     │                   │                   │                   │
     │                   │                   │ 5. Add player     │
     │                   │                   │    (host)         │
     │                   │                   │ 6. Set cookie     │
     │                   │                   │    lobby_ABC=123  │
     │                   │                   │ 7. Return JSON    │
     │                   │                   │    +you data      │
     │                   │ ◀────────────────│                   │
     │                   │ 8. Proxy back     │                   │
     │ 9. Receive        │                   │                   │
     │    lobby+you      │                   │                   │
     │◀─────────────────│                   │                   │
     │                   │                   │                   │
     │ 10. WS connect    │                   │                   │
     │    /ws/ABC        │                   │                   │
     │ ─────────────────────────────────────▶                   │
     │                   │                   │ 11. Accept WS    │
     │                   │                   │    connection    │
     │                   │                   │ 12. Send chat    │
     │                   │                   │    history       │
     │ 13. Receive       │                   │                   │
     │     history       │                   │                   │
     │◀──────────────────────────────────────│                   │
     │                   │                   │                   │
```

#### Flow 2: Multi-Player Join with Real-Time Sync

```
┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│  Alice    │  │    Bob    │  │   Carol   │  │   Server  │  │   Lobby   │
│ (In Game) │  │  (Joining)│  │ (In Game) │  │           │  │  (Memory) │
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
      │              │              │              │              │
      │              │ 1. POST /join│              │              │
      │              │ {name: Bob}  │              │              │
      │              │ ────────────▶│              │              │
      │              │              │ 2. Check     │              │
      │              │              │    session   │              │
      │              │              │ 3. Check     │              │
      │              │              │    name OK   │              │
      │              │              │ 4. Add Bob   │              │
      │              │              │ ────────────▶│              │
      │              │              │              │5. Update    │
      │              │              │              │   player list│
      │              │              │              │◀─────────────│
      │              │              │ 6. Broadcast │              │
      │              │              │    WS:       │              │
      │              │              │    lobby_    │              │
      │              │              │    update    │              │
      │ 7. Receive   │              │              │              │
      │    WS update │◀─────────────│◀─────────────│              │
      │              │              │              │              │
      │ 8. UI shows  │              │ 8. UI shows  │              │
      │    3 players │              │    3 players │              │
      │              │              │              │              │
      │              │ 9. HTTP      │              │              │
      │              │    200 OK    │              │              │
      │              │    +you data │              │              │
      │              │◀─────────────│              │              │
      │              │              │              │              │
      │              │ 10. WS       │              │              │
      │              │     connect  │              │              │
      │              │ ───────────────────────────▶              │
      │              │              │              │              │
      │ 11. WS:      │ 11. WS:      │              │              │
      │     Bob      │     Bob      │              │              │
      │     joined!  │     joined!  │              │              │
      │◀─────────────│◀─────────────│              │              │
```

### Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **In-memory lobbies** | Lobbies are ephemeral game sessions. Data loss on restart is acceptable. Fast, no DB latency. |
| **HTTP cookies for session** | Simple, works across page reloads, no JWT complexity needed for this use case |
| **No `you` in WebSocket broadcasts** | Prevents "join form flashing" when other players join. Each client maintains own identity. |
| **Case-insensitive names** | Prevents confusion ("Alice" vs "alice" treated as same) |
| **Re-join support** | Players can refresh or reconnect without losing their place/name in the lobby |
| **Name uniqueness per lobby** | Prevents impersonation, clear player identification |
| **Chat history in lobby** | All players see same context when joining. Stored with lobby (ephemeral). |
| **WebSocket for real-time, HTTP for actions** | Best of both: WebSocket for push updates, HTTP for reliable request/response |

---

## Design System

### Color Palette
| Color | Hex | Usage |
|-------|-----|-------|
| Primary Dark | `#09637E` | Buttons, active states |
| Primary Light | `#7AB2B2` | Accents, hover states |
| Teal | `#088395` | Links, icons |
| Off-White | `#EBF4F6` | Light mode backgrounds |
| Dark BG | `#0F172A` | Dark mode backgrounds |

### Features
- **Dark Mode**: Full support with persistent user preference
- **Responsive Design**: Mobile-first approach
- **Component Library**: Custom shadcn/ui components

---

## Frontend Routing

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | Navigate to /home | Root redirect |
| `/home` | HomePage | Lobby entry - New Game / Join Game |
| `/leaderboard` | LeaderboardPage | Global high scores |
| `/lobby/:lobbyCode` | LobbyPage | Game room (5-letter code) |

---

## API Specification

### REST Endpoints

#### Counter (Demo Endpoint)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/counter` | Get current counter value |
| POST | `/api/counter/increment` | Increment counter by 1 |

#### Leaderboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/leaderboard` | Get top leaderboard entries (sorted by score) |
| POST | `/api/leaderboard` | Create or update leaderboard entry |
| GET | `/api/leaderboard/stats` | Get leaderboard statistics |
| GET | `/api/leaderboard/{id}` | Get specific entry by ID |

**POST /api/leaderboard** Request Body:
```json
{
  "group_name": "string (required)",
  "score": "integer (required)",
  "games_played": "integer (default: 1)"
}
```

**Note**: If `group_name` already exists, the score and games_played will be added to the existing entry.

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/lobby/{lobby_code}` | WebSocket connection for lobby real-time updates |

#### WebSocket Message Protocol

**Message Types:**

| Type | Direction | Description |
|------|-----------|-------------|
| `connected` | Server → Client | Sent when client connects. Includes chat history |
| `player_joined` | Server → Client | Broadcast when a new player joins |
| `player_left` | Server → Client | Broadcast when a player leaves |
| `lobby_update` | Server → Client | Broadcast when player list changes (NO `you` field) |
| `chat` | Client ↔ Server | Chat messages |

**Important Design Note:**
- WebSocket broadcasts ONLY include player list, NOT the `you` field
- Each client determines their own identity via their session cookie
- This prevents "join form flashing" when new players join

**Connected Message (Initial Load):**
```json
{
  "type": "connected",
  "lobby_code": "ABCDE",
  "message": "Connected to lobby ABCDE",
  "data": {
    "messages": [
      {
        "id": "uuid",
        "player_name": "Player1",
        "player_id": "uuid",
        "message": "Hello!",
        "timestamp": "2026-03-15T16:00:00",
        "type": "chat"
      }
    ]
  }
}
```

**Player Joined Broadcast:**
```json
{
  "type": "player_joined",
  "player_name": "Player2",
  "timestamp": "2026-03-15T16:05:00"
}
```

**Lobby Update (Player List Only):**
```json
{
  "type": "lobby_update",
  "data": {
    "code": "ABCDE",
    "status": "waiting",
    "player_count": 2,
    "players": [
      {"id": "uuid", "name": "Player1", "is_host": true, "joined_at": "..."},
      {"id": "uuid", "name": "Player2", "is_host": false, "joined_at": "..."}
    ],
    "created_at": "2026-03-15T16:00:00",
    "updated_at": "2026-03-15T16:05:00"
  }
}
```
**Note:** No `you` field in broadcast. Each client knows their own identity via cookie.

**Chat Message:**
```json
{
  "type": "chat",
  "data": {
    "id": "uuid",
    "player_name": "Player1",
    "player_id": "uuid",
    "message": "Hello everyone!",
    "timestamp": "2026-03-15T16:10:00",
    "type": "chat"
  }
}
```

### Swagger Documentation
- Available at: `/docs`
- ReDoc available at: `/redoc`

---

## Database Schema

### Table: counter

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (always 1, singleton) |
| value | INTEGER | Current counter value |
| updated_at | TIMESTAMP | Last update time |

### Table: leaderboard

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| group_name | VARCHAR(100) | Team/group name (indexed, unique) |
| score | INTEGER | Total score accumulated |
| games_played | INTEGER | Number of games completed |
| updated_at | TIMESTAMP | Last update time (auto-updates) |

---

## Local Development

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker (for database)
- psql (PostgreSQL client) - `brew install libpq`

### Quick Start - Local Development

#### 1. Start the Database
```bash
# Start PostgreSQL in Docker
docker run -d \
  --name carduitive3-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=carduitive3 \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:16-alpine

# Verify it's running
docker ps
```

#### 2. Start the Backend
```bash
cd backend

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the server
./start.sh
```
Backend will be available at: http://localhost:8000
API docs at: http://localhost:8000/docs

#### 3. Start the Frontend
```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start the dev server
npm start
```
Frontend will be available at: http://localhost:5173

### Alternative: Docker Compose (All Services)
If you prefer to run everything in Docker:
```bash
docker compose up --build
```
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Database: localhost:5432

### Development URLs
| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React + Vite app |
| Backend API | http://localhost:8000 | FastAPI endpoints |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Database | localhost:5432 | PostgreSQL |

### Database Commands

**Connect to psql:**
```bash
docker exec -it carduitive3-db psql -U postgres -d carduitive3
```

**Common psql commands:**
- `\dt` - List all tables
- `\d leaderboard` - Describe leaderboard table
- `SELECT * FROM leaderboard;` - View leaderboard data
- `\q` - Quit psql

### Stopping Services
```bash
# Stop backend (Ctrl+C in the terminal)

# Stop frontend (Ctrl+C in the terminal)

# Stop database
docker stop carduitive3-db
```

---

## Project Structure

### Frontend
```
frontend/src/
├── components/
│   ├── ui/                      # shadcn components
│   │   ├── button.tsx           # Button variants
│   │   ├── input.tsx            # Text input
│   │   ├── card.tsx             # Card container
│   │   └── alert.tsx            # Alert/Error messages
│   ├── layout/                  # Layout components
│   │   ├── MainLayout.tsx       # App shell with navbar
│   │   └── Navbar.tsx           # Top navigation + theme toggle
│   └── lobby/                   # Lobby-specific components
│       ├── JoinLobbyForm.tsx    # Name input form (join/create)
│       ├── PlayerList.tsx       # Display players with host badges
│       └── LobbyChat.tsx        # Real-time chat interface
├── pages/
│   ├── HomePage.tsx             # Landing with New/Join Game options
│   ├── LeaderboardPage.tsx      # High scores display
│   └── LobbyPage.tsx            # Main game lobby (composite of components)
├── hooks/
│   ├── useTheme.ts              # Dark mode management
│   └── lobby/
│       └── useLobby.ts          # Main lobby state + WebSocket hook
├── types/
│   └── lobby.ts                 # TypeScript types (Player, Lobby, ChatMessage)
├── lib/
│   └── utils.ts                 # cn() helper for Tailwind classes
├── App.tsx                      # Router configuration
└── main.tsx                     # React entry point
```

### Backend
```
backend/
├── app/
│   ├── main.py                  # FastAPI app factory + WebSocket endpoint
│   ├── models.py                # SQLAlchemy DB models (Counter, Leaderboard)
│   ├── database.py              # Async PostgreSQL connection
│   ├── lobby_manager.py         # In-memory lobby + player + chat management
│   ├── websocket.py             # WebSocket connection manager (room-based)
│   └── routers/
│       ├── counter.py           # Demo counter API
│       ├── leaderboard.py       # Leaderboard CRUD
│       └── lobbies.py          # Lobby HTTP API + chat endpoints
├── init_db.py                   # Database initialization script
├── start.sh                     # Development startup script
├── requirements.txt             # Python dependencies
└── Dockerfile                   # Container config
```

### Key Files by Function

| File | Purpose |
|------|---------|
| `frontend/src/hooks/lobby/useLobby.ts` | Main hook managing lobby state, WebSocket, HTTP API |
| `backend/app/lobby_manager.py` | In-memory data structures (Lobby, Player, ChatMessage classes) |
| `backend/app/routers/lobbies.py` | HTTP endpoints for lobby CRUD + chat |
| `backend/app/main.py` | WebSocket endpoint + HTTP-to-WS broadcast bridge |
| `backend/app/websocket.py` | Room-based WebSocket connection manager |

---

## Kubernetes Configuration

### Components
- **Frontend Deployment**: React app served via nginx
- **Backend Deployment**: FastAPI application
- **Service**: Internal load balancer for backend
- **Ingress**: External HTTPS entry point
- **Cloud SQL Proxy**: Sidecar for database connection

---

## CI/CD Pipeline

### GitHub Actions Workflow
1. **Lint & Test**: Run linting and tests
2. **Build**: Build Docker images
3. **Deploy to GKE**: Deploy to Autopilot cluster

---

## Environment Variables

### Backend
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Application secret key |

### Frontend
| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API URL |

---

## Security Considerations

- Cloud SQL Auth Proxy for secure database access
- Non-root containers in Kubernetes
- Secrets managed via Kubernetes secrets
- HTTPS via GKE Ingress

---

## Future Enhancements

- User authentication (OAuth2/JWT)
- Real-time game state synchronization via WebSockets
- Game logic implementation (card dealing, turns, scoring)
- Lobby management (player join/leave, game start)
- Advanced leaderboard features (filters, time ranges)
- Monitoring and logging (Cloud Monitoring, Cloud Logging)
