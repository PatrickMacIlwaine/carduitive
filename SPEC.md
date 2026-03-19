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
| Framer Motion | Latest | Card animations and game board transitions |

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
| GKE Standard (single e2-micro node) | Kubernetes Orchestration |
| NodePort + nginx proxy | Traffic routing (no LoadBalancer cost) |
| Cloudflare | SSL termination and DNS |
| GCP Artifact Registry | Docker image storage |
| GCP Secret Manager | Secrets management |
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
│  │  │  • countdown: number | null                            │ ││
│  │  │  • isStarting: boolean                                 │ ││
│  │  │                                                          │ ││
│  │  │  Methods:                                              │ ││
│  │  │  • joinLobby(name) → HTTP POST + WS connect           │ ││
│  │  │  • createLobby(name) → HTTP POST + WS connect          │ ││
│  │  │  • leaveLobby() → HTTP POST + WS disconnect          │ ││
│  │  │  • sendChatMessage(msg) → WS emit                    │ ││
│  │  │  • startGame() → HTTP POST /start                     │ ││
│  │  │  • playCard(card) → HTTP POST /action {play}          │ ││
│  │  │  • advanceLevel() → HTTP POST /action {advance}       │ ││
│  │  │  • restartLevel() → HTTP POST /action {restart}       │ ││
│  │  │                                                          │ ││
│  │  │  WebSocket Handlers:                                   │ ││
│  │  │  • onLobbyUpdate(data) → Merge players, preserve 'you'│ ││
│  │  │  • onConnectionUpdate → Update player connected status │ ││
│  │  │  • onPlayerJoined(name) → Add system message           │ ││
│  │  │  • onChat(data) → Append message (deduplicated)       │ ││
│  │  │  • onCountdown(count) → Show countdown overlay        │ ││
│  │  │  • onGameStarted(data) → Transition to game board     │ ││
│  │  │  • onGameUpdate(data) → Update shared game state      │ ││
│  │  │  • onLevelStarted(data) → Fetch fresh state (private) │ ││
│  │  └────────────────────────────────────────────────────────┘ ││
│  │                                                              ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      ││
│  │  │PlayerList    │  │  LobbyChat   │  │HostControls  │      ││
│  │  │  Component   │  │  Component   │  │  Component   │      ││
│  │  │              │  │              │  │              │      ││
│  │  │ Props:       │  │ Props:       │  │ Props:       │      ││
│  │  │ • players    │  │ • messages   │  │ • isHost     │      ││
│  │  │ • you        │  │ • onSend     │  │ • playerCount│      ││
│  │  │ • count      │  │ • disabled   │  │ • connectedCount     ││
│  │  │              │  │ • mode       │  │ • isStarting │      ││
│  │  │              │  │   (inline/   │  │ • onStartGame│      ││
│  │  │              │  │    overlay)  │  │              │      ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘      ││
│  │                                                              ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      ││
│  │  │  GameBoard   │  │ GameResults  │  │CountdownOvly │      ││
│  │  │  Component   │  │  (Overlay)   │  │  Component   │      ││
│  │  │              │  │              │  │              │      ││
│  │  │ Shows when:  │  │ Shows when:  │  │ Shows when:  │      ││
│  │  │ isPlaying    │  │ success/fail │  │ countdown    │      ││
│  │  │              │  │              │  │ != null      │      ││
│  │  │ Fanned card  │  │ Per-player   │  │              │      ││
│  │  │ hand + back- │  │ card reveal  │  │ 3-2-1 timer  │      ││
│  │  │ face others  │  │ + actions    │  │              │      ││
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
│  │  ├── join_lobby(code, name, user_id, avatar_url, ...)      ││
│  │  ├── leave_lobby(code, player_id)                          ││
│  │  ├── start_game(code, game_type, config)                   ││
│  │  ├── handle_game_action(code, player_id, action, data)     ││
│  │  ├── get_game_state(code, player_id?)                      ││
│  │  ├── handle_player_reconnect(code, player_id)              ││
│  │  ├── is_name_taken(code, name)                             ││
│  │  └── get_player_by_session(code, session_id)               ││
│  │                                                              ││
│  │  Lobby                                                       ││
│  │  ├── code: str                                              ││
│  │  ├── players: List[Player]                                   ││
│  │  ├── messages: List[ChatMessage]                            ││
│  │  ├── status: str (waiting/starting/playing/ended)           ││
│  │  ├── game: Game | None  (active game instance)             ││
│  │  ├── current_level: int | None                             ││
│  │  ├── game_type: str | None                                 ││
│  │  ├── countdown: int | None                                 ││
│  │  ├── add_player(name, is_host)                             ││
│  │  ├── remove_player(player_id)                               ││
│  │  ├── add_message(...)                                       ││
│  │  ├── get_messages(limit)                                   ││
│  │  └── to_dict(player_id?)  [NO session_ids, NO you field]  ││
│  │                                                              ││
│  │  Player                                                      ││
│  │  ├── id: str (UUID)                                         ││
│  │  ├── name: str                                              ││
│  │  ├── is_host: bool                                         ││
│  │  ├── session_id: str (UUID, cookie value)                  ││
│  │  ├── avatar_url: str | None                                ││
│  │  ├── is_authenticated: bool                                ││
│  │  ├── user_id: int | None                                   ││
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
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Game Engine (app/games/)                       ││
│  │                                                              ││
│  │  Game (ABC - base.py)                                       ││
│  │  ├── lobby_code, players, status, config                   ││
│  │  ├── start_game(config) → public_state                     ││
│  │  ├── handle_action(player_id, action, data) → state        ││
│  │  ├── get_public_state() → shared state (no private cards)  ││
│  │  ├── get_player_state(player_id) → state + my_hand         ││
│  │  └── log_action(type, player_id, data)                     ││
│  │                                                              ││
│  │  ClassicCarduitive (classic.py)                            ││
│  │  Cooperative ascending-order card game                     ││
│  │  ├── deal_cards(level) → N cards per player from 1-100    ││
│  │  ├── play(player_id, card) → validate + check win/fail     ││
│  │  │   Rule: must play the globally lowest card remaining    ││
│  │  ├── advance() → increment level, re-deal                  ││
│  │  └── restart() → re-deal same level                        ││
│  │                                                              ││
│  │  GameStatus: SETUP | WAITING | PLAYING | SUCCESS |         ││
│  │              FAILED | COMPLETED                             ││
│  │                                                              ││
│  │  Public state: level, played_cards, last_played,           ││
│  │    next_expected, player_hands (card_count only),           ││
│  │    status, attempts, progression                            ││
│  │  Private state (per player): adds my_hand.cards            ││
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

See `STYLES.md` for the full design system documentation including color palette, typography, spacing, component styles, dark mode implementation, game board aesthetics, and Framer Motion animation patterns.

### Summary
- **Color Palette**: Teal/blue-green primary (`#09637E`), light teal accents (`#7AB2B2`), dark navy backgrounds in dark mode
- **Dark Mode**: Class-based (`.dark` on `<html>`), persisted to localStorage, respects `prefers-color-scheme`
- **Responsive**: Mobile-first with `sm:`, `md:`, `lg:` breakpoints
- **Component Library**: shadcn/ui base components + custom game board components
- **Animations**: Framer Motion for game interactions (card hover, deal-in, overlays)

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

#### Lobbies
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/lobbies` | Create a new lobby |
| GET | `/api/lobbies/{code}` | Get lobby details (includes `you` if session cookie present) |
| POST | `/api/lobbies/{code}/join` | Join an existing lobby |
| POST | `/api/lobbies/{code}/leave` | Leave a lobby |
| DELETE | `/api/lobbies/{code}` | Delete a lobby (host only) |
| GET | `/api/lobbies/{code}/messages` | Get chat message history |
| POST | `/api/lobbies/{code}/messages` | Send a chat message (HTTP fallback) |
| POST | `/api/lobbies/{code}/start` | Start game with 3-2-1 countdown (host only) |
| POST | `/api/lobbies/{code}/action` | Perform a game action (play/pass/advance/restart) |
| GET | `/api/lobbies/{code}/game-state` | Get current game state including private hand |

**POST /api/lobbies/{code}/start** Request Body:
```json
{
  "game_type": "classic",
  "config": {
    "deck_size": 100,
    "timing_mode": "relaxed"
  }
}
```

**POST /api/lobbies/{code}/action** Request Body:
```json
{
  "action": "play",
  "data": { "card": 42 }
}
```
Actions: `play` (data: `{card: number}`), `pass` (data: `{}`), `advance` (data: `{}`), `restart` (data: `{}`)

**Action Response**: Returns player-specific game state including `my_hand`. Also triggers a WebSocket broadcast.

---

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

#### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/google/login` | Initiate Google OAuth login flow |
| GET | `/api/auth/google/callback` | OAuth callback (handled by backend) |
| GET | `/api/auth/me` | Get current authenticated user info |
| POST | `/api/auth/logout` | Logout user and clear session |

**GET /api/auth/me** Response:
```json
{
  "user_id": "integer",
  "google_id": "string",
  "email": "string",
  "name": "string",
  "avatar_url": "string | null"
}
```

**Features**:
- JWT tokens stored in HTTP-only cookies (7-day expiry)
- Avatar support with fallback to database lookup for old tokens
- Automatic name pre-fill in lobby forms when authenticated
- Logout clears cookie and redirects to home

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/lobby/{lobby_code}` | WebSocket connection for lobby real-time updates |

#### WebSocket Message Protocol

**Message Types:**

| Type | Direction | Description |
|------|-----------|-------------|
| `connected` | Server → Client | Sent when client connects. Includes chat history and connected player IDs |
| `player_joined` | Server → Client | Broadcast when a new player joins |
| `player_left` | Server → Client | Broadcast when a player leaves |
| `lobby_update` | Server → Client | Broadcast when player list changes (NO `you` field) |
| `connection_update` | Server → Client | Broadcast when a player's WebSocket connection status changes |
| `chat` | Client ↔ Server | Chat messages |
| `countdown` | Server → Client | 3-2-1 countdown before game start |
| `game_started` | Server → Client | Game has started; includes initial public game state |
| `game_update` | Server → Client | Broadcast after a play/pass action; includes updated public game state |
| `level_started` | Server → Client | Broadcast after advance/restart; clients should re-fetch for private hand |
| `error` | Server → Client | Error message |

**Important Design Notes:**
- WebSocket broadcasts ONLY include public game state, NOT private card hands
- `you` field is never in WebSocket broadcasts — each client preserves their own identity
- After `level_started`, clients call `GET /api/lobbies/{code}` to get their new private hand
- `connection_update` carries a `connected_players` array of player IDs currently connected

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

**Countdown:**
```json
{
  "type": "countdown",
  "data": { "count": 3, "message": "Game starting in 3..." }
}
```

**Game Started:**
```json
{
  "type": "game_started",
  "data": {
    "game_type": "classic",
    "game_state": { "level": 1, "status": "playing", "played_cards": [], ... },
    "lobby": { ... }
  }
}
```

**Game Update (after play/pass):**
```json
{
  "type": "game_update",
  "data": {
    "level": 1, "status": "playing",
    "played_cards": [7],
    "next_expected": 15,
    "player_hands": { "uuid": { "card_count": 0, "cards_played": [7] }, ... }
  }
}
```
**Note:** `game_update` carries public state only. No `my_hand` — each player's private cards come only from HTTP responses.

**Level Started (after advance/restart):**
```json
{
  "type": "level_started",
  "data": { "level": 2, "status": "playing", "action": "advance" }
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

### Table: users

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| google_id | VARCHAR(255) | Google OAuth ID (unique, indexed) |
| email | VARCHAR(255) | User email (unique, indexed) |
| name | VARCHAR(255) | Display name from Google |
| avatar_url | VARCHAR(500) | Google profile image URL |
| is_active | BOOLEAN | Account status (default: true) |
| created_at | TIMESTAMP | Account creation time |
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
│   ├── auth/                    # Authentication components
│   │   └── GoogleAuth.tsx       # Google login button + user info
│   ├── layout/                  # Layout components
│   │   ├── MainLayout.tsx       # App shell with navbar
│   │   └── Navbar.tsx           # Top navigation + auth + theme toggle
│   └── lobby/                   # Lobby-specific components
│       ├── JoinLobbyForm.tsx    # Name input form (join/create)
│       ├── PlayerList.tsx       # Display players with host badges
│       ├── LobbyChat.tsx        # Real-time chat (inline + overlay modes)
│       ├── LobbyCodeInput.tsx   # Lobby code entry with validation
│       ├── GameBoard.tsx        # Main game UI (fanned hands, last played card)
│       ├── GameResults.tsx      # Level success/failure overlay with card reveal
│       └── CountdownOverlay.tsx # 3-2-1 countdown animation before game start
├── contexts/
│   └── AuthContext.tsx          # Global auth state management
├── pages/
│   ├── HomePage.tsx             # Landing with New/Join Game options
│   ├── LeaderboardPage.tsx      # High scores display
│   └── LobbyPage.tsx            # Main game lobby (composite of components)
├── hooks/
│   ├── useAuth.ts               # Auth hook (exports from AuthContext)
│   ├── useTheme.ts              # Dark mode management
│   └── lobby/
│       └── useLobby.ts          # Main lobby state + WebSocket hook
├── types/
│   └── lobby.ts                 # TypeScript types (Player, Lobby, ChatMessage, User)
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
│   ├── models.py                # SQLAlchemy DB models (Counter, Leaderboard, User)
│   ├── config.py                # Application configuration + settings
│   ├── database.py              # Async PostgreSQL connection
│   ├── lobby_manager.py         # In-memory lobby + player + chat + game management
│   ├── websocket.py             # WebSocket connection manager (room-based)
│   ├── games/
│   │   ├── base.py              # Abstract Game class + GameStatus enum + GameAction
│   │   ├── classic.py           # ClassicCarduitive game implementation
│   │   └── factory.py           # Game factory (creates game instances by type)
│   ├── services/
│   │   └── user_service.py      # User CRUD operations
│   └── routers/
│       ├── auth.py              # Google OAuth endpoints
│       ├── counter.py           # Demo counter API
│       ├── leaderboard.py       # Leaderboard CRUD
│       └── lobbies.py           # Lobby HTTP API + game start/action endpoints
├── init_db.py                   # Database initialization script
├── start.sh                     # Development startup script
├── requirements.txt             # Python dependencies
└── Dockerfile                   # Container config
```

### Key Files by Function

| File | Purpose |
|------|---------|
| `frontend/src/contexts/AuthContext.tsx` | Global auth state management |
| `frontend/src/hooks/lobby/useLobby.ts` | All lobby + game state, WebSocket, HTTP actions |
| `frontend/src/components/lobby/GameBoard.tsx` | Game UI: fanned hands, card play, opponent view |
| `frontend/src/components/lobby/GameResults.tsx` | Post-round overlay with per-player card reveal |
| `backend/app/routers/auth.py` | Google OAuth + JWT token management |
| `backend/app/services/user_service.py` | User database operations |
| `backend/app/lobby_manager.py` | In-memory Lobby/Player/ChatMessage + game delegation |
| `backend/app/games/classic.py` | Classic game logic: dealing, play validation, level progression |
| `backend/app/routers/lobbies.py` | HTTP endpoints: lobby CRUD + game start/action/state |
| `backend/app/main.py` | WebSocket endpoint + HTTP-to-WS broadcast bridge |
| `backend/app/websocket.py` | Room-based WebSocket connection manager |

---

## Kubernetes Configuration

### Components
- **Frontend Deployment**: React app served via nginx (hostNetwork, binds to port 80)
- **Backend Deployment**: FastAPI application
- **Services**: NodePort (frontend: 30081, backend: 30080)
- **No LoadBalancer/Ingress**: Traffic enters via Cloudflare → Node External IP → NodePort
- **In-cluster PostgreSQL**: Runs as a pod with persistent volume (no Cloud SQL)
- **Secrets**: Managed via GCP Secret Manager, synced to Kubernetes secrets manually

---

## CI/CD Pipeline

### GitHub Actions Workflow
1. **Lint & Test**: Run linting and tests
2. **Build**: Build Docker images
3. **Deploy to GKE**: Deploy to Autopilot cluster

---

## Environment Variables

### Backend
| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | Application secret key for JWT signing | Yes |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | Yes (for auth) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | Yes (for auth) |
| `FRONTEND_URL` | Frontend URL for OAuth redirects | Yes (default: http://localhost:5173) |
| `ENVIRONMENT` | Environment name (development/production) | No (default: development) |

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

### Completed ✅
- **User authentication**: Google OAuth with JWT tokens, avatar support, persistent sessions
- **Game logic (Classic Carduitive)**: Cooperative ascending-order card game with server-side validation
- **Real-time game state**: WebSocket-driven countdown, card play broadcast, level transitions
- **Game UI**: Fanned card hands with Framer Motion animations, per-player opponent view
- **GameResults overlay**: Post-round card reveal for all players on success/failure
- **Lobby management**: Player join/leave, connection status tracking, host controls, re-join

### Planned
- Leaderboard integration on game completion (auto-submit scores)
- Advanced leaderboard features (filters by time range, personal bests)
- Additional game modes (timed, speedrun)
- Monitoring and logging (Cloud Monitoring, Cloud Logging)
- User profiles with editable display names and avatars
- Friends system and invite functionality
- Spectator mode
- Game replay / action history view
