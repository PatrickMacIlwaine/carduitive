import { User, Crown, Loader2, CheckCircle2, Wifi, WifiOff } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { Player, CurrentPlayer } from '@/types/lobby'

interface PlayerListProps {
  players: Player[]
  currentPlayer?: CurrentPlayer
  playerCount: number
  loading?: boolean
}

function PlayerItem({ player, isCurrentPlayer }: { player: Player; isCurrentPlayer: boolean }) {
  const isConnected = player.is_connected ?? false
  
  return (
    <div 
      className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
        isCurrentPlayer 
          ? 'bg-primary/10 border border-primary/20' 
          : 'bg-muted hover:bg-muted/80'
      }`}
    >
      {/* Avatar */}
      <div className="relative">
        {player.avatar_url ? (
          <img
            src={player.avatar_url}
            alt={player.name}
            className="w-10 h-10 rounded-full object-cover"
          />
        ) : (
          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
            <User className="w-5 h-5 text-primary" />
          </div>
        )}
        {/* Connection status indicator */}
        <div 
          className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-background ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`}
          title={isConnected ? 'Connected' : 'Disconnected'}
        />
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium truncate">{player.name}</span>
          {player.is_authenticated && (
            <div className="text-green-500" title="Verified Google user">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          )}
          {isCurrentPlayer && (
            <span className="text-xs text-primary font-medium">(You)</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isConnected ? (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
              <Wifi className="w-3 h-3" />
              Connected
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300">
              <WifiOff className="w-3 h-3" />
              Offline
            </span>
          )}
        </div>
      </div>

      {player.is_host && (
        <div className="flex items-center gap-1 text-yellow-500 bg-yellow-500/10 px-2 py-1 rounded-full">
          <Crown className="w-3 h-3" />
          <span className="text-xs font-semibold">Host</span>
        </div>
      )}
    </div>
  )
}

export function PlayerList({ players, currentPlayer, playerCount, loading }: PlayerListProps) {
  // Count connected players
  const connectedCount = players.filter(p => p.is_connected).length
  
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="w-5 h-5" />
            Players
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="w-5 h-5" />
          Players ({connectedCount}/{playerCount} connected)
        </CardTitle>
        <CardDescription>
          {connectedCount === playerCount 
            ? "All players connected and ready" 
            : "Waiting for all players to connect..."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {players.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No players yet. Waiting for others to join...
            </div>
          ) : (
            players.map((player) => (
              <PlayerItem 
                key={player.id} 
                player={player}
                isCurrentPlayer={currentPlayer?.id === player.id}
              />
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
