import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Wifi, WifiOff, Crown, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useLobby } from '@/hooks/lobby/useLobby'
import { useAuth } from '@/hooks/useAuth'
import { PlayerList } from '@/components/lobby/PlayerList'
import { LobbyChat } from '@/components/lobby/LobbyChat'
import { JoinLobbyForm } from '@/components/lobby/JoinLobbyForm'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

function LobbyHeader({ 
  code, 
  wsConnected, 
  playerCount 
}: { 
  code: string
  wsConnected: boolean
  playerCount: number
}) {
  return (
    <div className="text-center space-y-4">
      <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary font-mono text-lg tracking-widest">
        {code}
      </div>
      <div>
        <h1 className="text-3xl md:text-4xl font-bold">Lobby</h1>
        <p className="text-muted-foreground mt-2">
          {playerCount} {playerCount === 1 ? 'player' : 'players'} waiting
        </p>
      </div>
      <div className="flex items-center justify-center gap-2">
        {wsConnected ? (
          <span className="inline-flex items-center gap-1 text-green-500 text-sm">
            <Wifi className="w-4 h-4" />
            Connected
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-red-500 text-sm">
            <WifiOff className="w-4 h-4" />
            Disconnected
          </span>
        )}
      </div>
    </div>
  )
}

function HostControls({ 
  isHost, 
  playerCount 
}: { 
  isHost: boolean
  playerCount: number
}) {
  if (!isHost) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <Crown className="w-8 h-8 mx-auto mb-2 text-muted-foreground opacity-50" />
          <p className="text-muted-foreground">Waiting for host to start the game...</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="w-5 h-5" />
          Host Controls
        </CardTitle>
        <CardDescription>
          You are the host. Start the game when ready.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button 
          className="w-full" 
          size="lg"
          disabled={playerCount < 1}
        >
          Start Game
        </Button>
      </CardContent>
    </Card>
  )
}

export function LobbyPage() {
  const { lobbyCode } = useParams<{ lobbyCode: string }>()
  const code = lobbyCode?.toUpperCase() || ''
  
  const { user } = useAuth()
  
  const {
    lobby,
    loading,
    error,
    wsConnected,
    messages,
    joinLobby,
    createLobby,
    leaveLobby,
    sendChatMessage
  } = useLobby(code)

  const isNewLobby = !loading && !lobby && !error

  // Show join form if not in lobby yet (no lobby or not a player in the lobby)
  if (!lobby || !lobby.you) {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <Link to="/home">
          <Button variant="ghost" className="pl-0">
            <ArrowLeft className="mr-2 w-4 h-4" />
            Back to Home
          </Button>
        </Link>

        <JoinLobbyForm
          lobbyCode={code}
          isNewLobby={isNewLobby}
          onJoin={joinLobby}
          onCreate={createLobby}
          loading={loading}
          error={error}
          user={user}
        />
      </div>
    )
  }

  // Show lobby interface
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <Link to="/home">
          <Button variant="ghost" className="pl-0">
            <ArrowLeft className="mr-2 w-4 h-4" />
            Back to Home
          </Button>
        </Link>
        <Button variant="outline" onClick={leaveLobby}>
          Leave Lobby
        </Button>
      </div>

      {/* Lobby Header */}
      <LobbyHeader 
        code={code} 
        wsConnected={wsConnected}
        playerCount={lobby.player_count}
      />

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Player List */}
        <div className="lg:col-span-1 space-y-6">
          <PlayerList
            players={lobby.players}
            currentPlayer={lobby.you}
            playerCount={lobby.player_count}
            loading={loading}
          />

          <HostControls
            isHost={lobby.you?.is_host || false}
            playerCount={lobby.player_count}
          />
        </div>

        {/* Right Column - Chat */}
        <div className="lg:col-span-2">
          <LobbyChat
            messages={messages}
            onSendMessage={sendChatMessage}
            disabled={!wsConnected}
          />
        </div>
      </div>
    </div>
  )
}
