export interface Player {
  id: string
  name: string
  is_host: boolean
  joined_at: string
  avatar_url?: string
  is_authenticated?: boolean
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

export interface Lobby {
  code: string
  status: 'waiting' | 'playing' | 'ended'
  player_count: number
  players: Player[]
  you?: CurrentPlayer
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
  type: 'player_joined' | 'player_left' | 'lobby_update' | 'chat' | 'connected' | 'error'
  data?: Lobby | ChatMessage | { messages: ChatMessage[] }
  player_name?: string
  message?: string
  player_id?: string
  timestamp?: string
}

// Auth types
export interface User {
  user_id: number
  google_id: string
  email: string
  name: string
  avatar_url?: string
}
