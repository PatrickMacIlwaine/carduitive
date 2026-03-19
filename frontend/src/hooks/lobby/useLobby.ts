import { useState, useEffect, useRef, useCallback } from 'react'
import type { Lobby, ChatMessage, WebSocketMessage } from '@/types/lobby'
import { API_URL } from '@/contexts/AuthContext'

interface UseLobbyReturn {
  lobby: Lobby | null
  loading: boolean
  error: string | null
  wsConnected: boolean
  messages: ChatMessage[]
  countdown: number | null
  isStarting: boolean
  joinLobby: (playerName: string) => Promise<boolean>
  createLobby: (playerName: string) => Promise<boolean>
  leaveLobby: () => void
  sendChatMessage: (message: string) => void
  startGame: (gameType: string, config: Record<string, unknown>) => Promise<boolean>
  sendGameAction: (action: string, data?: Record<string, unknown>) => Promise<boolean>
}

export function useLobby(lobbyCode: string): UseLobbyReturn {
  const [lobby, setLobby] = useState<Lobby | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [wsConnected, setWsConnected] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [countdown, setCountdown] = useState<number | null>(null)
  const [isStarting, setIsStarting] = useState(false)
  
  const wsRef = useRef<WebSocket | null>(null)
  const playerRef = useRef<{ id: string; name: string } | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const MAX_RECONNECT_ATTEMPTS = 5
  const RECONNECT_DELAY = 3000 // 3 seconds

  // Fetch lobby data from API
  const fetchLobby = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/lobbies/${lobbyCode}`, {
        credentials: 'include'
      })
      
      if (!res.ok) {
        if (res.status === 404) {
          return false
        }
        throw new Error('Failed to fetch lobby')
      }
      
      const data = await res.json()
      setLobby(data)
      
      // Store current player reference
      if (data.you) {
        playerRef.current = { id: data.you.id, name: data.you.name }
      }
      
      return true
    } catch (err) {
      console.error('Error fetching lobby:', err)
      setError('Failed to load lobby')
      return false
    } finally {
      setLoading(false)
    }
  }, [lobbyCode])

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    // Use same origin - works in both dev (Vite proxy) and production (Ingress proxy)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/lobby/${lobbyCode}`
    
    console.log('Connecting to WebSocket:', wsUrl)
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected to lobby')
      setWsConnected(true)
      setError(null)
      // Reset reconnection attempts on successful connection
      reconnectAttemptsRef.current = 0
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
    }

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        console.log('WebSocket message:', message)
        
        switch (message.type) {
          case 'player_joined':
            if (message.player_name) {
              setMessages(prev => [...prev, {
                id: `system-${Date.now()}`,
                player_name: 'System',
                player_id: 'system',
                message: `${message.player_name} joined the lobby`,
                timestamp: new Date().toISOString(),
                type: 'system'
              }])
            }
            break
            
          case 'player_left':
            if (message.player_name) {
              setMessages(prev => [...prev, {
                id: `system-${Date.now()}`,
                player_name: 'System',
                player_id: 'system',
                message: `${message.player_name} left the lobby`,
                timestamp: new Date().toISOString(),
                type: 'system'
              }])
            }
            break
            
          case 'lobby_update':
            if (message.data && 'players' in message.data) {
              // Merge lobby update while preserving 'you' (current player identity) and my_hand
              setLobby(prev => {
                const updatedLobby = message.data as Lobby
                return {
                  ...updatedLobby,
                  you: prev?.you,  // Preserve current player's identity
                  game_state: prev?.game_state ? {
                    ...updatedLobby.game_state,
                    my_hand: prev.game_state.my_hand  // Preserve my private hand
                  } : updatedLobby.game_state
                }
              })
            }
            break
            
          case 'game_update':
            // Update game state from other players' moves
            if (message.data) {
              const gameData = message.data as any
              
              setLobby(prev => {
                if (!prev) return prev
                const prevPlayedCount = prev.game_state?.played_cards?.length || 0
                const newPlayedCount = gameData.played_cards?.length || 0
                
                // If more cards were played (by others), fetch fresh data to sync
                // Otherwise just update with preserved my_hand
                if (newPlayedCount > prevPlayedCount) {
                  // Schedule fetch after this state update
                  setTimeout(() => fetchLobby(), 0)
                  return {
                    ...prev,
                    game_state: gameData
                  }
                }
                
                return {
                  ...prev,
                  game_state: {
                    ...gameData,
                    my_hand: prev.game_state?.my_hand
                  }
                }
              })
            }
            break
            
          case 'level_started':
            // New level started (advance or restart)
            console.log('Level started:', message.data)
            if (message.data && 'level' in message.data) {
              const levelData = message.data as { level: number; status: string; action: string }
              // Update lobby with new level info
              setLobby(prev => {
                if (!prev) return prev
                return {
                  ...prev,
                  status: 'playing',
                  current_level: levelData.level,
                  game_state: {
                    ...prev.game_state,
                    level: levelData.level,
                    status: levelData.status
                  }
                }
              })
              
              // Fetch new game state with new cards for this level
              // Use setTimeout to ensure backend has processed the level transition
              setTimeout(() => {
                console.log('Fetching new game state for level', levelData.level)
                fetchLobby()
              }, 100)
            }
            break
            
          case 'connection_update':
            // Update connection status for players
            if (message.connected_players) {
              setLobby(prev => {
                if (!prev) return prev
                const connectedSet = new Set(message.connected_players)
                return {
                  ...prev,
                  players: prev.players.map(player => ({
                    ...player,
                    is_connected: connectedSet.has(player.id)
                  }))
                }
              })
            }
            break
            
          case 'chat':
            if (message.data && 'player_id' in message.data) {
              const chatData = message.data as ChatMessage
              setMessages(prev => {
                // Avoid duplicates by checking id
                if (prev.some(m => m.id === chatData.id)) {
                  return prev
                }
                return [...prev, chatData]
              })
            }
            break
            
          case 'connected':
            console.log('Connected to lobby:', message.message)
            // Load initial chat history from connection
            if (message.data && 'messages' in message.data && Array.isArray(message.data.messages)) {
              setMessages(message.data.messages as ChatMessage[])
            }
            // Load initial connected players
            if (message.data && 'connected_players' in message.data && Array.isArray(message.data.connected_players)) {
              const connectedSet = new Set(message.data.connected_players as string[])
              setLobby(prev => {
                if (!prev) return prev
                return {
                  ...prev,
                  players: prev.players.map(player => ({
                    ...player,
                    is_connected: connectedSet.has(player.id)
                  }))
                }
              })
            }
            break
            
          case 'countdown':
            if (message.data && 'count' in message.data) {
              const count = message.data.count as number
              console.log('Countdown:', count)
              setCountdown(count)
              setIsStarting(true)
              
              // Clear countdown after it reaches 0
              if (count === 0) {
                setTimeout(() => {
                  setCountdown(null)
                  setIsStarting(false)
                }, 1500)
              }
            }
            break
            
          case 'game_started':
            console.log('Game started:', message.data)
            const gameData = message.data as any
            if (gameData && gameData.game_state) {
              setLobby(prev => {
                if (!prev) return prev
                return {
                  ...prev,
                  status: 'playing',
                  game_state: gameData.game_state
                }
              })
            }
            setCountdown(null)
            setIsStarting(false)
            
            // Fetch full game state with private hand info
            fetchLobby()
            break
            
          case 'error':
            console.error('WebSocket error:', message.message)
            break
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err)
      }
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setWsConnected(false)
      
      // Attempt to reconnect if we haven't exceeded max attempts
      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttemptsRef.current++
        console.log(`Attempting to reconnect... (${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`)
        
        reconnectTimeoutRef.current = setTimeout(() => {
          fetchLobby().then(success => {
            if (success && lobby) {
              connectWebSocket()
            }
          })
        }, RECONNECT_DELAY)
      } else {
        console.log('Max reconnection attempts reached')
        setError('Connection lost. Please refresh the page to rejoin.')
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setWsConnected(false)
    }
  }, [lobbyCode])

  // Disconnect WebSocket
  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setWsConnected(false)
  }, [])

  // Join existing lobby
  const joinLobby = useCallback(async (playerName: string): Promise<boolean> => {
    try {
      setLoading(true)
      setError(null)
      
      const res = await fetch(`${API_URL}/lobbies/${lobbyCode}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ player_name: playerName.trim() })
      })

      if (res.status === 409) {
        const errorData = await res.json()
        setError(errorData.detail || `Name '${playerName}' is already taken`)
        return false
      }

      if (!res.ok) {
        throw new Error('Failed to join lobby')
      }

      const data = await res.json()
      setLobby(data)
      playerRef.current = { id: data.you.id, name: data.you.name }
      
      // If re-joining, load messages from response
      if (data.messages) {
        setMessages(data.messages)
      }
      
      // Connect to WebSocket
      connectWebSocket()
      
      return true
    } catch (err) {
      console.error('Error joining lobby:', err)
      setError('Failed to join lobby')
      return false
    } finally {
      setLoading(false)
    }
  }, [lobbyCode, connectWebSocket])

  // Create new lobby
  const createLobby = useCallback(async (playerName: string): Promise<boolean> => {
    try {
      setLoading(true)
      
      const res = await fetch(`${API_URL}/lobbies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ 
          code: lobbyCode,
          player_name: playerName.trim() 
        })
      })

      if (!res.ok) {
        throw new Error('Failed to create lobby')
      }

      const data = await res.json()
      setLobby(data)
      playerRef.current = { id: data.you.id, name: data.you.name }
      
      // Connect to WebSocket
      connectWebSocket()
      
      return true
    } catch (err) {
      console.error('Error creating lobby:', err)
      setError('Failed to create lobby')
      return false
    } finally {
      setLoading(false)
    }
  }, [lobbyCode, connectWebSocket])

  // Leave lobby
  const leaveLobby = useCallback(async () => {
    try {
      await fetch(`${API_URL}/lobbies/${lobbyCode}/leave`, {
        method: 'POST',
        credentials: 'include'
      })
    } catch (err) {
      console.error('Error leaving lobby:', err)
    } finally {
      disconnectWebSocket()
      setLobby(null)
      playerRef.current = null
      setMessages([])
    }
  }, [lobbyCode, disconnectWebSocket])

  // Send chat message
  const sendChatMessage = useCallback((message: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected')
      return
    }

    const player = playerRef.current
    if (!player) {
      console.error('No player reference')
      return
    }

    // Send message to server - it will broadcast back to all clients
    wsRef.current.send(JSON.stringify({
      type: 'chat',
      player_name: player.name,
      player_id: player.id,
      message: message.trim(),
    }))
  }, [])

  // Start game (host only) — game type and config provided by the game-specific layer
  const startGame = useCallback(async (gameType: string, config: Record<string, unknown>): Promise<boolean> => {
    try {
      setIsStarting(true)

      const res = await fetch(`${API_URL}/lobbies/${lobbyCode}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ game_type: gameType, config })
      })

      if (!res.ok) {
        const errorData = await res.json()
        setError(errorData.detail || 'Failed to start game')
        setIsStarting(false)
        return false
      }

      const data = await res.json()
      console.log('Game start response:', data)

      // Countdown will be handled via WebSocket messages
      return true
    } catch (err) {
      console.error('Error starting game:', err)
      setError('Failed to start game')
      setIsStarting(false)
      return false
    }
  }, [lobbyCode])

  // Generic game action — used by game-mode-specific hooks (e.g. useClassicGame)
  const sendGameAction = useCallback(async (action: string, data: Record<string, unknown> = {}): Promise<boolean> => {
    try {
      const res = await fetch(`${API_URL}/lobbies/${lobbyCode}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ action, data })
      })

      if (!res.ok) {
        const errorData = await res.json()
        setError(errorData.detail || `Action failed: ${action}`)
        return false
      }

      const responseData = await res.json()

      setLobby(prev => {
        if (!prev) return prev
        return {
          ...prev,
          game_state: responseData,
          ...(responseData.level !== undefined ? { current_level: responseData.level } : {})
        }
      })

      return true
    } catch (err) {
      console.error(`Error on game action '${action}':`, err)
      setError(`Action failed: ${action}`)
      return false
    }
  }, [lobbyCode])

  // Initial lobby check
  useEffect(() => {
    let mounted = true
    
    const checkLobby = async () => {
      const exists = await fetchLobby()
      if (mounted && exists) {
        connectWebSocket()
      }
    }
    
    checkLobby()
    
    return () => {
      mounted = false
    }
  }, [fetchLobby, connectWebSocket])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectWebSocket()
      // Clear any pending reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [disconnectWebSocket])

  return {
    lobby,
    loading,
    error,
    wsConnected,
    messages,
    countdown,
    isStarting,
    joinLobby,
    createLobby,
    leaveLobby,
    sendChatMessage,
    startGame,
    sendGameAction,
  }
}
