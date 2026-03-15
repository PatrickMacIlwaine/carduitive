import { useState, useEffect, useRef, useCallback } from 'react'
import type { Lobby, ChatMessage, WebSocketMessage } from '@/types/lobby'

interface UseLobbyReturn {
  lobby: Lobby | null
  loading: boolean
  error: string | null
  wsConnected: boolean
  messages: ChatMessage[]
  joinLobby: (playerName: string) => Promise<boolean>
  createLobby: (playerName: string) => Promise<boolean>
  leaveLobby: () => void
  sendChatMessage: (message: string) => void
}

export function useLobby(lobbyCode: string): UseLobbyReturn {
  const [lobby, setLobby] = useState<Lobby | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [wsConnected, setWsConnected] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  
  const wsRef = useRef<WebSocket | null>(null)
  const playerRef = useRef<{ id: string; name: string } | null>(null)

  // Fetch lobby data from API
  const fetchLobby = useCallback(async () => {
    try {
      const res = await fetch(`/api/lobbies/${lobbyCode}`, {
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

    const wsUrl = `ws://${window.location.host}/ws/lobby/${lobbyCode}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected to lobby')
      setWsConnected(true)
      setError(null)
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
              // Merge lobby update while preserving 'you' (current player identity)
              setLobby(prev => {
                const updatedLobby = message.data as Lobby
                return {
                  ...updatedLobby,
                  you: prev?.you  // Preserve current player's identity
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
      
      const res = await fetch(`/api/lobbies/${lobbyCode}/join`, {
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
      
      const res = await fetch('/api/lobbies', {
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
      await fetch(`/api/lobbies/${lobbyCode}/leave`, {
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
    }
  }, [disconnectWebSocket])

  return {
    lobby,
    loading,
    error,
    wsConnected,
    messages,
    joinLobby,
    createLobby,
    leaveLobby,
    sendChatMessage
  }
}
