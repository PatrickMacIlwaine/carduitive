import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Wifi, WifiOff, Crown, Users, Copy, Check, Settings, Trophy } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useLobby } from '@/hooks/lobby/useLobby'
import { useClassicGame } from '@/hooks/game/useClassicGame'
import { useAuth } from '@/hooks/useAuth'
import { PlayerList } from '@/components/lobby/PlayerList'
import { LobbyChat } from '@/components/lobby/LobbyChat'
import { JoinLobbyForm } from '@/components/lobby/JoinLobbyForm'
import { CountdownOverlay } from '@/components/lobby/CountdownOverlay'
import { GameBoard } from '@/components/lobby/GameBoard'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { GameSettingsModal } from '@/components/lobby/GameSettingsModal'
import type { GameConfig } from '@/types/lobby'

function LobbyHeader({
  code,
  wsConnected,
  playerCount
}: {
  code: string
  wsConnected: boolean
  playerCount: number
}) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    const lobbyUrl = `${window.location.origin}/lobby/${code}`
    await navigator.clipboard.writeText(lobbyUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="text-center space-y-4">
      <button
        onClick={handleCopy}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary font-mono text-lg tracking-widest hover:bg-primary/20 transition-colors cursor-pointer"
      >
        {code}
        {copied ? (
          <Check className="w-4 h-4 text-green-500" />
        ) : (
          <Copy className="w-4 h-4" />
        )}
      </button>
      {copied && (
        <p className="text-sm text-green-500">Copied!</p>
      )}
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
  playerCount,
  connectedCount,
  isStarting,
  onStartGame,
  onOpenSettings,
  failureMode,
  allAuthenticated,
}: {
  isHost: boolean
  playerCount: number
  connectedCount: number
  isStarting: boolean
  onStartGame: () => void
  onOpenSettings: () => void
  failureMode: string
  allAuthenticated: boolean
}) {
  const leaderboardEligible = failureMode === 'hardcore' && playerCount >= 2 && allAuthenticated
  if (!isHost) {
    return (
      <Card>
        <CardContent className="py-8 text-center space-y-3">
          <Crown className="w-8 h-8 mx-auto mb-2 text-muted-foreground opacity-50" />
          <p className="text-muted-foreground">Waiting for host to start the game...</p>
          <Button variant="outline" size="sm" onClick={onOpenSettings}>
            <Settings className="w-4 h-4 mr-2" />
            View Settings
          </Button>
        </CardContent>
      </Card>
    )
  }

  const allConnected = connectedCount === playerCount
  const canStart = allConnected && !isStarting

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="w-5 h-5" />
          Host Controls
        </CardTitle>
        <CardDescription>
          {allConnected
            ? "All players connected. Ready to start!"
            : `Waiting for ${playerCount - connectedCount} more player${playerCount - connectedCount === 1 ? '' : 's'} to connect...`}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <Button variant="outline" className="w-full" onClick={onOpenSettings}>
          <Settings className="w-4 h-4 mr-2" />
          Game Settings
          <span className="ml-auto text-xs text-muted-foreground capitalize">{failureMode}</span>
        </Button>
        {leaderboardEligible && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-yellow-50 dark:bg-yellow-950/30 border border-yellow-200 dark:border-yellow-800">
            <Trophy className="w-4 h-4 text-yellow-500 flex-shrink-0" />
            <p className="text-xs text-yellow-700 dark:text-yellow-400">Leaderboard eligible</p>
          </div>
        )}
        {failureMode === 'hardcore' && playerCount >= 2 && !allAuthenticated && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/50 border border-muted">
            <Trophy className="w-4 h-4 text-muted-foreground flex-shrink-0" />
            <p className="text-xs text-muted-foreground">All players must sign in with Google for leaderboard</p>
          </div>
        )}
        <Button
          className="w-full"
          size="lg"
          disabled={!canStart}
          onClick={onStartGame}
        >
          {isStarting ? 'Starting...' : 'Start Game'}
        </Button>
        {!allConnected && (
          <p className="text-sm text-muted-foreground mt-2 text-center">
            All players must be connected to start
          </p>
        )}
      </CardContent>
    </Card>
  )
}

export function LobbyPage() {
  const { lobbyCode } = useParams<{ lobbyCode: string }>()
  const code = lobbyCode?.toUpperCase() || ''
  
  const { user } = useAuth()
  
  // Chat toggle state for game mode
  const [showGameChat, setShowGameChat] = useState(false)
  const [showSettings, setShowSettings] = useState(false)

  const handleConfigChange = (config: Partial<GameConfig>) => {
    updateConfig(config)
  }
  
  const {
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
    startGame: startLobbyGame,
    sendGameAction,
    updateConfig,
  } = useLobby(code)

  // Classic game actions — add new game mode hooks here and dispatch by lobby.game_type
  const { startGame, playCard, advanceLevel, restartLevel } = useClassicGame(sendGameAction, startLobbyGame)

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

  // Show lobby interface or game board
  const connectedCount = lobby.players.filter(p => p.is_connected).length
  const isPlaying = lobby.status === 'playing' && lobby.game_state
  
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Countdown Overlay */}
      <CountdownOverlay 
        count={countdown} 
        onComplete={() => console.log('Countdown complete!')} 
      />
      
      {/* Header - Different for lobby vs game */}
      {!isPlaying && (
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
      )}

      {isPlaying ? (
        /* Game Mode - With Overlay Chat */
        <div className="relative">
          <GameBoard
            gameState={lobby.game_state}
            currentPlayerId={lobby.you?.id || ''}
            players={lobby.players.map(p => ({ 
              id: p.id, 
              name: p.name,
              is_connected: p.is_connected,
              is_host: p.is_host
            }))}
            onPlayCard={playCard}
            onAdvance={advanceLevel}
            onRestart={restartLevel}
          />
          
          <LobbyChat
            mode="overlay"
            messages={messages}
            onSendMessage={sendChatMessage}
            disabled={!wsConnected}
            isOpen={showGameChat}
            onToggle={() => setShowGameChat(!showGameChat)}
          />
        </div>
      ) : (
        /* Lobby Interface */
        <>
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
                connectedCount={connectedCount}
                isStarting={isStarting}
                onStartGame={startGame}
                onOpenSettings={() => setShowSettings(true)}
                failureMode={lobby.game_config?.failure_mode ?? 'forgiving'}
                allAuthenticated={lobby.players.every(p => p.is_authenticated)}
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

          <GameSettingsModal
            isOpen={showSettings}
            onClose={() => setShowSettings(false)}
            config={lobby.game_config ?? {}}
            onConfigChange={handleConfigChange}
            isHost={lobby.you?.is_host || false}
          />
        </>
      )}
    </div>
  )
}
