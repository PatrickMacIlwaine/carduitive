import { User, Crown, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { Player, CurrentPlayer } from '@/types/lobby'

interface PlayerListProps {
  players: Player[]
  currentPlayer?: CurrentPlayer
  playerCount: number
  loading?: boolean
}

function PlayerItem({ player, isCurrentPlayer }: { player: Player; isCurrentPlayer: boolean }) {
  return (
    <div 
      className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
        isCurrentPlayer 
          ? 'bg-primary/10 border border-primary/20' 
          : 'bg-muted hover:bg-muted/80'
      }`}
    >
      <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
        <User className="w-5 h-5 text-primary" />
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium truncate">{player.name}</span>
          {isCurrentPlayer && (
            <span className="text-xs text-primary font-medium">(You)</span>
          )}
        </div>
        <span className="text-xs text-muted-foreground">
          Joined {new Date(player.joined_at).toLocaleTimeString()}
        </span>
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
          Players ({playerCount})
        </CardTitle>
        <CardDescription>
          Players currently in this lobby
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
