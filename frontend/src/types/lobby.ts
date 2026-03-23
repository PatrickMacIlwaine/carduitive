export interface Player {
  id: string
  name: string
  is_host: boolean
  joined_at: string
  avatar_url?: string
  is_authenticated?: boolean
  is_connected?: boolean  // WebSocket connection status
  is_ready?: boolean      // Ready to start game
}

export interface CurrentPlayer {
  id: string
  name: string
  is_host: boolean
  session_id: string
  avatar_url?: string
  is_authenticated?: boolean
  user_id?: number
}

export interface GameConfig {
  failure_mode?: 'forgiving' | 'hardcore'
  cards_sorted?: boolean
  timer_seconds?: number | null
}

export interface Lobby {
  code: string
  status: 'waiting' | 'starting' | 'playing' | 'ended'
  player_count: number
  players: Player[]
  you?: CurrentPlayer
  current_level?: number
  game_config?: GameConfig
  game_state?: any  // Game state when playing
  created_at?: string
  updated_at?: string
}

export interface ChatMessage {
  id: string
  player_name: string
  player_id: string
  message: string
  timestamp: string
  type: 'chat' | 'system'
}

export interface WebSocketMessage {
  type: 'player_joined' | 'player_left' | 'lobby_update' | 'chat' | 'connected' | 'connection_update' | 'countdown' | 'game_started' | 'game_update' | 'level_started' | 'config_update' | 'timer_tick' | 'error'
  data?: Lobby | ChatMessage | { messages: ChatMessage[]; connected_players?: string[]; count?: number; game_state?: any; game_type?: string; level?: number; status?: string; action?: string }
  player_name?: string
  message?: string
  player_id?: string
  timestamp?: string
  connected_players?: string[]
}

// Auth types
export interface User {
  user_id: number
  google_id: string
  email: string
  name: string
  avatar_url?: string
}
