import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Crown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface GameResultsProps {
  gameState: {
    status: 'success' | 'failed'
    level: number
    player_hands: {
      [playerId: string]: {
        card_count: number
        cards_played: number[]
      }
    }
    my_hand?: {
      cards: number[]
      cards_played: number[]
    }
  }
  players: Array<{
    id: string
    name: string
    is_host?: boolean
  }>
  currentPlayerId: string
  onAdvance: () => void
  onRestart: () => void
}

interface PlayerCardRowProps {
  playerName: string
  cardsPlayed: number[]
  remainingCards: number[]
  remainingCount: number
  isCurrentPlayer: boolean
  isHost?: boolean
}

function PlayerCardRow({ 
  playerName, 
  cardsPlayed, 
  remainingCards,
  remainingCount,
  isCurrentPlayer,
  isHost 
}: PlayerCardRowProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className={cn(
        "flex items-center gap-4 p-3 rounded-lg",
        isCurrentPlayer && "bg-primary/10 border border-primary/30"
      )}
    >
      <div className="w-32 flex-shrink-0">
        <p className="font-medium truncate flex items-center gap-1">
          {playerName}
          {isHost && <Crown className="w-4 h-4 text-yellow-500" />}
        </p>
        {isCurrentPlayer && (
          <p className="text-xs text-primary">You</p>
        )}
      </div>
      
      <div className="flex-1 flex flex-wrap gap-1">
        {cardsPlayed.length > 0 ? (
          cardsPlayed.map((card, idx) => (
            <div
              key={`played-${idx}`}
              className="w-10 h-14 rounded bg-slate-200 border border-slate-300 flex items-center justify-center text-sm font-bold text-slate-600"
            >
              {card}
            </div>
          ))
        ) : (
          <span className="text-sm text-muted-foreground">No cards played</span>
        )}
      </div>
      
      {remainingCards.length > 0 ? (
        <>
          <div className="text-muted-foreground">→</div>
          <div className="flex flex-wrap gap-1">
            {remainingCards.map((card, idx) => (
              <div
                key={`remaining-${idx}`}
                className="w-10 h-14 rounded bg-white border-2 border-primary/30 flex items-center justify-center text-sm font-bold text-primary"
              >
                {card}
              </div>
            ))}
          </div>
        </>
      ) : remainingCount > 0 ? (
        <>
          <div className="text-muted-foreground">→</div>
          <div className="text-sm text-muted-foreground">
            {remainingCount} card{remainingCount !== 1 ? 's' : ''} remaining
          </div>
        </>
      ) : null}
      
      <div className="w-16 text-right text-sm text-muted-foreground">
        {cardsPlayed.length + (remainingCards.length || remainingCount)} total
      </div>
    </motion.div>
  )
}

export function GameResults({ 
  gameState, 
  players, 
  currentPlayerId,
  onAdvance, 
  onRestart 
}: GameResultsProps) {
  const { status, level, player_hands, my_hand } = gameState
  const isWin = status === 'success'

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="absolute inset-0 bg-background/95 flex items-center justify-center z-20 p-4"
    >
      <Card className="w-full max-w-2xl max-h-[80vh] overflow-auto">
        <CardHeader className="text-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", bounce: 0.5 }}
          >
            <CardTitle className={cn(
              "text-4xl mb-2",
              isWin ? "text-green-500" : "text-red-500"
            )}>
              {isWin ? '🎉 Level Complete!' : '💥 Level Failed'}
            </CardTitle>
            <p className="text-muted-foreground">
              Level {level} - All Players' Cards
            </p>
          </motion.div>
        </CardHeader>
        
        <CardContent className="space-y-2">
          <div className="text-sm text-muted-foreground mb-4">
            <p className="font-medium mb-2">Cards played → Remaining in hand</p>
          </div>
          
          {players.map((player, index) => {
            const handInfo = player_hands[player.id] || { card_count: 0, cards_played: [] }
            const isCurrentPlayer = player.id === currentPlayerId
            
            const remainingCards = isCurrentPlayer && my_hand ? my_hand.cards : []
            
            return (
              <motion.div
                key={player.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <PlayerCardRow
                  playerName={player.name}
                  cardsPlayed={handInfo.cards_played}
                  remainingCards={remainingCards}
                  remainingCount={handInfo.card_count}
                  isCurrentPlayer={isCurrentPlayer}
                  isHost={player.is_host}
                />
              </motion.div>
            )
          })}
          
          <div className="flex justify-center gap-4 mt-6 pt-4 border-t">
            {isWin ? (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onAdvance}
                className="px-8 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium shadow-lg"
              >
                Advance to Level {level + 1}
              </motion.button>
            ) : (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onRestart}
                className="px-8 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium shadow-lg"
              >
                Try Level {level} Again
              </motion.button>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
