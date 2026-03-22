# Carduitive - Claude Code Guidelines

This file governs how Claude assists with this codebase. Follow these principles in every session.

**Never add `Co-Authored-By` lines to commit messages.**

**Never add "Generated with Claude Code" lines to PR descriptions.**

---

## Code Quality Standards

### 1. TypeScript Strictness

- **No `any` types.** The one exception is `game_state` in `Lobby` — this is intentionally loose until a second game mode exists and we can define a discriminated union. Do not introduce new `any` usages.
- Define explicit interfaces for all WebSocket message payloads, API request/response bodies, and game state shapes.
- Use discriminated unions for types that vary by game mode:
  ```ts
  type GameState = ClassicGameState | FutureGameState
  type GameState = { game_type: 'classic' } & ClassicGameState
                 | { game_type: 'future'  } & FutureGameState
  ```
- Prefer `unknown` over `any` when a type is truly unknown — it forces explicit narrowing before use.
- All new hook return types must have an explicit named interface (not inlined).

---

### 2. Test Coverage

**Always use Docker to run tests — never a local venv or system Python.**

There are two categories of backend tests:

- **Unit tests** (`test_disconnect.py`, `test_player_state.py`): Import game/lobby classes directly. Run inside the backend container:
  ```bash
  docker compose up -d --build
  docker compose exec backend python -m pytest tests/test_disconnect.py tests/test_player_state.py -v
  ```
- **Integration tests** (`test_backend.py`, `test_dealing.py`): Hit the live API at `http://localhost:8000`. Run against the running stack:
  ```bash
  docker compose exec backend python tests/test_backend.py
  docker compose exec backend python tests/test_dealing.py
  ```

New game modes require tests covering: deal correctness, valid play, invalid play (wrong card), level completion, level failure, advance, restart.
- Test the HTTP endpoints for game actions — not just the game class in isolation.
- Do not mock `lobby_manager` in action tests — test through the real manager.

**Frontend:**
- New utility functions in `src/lib/` require unit tests.
- When a bug is fixed, add a test that would have caught it.
- Complex state transitions in game hooks (e.g., reconnect while playing, level transition race) should have integration tests once a frontend test setup is in place.

---

### 3. Error Handling

**Backend:**
- All `HTTPException` usages must include a `detail` string that is safe to surface to the user.
- Game action errors return `{"error": "..."}` from the game engine — the router must translate these to `HTTPException(400, detail=...)` before responding. Never let raw engine errors reach the client unchecked.
- WebSocket errors broadcast `{"type": "error", "message": "..."}` — always include a user-readable message.

**Frontend:**
- Errors from game actions (play, advance, restart) must surface visibly in the game UI — not just `console.error`.
- `useLobby` errors should distinguish between lobby errors (shown in join form) and game errors (shown in game board). Do not reuse the single `error` string for both once the game layer is split.
- Never silently swallow errors from `fetch` calls. If you catch and don't surface, add a comment explaining why.

---

### 4. Game Mode Extensibility

The backend is already structured correctly (abstract `Game` class + factory). The frontend must follow the same pattern. **Adding a new game mode should mean adding files, not editing existing ones.**

**The rule:** `LobbyPage.tsx`, `useLobby.ts`, and the lobby WebSocket layer are generic infrastructure. They must not contain Classic-specific logic.

**Target architecture:**

```
useLobby
└── exposes: sendGameAction(action: string, data: Record<string, unknown>) => Promise<boolean>
    (lobby/WS/connection layer — game-type agnostic)

Per-game hooks (optional, for typed convenience):
└── useClassicGame(sendGameAction) → { playCard, advanceLevel, restartLevel }

LobbyPage renders game component by game_type:
└── 'classic' → <ClassicGameBoard />
    'future'  → <FutureGameBoard />
```

**When working on game logic:**
- Classic-specific action methods (`playCard`, `advanceLevel`, `restartLevel`) belong in a Classic-specific hook or component, not in `useLobby`.
- Game board components own their game state type — `ClassicGameBoard` defines what shape it expects from `game_state`, not a shared global type.
- The `sendGameAction(action, data)` primitive in `useLobby` is the only game-related export needed from the lobby layer.

**Do not** add new game-specific action methods to `useLobby` directly. Route them through `sendGameAction`.

---

### 5. Commit & PR Conventions

**Commit message format:**
```
<type>(<scope>): <short description>

[optional body]
```

**Types:**
| Type | When to use |
|------|-------------|
| `feat` | New user-facing feature |
| `fix` | Bug fix |
| `game` | Game logic changes (new mode, rule change, balance) |
| `refactor` | Code restructure with no behavior change |
| `test` | Adding or fixing tests |
| `docs` | SPEC.md, STYLES.md, CLAUDE.md, DEPLOYMENT_GUIDE.md |
| `infra` | k8s manifests, Dockerfiles, CI/CD |
| `chore` | Dependencies, config, tooling |

**Scopes:** `lobby`, `game`, `auth`, `leaderboard`, `ws`, `frontend`, `backend`, `k8s`

**Examples:**
```
feat(game): add classic game board with fanned card hands
fix(ws): preserve my_hand across lobby_update broadcasts
game(classic): validate lowest-card rule server-side only
refactor(lobby): extract sendGameAction from useLobby
docs: update SPEC with game engine architecture
infra: use hostNetwork for frontend to bind port 80
```

**PR checklist before merging:**
- [ ] No new `any` types introduced
- [ ] New game logic has backend tests
- [ ] Errors surface to the user (not just console)
- [ ] Game-specific code is not added to `useLobby` directly
- [ ] SPEC.md or STYLES.md updated if architecture/design changed
- [ ] Commit messages follow format above

---

## Architecture Reminders

- **Private card hands are never in WebSocket broadcasts.** Only HTTP responses include `my_hand`. After `level_started`, clients must re-fetch via `GET /api/lobbies/{code}`.
- **`you` is never in WebSocket broadcasts.** Each client preserves their own identity from the initial HTTP join/create response.
- **All game logic runs server-side.** The frontend sends actions and renders state — it never computes game outcomes locally.
- **Lobby state is in-memory only.** Data loss on pod restart is acceptable. Do not attempt to persist lobby/game state to the database.
- See `SPEC.md` for full architecture and API reference.
- See `STYLES.md` for design system, component patterns, and game board aesthetics.
