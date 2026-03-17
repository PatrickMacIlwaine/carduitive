import { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { HelpCircle } from 'lucide-react'

interface GameBoardProps {
  gameState: {
    game_type: string
    status: 'playing' | 'success' | 'failed'
    level: number
    played_cards: number[]
    next_expected: number
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
    progression?: {
      available_actions: string[]
      message: string
    }
  }
  currentPlayerId: string
  players: Array<{
    id: string
    name: string
  }>
  onPlayCard: (card: number) => void
  onAdvance: () => void
  onRestart: () => void
}

export function GameBoard({ 
  gameState, 
  currentPlayerId, 
  players,
  onPlayCard,
  onAdvance,
  onRestart
}: GameBoardProps) {
  const [hoveredCard, setHoveredCard] = useState<number | null>(null)

  const { 
    level, 
    played_cards, 
    next_expected, 
    player_hands, 
    my_hand,
    status,
    progression
  } = gameState

  // Get my cards
  const myCards = my_hand?.cards || []
  
  // Get other players (exclude current player)
  const otherPlayers = players.filter(p => p.id !== currentPlayerId)

  // Get last played card
  const lastPlayedCard = played_cards.length > 0 
    ? played_cards[played_cards.length - 1] 
    : null

  const handlePlayCard = (card: number) => {
    if (status === 'playing') {
      onPlayCard(card)
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8">
      {/* Header - Level and Status */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary">
          <span className="font-bold text-lg">Level {level}</span>
        </div>
        <p className="text-muted-foreground">
          {status === 'playing' && `Play cards in order: ${next_expected}, ${next_expected + 1}, ${next_expected + 2}...`}
          {status === 'success' && progression?.message}
          {status === 'failed' && progression?.message}
        </p>
      </div>

      {/* Main Game Area */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left: Other Players */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Other Players
          </h3>
          <div className="space-y-3">
            {otherPlayers.map(player => {
              const handInfo = player_hands[player.id] || { card_count: 0 }
              return (
                <Card key={player.id} className="bg-muted/50">
                  <CardContent className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-10 rounded bg-primary/20 flex items-center justify-center border border-primary/30">
                        <HelpCircle className="w-4 h-4 text-primary/60" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">{player.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {handInfo.card_count} card{handInfo.card_count !== 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>

        {/* Center: Last Played Card */}
        <div className="flex flex-col items-center justify-center space-y-6">
          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-4">Last Played</p>
            {lastPlayedCard ? (
              <motion.div
                key={lastPlayedCard}
                initial={{ scale: 0.8, rotate: -10 }}
                animate={{ scale: 1, rotate: 0 }}
                className="w-32 h-44 rounded-xl bg-white border-2 border-slate-200 shadow-xl flex items-center justify-center relative overflow-hidden"
              >
                {/* Card pattern */}
                <div className="absolute inset-0 opacity-5 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-slate-400 to-transparent" />
                
                {/* Card value */}
                <span className="text-5xl font-bold text-slate-800">
                  {lastPlayedCard}
                </span>
                
                {/* Corner decorations */}
                <span className="absolute top-2 left-2 text-sm font-bold text-slate-400">
                  {lastPlayedCard}
                </span>
                <span className="absolute bottom-2 right-2 text-sm font-bold text-slate-400 rotate-180">
                  {lastPlayedCard}
                </span>
              </motion.div>
            ) : (
              <div className="w-32 h-44 rounded-xl border-2 border-dashed border-slate-300 flex items-center justify-center">
                <span className="text-slate-400 text-sm">No cards yet</span>
              </div>
            )}
          </div>

          {/* Progression Controls */}
          {status === 'success' && (
            <Button 
              size="lg" 
              onClick={onAdvance}
              className="w-full"
            >
              Advance to Level {level + 1}
            </Button>
          )}
          {status === 'failed' && (
            <Button 
              size="lg" 
              variant="destructive"
              onClick={onRestart}
              className="w-full"
            >
              Try Level {level} Again
            </Button>
          )}
        </div>

        {/* Right: Played Sequence */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Sequence
          </h3>
          <div className="flex flex-wrap gap-2">
            {played_cards.length === 0 ? (
              <p className="text-sm text-muted-foreground">Waiting for first card...</p>
            ) : (
              played_cards.map((card, index) => (
                <motion.div
                  key={`${card}-${index}`}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: index * 0.05 }}
                  className="w-10 h-14 rounded bg-primary/10 border border-primary/20 flex items-center justify-center text-sm font-bold"
                >
                  {card}
                </motion.div>
              ))
            )}
          </div>
          {played_cards.length > 0 && (
            <p className="text-xs text-muted-foreground">
              {played_cards.length} card{played_cards.length !== 1 ? 's' : ''} played
            </p>
          )}
        </div>
      </div>

      {/* Bottom: Your Hand (Fanned Out) */}
      <div className="space-y-4">
        <h3 className="text-center text-lg font-semibold">
          Your Hand
        </h3>
        
        {status === 'playing' ? (
          <div className="flex justify-center items-end gap-[-20px] md:gap-[-30px]" style={{ perspective: '1000px' }}>
            {myCards.map((card, index) => {
              const isHovered = hoveredCard === card
              const totalCards = myCards.length
              const rotation = (index - (totalCards - 1) / 2) * 5
              
              return (
                <motion.button
                  key={card}
                  onClick={() => handlePlayCard(card)}
                  onMouseEnter={() => setHoveredCard(card)}
                  onMouseLeave={() => setHoveredCard(null)}
                  whileHover={{ 
                    y: -20, 
                    scale: 1.1,
                    zIndex: 10,
                    transition: { duration: 0.2 }
                  }}
                  whileTap={{ scale: 0.95 }}
                  initial={{ y: 0, rotate: rotation }}
                  animate={{ 
                    y: isHovered ? -20 : 0,
                    rotate: rotation,
                    zIndex: isHovered ? 10 : index
                  }}
                  className={`
                    relative w-20 h-28 md:w-24 md:h-36
                    rounded-lg bg-white border-2 border-slate-300 shadow-lg
                    flex items-center justify-center
                    cursor-pointer
                    hover:border-primary hover:shadow-xl
                    transition-shadow
                  `}
                  style={{
                    marginLeft: index > 0 ? '-30px' : '0',
                    zIndex: index
                  }}
                >
                  {/* Card value */}
                  <span className="text-3xl md:text-4xl font-bold text-slate-800">
                    {card}
                  </span>
                  
                  {/* Corner decorations */}
                  <span className="absolute top-1 left-2 text-xs font-bold text-slate-400">
                    {card}
                  </span>
                  <span className="absolute bottom-1 right-2 text-xs font-bold text-slate-400 rotate-180">
                    {card}
                  </span>
                  
                  {/* Hover overlay */}
                  {isHovered && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="absolute inset-0 bg-primary/10 rounded-lg flex items-center justify-center"
                    >
                      <span className="text-primary font-semibold text-sm bg-white/90 px-2 py-1 rounded">
                        Play
                      </span>
                    </motion.div>
                  )}
                </motion.button>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-muted-foreground">
              {status === 'success' ? 'Level Complete!' : 'Level Failed'}
            </p>
          </div>
        )}
        
        <p className="text-center text-sm text-muted-foreground">
          {myCards.length} card{myCards.length !== 1 ? 's' : ''} in hand
        </p>
      </div>

      {/* Debug Info (remove in production) */}
      <div className="text-center text-xs text-muted-foreground pt-4 border-t">
        <p>Next expected: {next_expected} | Level: {level} | Status: {status}</p>
      </div>
    </div>
  )
}
